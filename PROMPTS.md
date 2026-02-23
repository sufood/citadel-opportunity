I need advice on building an application with Claude Code.
It is an interactive web application which can crawl specific site URLs, authenticate and scrape and download content.
Required Features: 1. UX has Search a given website by keyword search: eg: __https://www.tenders.gov.au/atm__, eg: __https://www.tenders.gov.au/atm?filter=published&orderBy=&Number=&Keyword=__ 
2. Ability to find the unique string ID for each entry in the search results, this will be in the Full Details link of each entry, eg:                        <div class="list-desc">
<span>&nbsp;</span>
<div class="list-desc-inner"><a class="detail" href="/Atm/Show/60e02e43-1969-4d7b-83e4-f953caf81d5c" title="Full Details for Norfolk Island Kingston Pier Rock Revetment Remediation Project 2026">Full Details</a></div>
</div> Where 60e02e43-1969-4d7b-83e4-f953caf81d5c is the unique string ID
3. Ability to create a tmp file directory for each unique string ID
4. Ability to click on “Full Details” link on ATM List Entries and capture the unique string ID, eg: __https://www.tenders.gov.au/Atm/Show/60e02e43-1969-4d7b-83e4-f953caf81d5c__ where 60e02e43-1969-4d7b-83e4-f953caf81d5c is the ID
5. Once the Full Details screen loads completely, look for the window.dataLayer object data in the view page source and write it to the respective unique string ID directory as data-layer.json.
6. Once the Full Details screen loads completely, look for the <div class="box boxW listInner"> DOM item in the view page source and write the following to the respective unique string ID directory as atm-details.json
1. ATM ID
2. Agency
3. Category
4. Close Date &amp; Time
5. Publish Date
6. Location
7. ATM Type
8. Multi Agency Access (yes/no)
9. Panel Arrangement (yes/no)
10. Multi-stage (yes/no)
11. Description
12. Other Instructions
13. Conditions for Participation
14. Timeframe for Delivery
15. Address for Lodgement
16. Addenda Available (get the href URL)
17. Contact Details (get the name, Phone, Email Address)
18. ATM Documents (get the href URL)
19. Lodgement Page (get the href URL)
7. Ability to log in to this sub page with fixed given credentials (form fill plus click “Login” button): __https://www.tenders.gov.au/Atm/ViewDocuments/60e02e43-1969-4d7b-83e4-f953caf81d5c__
8. Ability to download documents listed on the resulting page to the tmp file directory for matching unique string ID __https://www.tenders.gov.au/Atm/ViewDocuments/60e02e43-1969-4d7b-83e4-f953caf81d5c__ would be ./tmp/60e02e43-1969-4d7b-83e4-f953caf81d5c/.
What techs, libraries, programming languages would you choose and why?  Compare multiple options and make recommendations.



Let's choose FastAPI+React and Typescript.




Use web search to have a look at https://citadeledge.com/
What services do the provide?
What case studies are listed including the details.



Spilt that into two markdown files:
1. citadel-edge-services-industries
2. citadel-edge-case-studies



How would you use the two files to score and triage a tender based on tender information?



give me the triage process in a markdown file




Read CLAUDE.md and todo.md, then start Phase 1 — scaffold the project structure.




Read CLAUDE.md and todo.md, then start Phase 1 — scaffold the project structure.
