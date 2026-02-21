import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import type { ATMDetail } from "@/types/atm";

interface ATMDetailPanelProps {
  detail: ATMDetail | null | undefined;
  isLoading?: boolean;
}

function Field({ label, value }: { label: string; value: string | null | undefined }) {
  if (!value) return null;
  return (
    <div className="space-y-1">
      <dt className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
        {label}
      </dt>
      <dd className="text-sm whitespace-pre-line">{value}</dd>
    </div>
  );
}

function BoolField({ label, value }: { label: string; value: boolean | null | undefined }) {
  if (value === null || value === undefined) return null;
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
        {label}
      </span>
      <Badge variant={value ? "default" : "secondary"}>
        {value ? "Yes" : "No"}
      </Badge>
    </div>
  );
}

function DetailSkeleton() {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-2 flex-1">
            <Skeleton className="h-6 w-32" />
            <Skeleton className="h-4 w-48" />
          </div>
          <Skeleton className="h-6 w-28" />
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="space-y-1">
              <Skeleton className="h-3 w-20" />
              <Skeleton className="h-4 w-full" />
            </div>
          ))}
        </div>
        <div className="flex gap-4">
          <Skeleton className="h-6 w-36" />
          <Skeleton className="h-6 w-36" />
          <Skeleton className="h-6 w-24" />
        </div>
        <Separator />
        <div className="space-y-1">
          <Skeleton className="h-3 w-24" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
        </div>
        <div className="space-y-1">
          <Skeleton className="h-3 w-32" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
          <Skeleton className="h-4 w-2/3" />
        </div>
      </CardContent>
    </Card>
  );
}

export function ATMDetailPanel({ detail, isLoading }: ATMDetailPanelProps) {
  if (isLoading) {
    return <DetailSkeleton />;
  }

  if (!detail) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          Select a tender and scrape it to view details.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div>
            <CardTitle>{detail.atm_id}</CardTitle>
            <CardDescription>{detail.agency}</CardDescription>
          </div>
          {detail.atm_type && <Badge variant="outline">{detail.atm_type}</Badge>}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <Field label="Category" value={detail.category} />
          <Field label="Location" value={detail.location} />
          <Field label="Publish Date" value={detail.publish_date} />
          <Field label="Close Date" value={detail.close_date} />
        </div>

        <div className="flex flex-wrap gap-4">
          <BoolField label="Multi Agency Access" value={detail.multi_agency_access} />
          <BoolField label="Panel Arrangement" value={detail.panel_arrangement} />
          <BoolField label="Multi-stage" value={detail.multi_stage} />
        </div>

        <Separator />

        <Field label="Description" value={detail.description} />
        <Field label="Other Instructions" value={detail.other_instructions} />
        <Field label="Conditions for Participation" value={detail.conditions_for_participation} />
        <Field label="Timeframe for Delivery" value={detail.timeframe_for_delivery} />
        <Field label="Address for Lodgement" value={detail.address_for_lodgement} />

        <Separator />

        {detail.contact_details && (
          <div className="space-y-1">
            <dt className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Contact
            </dt>
            <dd className="text-sm">
              {detail.contact_details.name && <div>{detail.contact_details.name}</div>}
              {detail.contact_details.phone && <div>{detail.contact_details.phone}</div>}
              {detail.contact_details.email && (
                <div>
                  <a
                    href={`mailto:${detail.contact_details.email}`}
                    className="text-primary underline"
                  >
                    {detail.contact_details.email}
                  </a>
                </div>
              )}
            </dd>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
