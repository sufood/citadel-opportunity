# Pre-Mortem: Opportunity Analyser on AWS
### *90 days in, everything has gone to hell*

---

## Internal Architecture Failures

### 1. The Singleton Browser Killed You First (Week 1–2)

This is the big one. The app was designed explicitly as a *"single-user tool"* with a singleton Playwright/Chromium context. On AWS, when two people clicked "Analyse" at the same time, they shared the same browser context — cookies, navigation state, downloads, all of it. Race conditions caused half the scrapes to return wrong data or fail silently. Chromium also has a memory leak under sustained load — within days the container was OOMing and getting killed by AWS, wiping the in-memory job store and all active SSE connections with it.

### 2. The In-Memory Job Store Evaporated on Every Restart

The README literally says *"avoids the complexity of Celery/Redis"* — which is fine for local dev. In AWS, the ECS task or EC2 instance restarts for deployments, health check failures, spot interruptions, or OOM kills. Every restart nuked every in-memory job. Users mid-triage got a dead SSE stream with no way to recover. No persistence, no retry, no queue.

### 3. `tmp/` Disk Storage Exploded

Every ATM analysis writes JSON, PDFs, and DOCX to `tmp/{uuid}/`. There's no eviction, no TTL, no cleanup job. After 90 days of real usage, the EBS volume (or container ephemeral storage) filled up. Writes started failing silently, or with cryptic OS errors. If running on ECS Fargate, `tmp/` was never even persisted between task restarts — meaning all previously downloaded documents just vanished.

### 4. tenders.gov.au Rate-Limited or Blocked You

Playwright is spoofing a Chrome user agent to bypass CloudFront WAF. That works until the government's WAF learns the pattern — consistent headless browser fingerprint, no mouse movement, deterministic timing, all requests from the same AWS IP range. After enough scrapes, the IP gets flagged, sessions get challenged with CAPTCHAs, or 403s start appearing. Since there's no retry logic, backoff, or IP rotation, every search just... fails.

### 5. `auth_state.json` Went Stale

Session cookies are saved to `tmp/.auth_state.json` and restored on restart. Government portals typically invalidate sessions after 30–60 days, or on suspicious activity (like your IP changing on every container restart). After the first credentials rotation or session expiry, document downloads silently fell back to unauthenticated behaviour, returning login pages instead of files — and pdfplumber happily "parsed" those HTML login pages into garbage that Claude then triaged as real tender content.

### 6. The Claude API Costs Went Sideways

The triage sends *all* files in `tmp/{uuid}/` — every PDF, every DOCX, all the JSON — to Claude Sonnet. No chunking strategy, no token budgeting. A large tender with 10 documents could easily hit 100k+ tokens per triage call. At 90 days of real usage, the Anthropic API bill was likely 10–20x what was estimated, with no alerting or cost controls in place.

### 7. SSE Through AWS Load Balancers Just Died

ALB and API Gateway both have idle connection timeouts (default 60 seconds on ALB). SSE connections that went quiet for more than 60 seconds — e.g. a slow download or a large Claude API call — were silently dropped by the load balancer. The frontend's `EventSource` got a closed connection with no error event, leaving the UI spinning forever with no indication of what happened.

---

### Root Cause

The README is upfront about it: *"fundamentally a single-user tool."* The architecture is entirely correct for that scope. The mistake was deploying it to AWS as if that constraint had changed, without first addressing concurrency, persistence, disk lifecycle, and network infrastructure assumptions.

---

## External World Events That Also Conspired Against You

### The AWS US-EAST-1 Outage Wiped You Out (October 20, 2025)

If you deployed to US-EAST-1 — the default region everyone picks — you were among the 400+ SaaS providers caught in the blast radius when a DNS race condition deleted DynamoDB's regional endpoint record, taking the region down for 15 hours. Engineering teams found themselves in an impossible position: monitoring dashboards showed failing services, but the AWS management consoles needed to diagnose and fix things were either unreachable or showing stale data.

For this app specifically, that means: the container is dead, the in-memory job store is gone, all active SSE streams are severed, and any `tmp/` data not on a persistent EBS volume has vanished.

> **Looking ahead:** Forrester's 2026 predictions warn this isn't over — AI data centre upgrades are expected to trigger at least two more major multi-day outages in 2026 as hyperscalers divert investment away from legacy infrastructure toward GPU-centric AI workloads.

### The Claude API Had Its Own Bad Week (March 2, 2026)

The triage feature — the core value proposition — runs entirely on the Anthropic API. On March 2, 2026, Claude experienced a worldwide outage with elevated errors across all platforms. The outage showed a whack-a-mole pattern: just as login paths were stabilised, new issues appeared with Claude Opus 4.6, followed by Claude Haiku 4.5.

The app has no fallback model, no graceful degradation, and no circuit breaker — so every triage request during that window either hung indefinitely or returned a 500 that the user had no way to retry. Best practice guidance recommends implementing exponential backoff on 429 and 5xx errors, reducing concurrency, and narrowing prompts or context length — none of which this app does.

### AusTender's Own Maintenance Windows

The target site itself goes dark on a schedule. The AusTender Helpdesk was unavailable from 24 December 2025 through 2 January 2026, and is also closed for ACT public holidays (e.g. Canberra Day, March 9, 2026). Beyond scheduled downtime, the site runs behind CloudFront WAF — already identified as a scraping risk in the README — and a government portal has every incentive to harden its defences further if it detects automated access patterns originating from a static AWS IP.

### The Broader Reliability Picture

Global network outages rose 33% between January and May 2025, and 50% of data centres experienced at least one impactful outage over the past three years. This app was architected with zero tolerance for any of that — no retry logic, no multi-region failover, no queue persistence, no fallback for either of its two critical external dependencies (tenders.gov.au and the Anthropic API). Every real-world reliability event that happened in the 90 days since go-live hit an architecture that had no answer for any of them.

---

## Summary

| Failure | Type | Severity |
|---|---|---|
| Singleton browser / race conditions | Internal | Critical |
| In-memory job store lost on restart | Internal | Critical |
| `tmp/` disk fills with no eviction | Internal | High |
| tenders.gov.au WAF blocks AWS IP | Internal + External | High |
| `auth_state.json` session expiry | Internal | High |
| Claude API token costs unbudgeted | Internal | Medium |
| SSE dropped by ALB timeout | Internal | Medium |
| AWS US-EAST-1 15hr outage (Oct 2025) | External | Critical |
| Claude API worldwide outage (Mar 2026) | External | High |
| AusTender maintenance windows | External | Low–Medium |

**The brutal summary:** the technical debt from *"it's a single-user tool"* assumptions combined with the single worst AWS outage of 2025 and the Claude API going down in the same 90-day window. The app was exposed to every external failure mode simultaneously, with no resilience layer between it and any of them.
