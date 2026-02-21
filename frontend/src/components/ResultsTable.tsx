import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import type { SearchResult } from "@/types/atm";

interface ResultsTableProps {
  results: SearchResult[];
  selectedId: string | null;
  onSelect: (uuid: string) => void;
  isLoading?: boolean;
  hasSearched?: boolean;
}

function SkeletonRows() {
  return (
    <>
      {Array.from({ length: 5 }).map((_, i) => (
        <TableRow key={i}>
          <TableCell>
            <Skeleton className="h-4 w-20" />
          </TableCell>
          <TableCell>
            <Skeleton className="h-4 w-full" />
          </TableCell>
        </TableRow>
      ))}
    </>
  );
}

export function ResultsTable({
  results,
  selectedId,
  onSelect,
  isLoading,
  hasSearched,
}: ResultsTableProps) {
  if (!hasSearched && results.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        Search for opportunities to get started.
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[100px]">UUID</TableHead>
          <TableHead>Title</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {isLoading ? (
          <SkeletonRows />
        ) : results.length === 0 ? (
          <TableRow>
            <TableCell colSpan={2} className="text-center py-8 text-muted-foreground">
              No results found. Try a different keyword.
            </TableCell>
          </TableRow>
        ) : (
          results.map((r) => (
            <TableRow
              key={r.uuid}
              className={`cursor-pointer transition-colors ${
                selectedId === r.uuid ? "bg-accent" : "hover:bg-muted/50"
              }`}
              onClick={() => onSelect(r.uuid)}
            >
              <TableCell className="font-mono text-xs">
                {r.uuid.slice(0, 8)}...
              </TableCell>
              <TableCell>{r.title}</TableCell>
            </TableRow>
          ))
        )}
      </TableBody>
    </Table>
  );
}
