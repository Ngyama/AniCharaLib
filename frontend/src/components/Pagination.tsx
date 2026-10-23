import { ChevronLeftIcon, ChevronRightIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

function pageWindow(page: number, pages: number): (number | "gap")[] {
  const wanted = new Set([1, pages, page - 1, page, page + 1].filter((p) => p >= 1 && p <= pages));
  const sorted = [...wanted].sort((a, b) => a - b);
  const out: (number | "gap")[] = [];
  sorted.forEach((p, i) => {
    if (i > 0 && p - sorted[i - 1] > 1) out.push("gap");
    out.push(p);
  });
  return out;
}

export function Pagination({
  page,
  pages,
  onChange,
}: {
  page: number;
  pages: number;
  onChange: (page: number) => void;
}) {
  if (pages <= 1) return null;
  return (
    <nav aria-label="分页" className="flex items-center justify-center gap-1">
      <Button variant="ghost" size="icon-sm" disabled={page <= 1} onClick={() => onChange(page - 1)} aria-label="上一页">
        <ChevronLeftIcon />
      </Button>
      {pageWindow(page, pages).map((p, i) =>
        p === "gap" ? (
          <span key={`gap-${i}`} className="px-1 text-sm text-muted-foreground">
            …
          </span>
        ) : (
          <Button
            key={p}
            variant="ghost"
            size="icon-sm"
            aria-current={p === page ? "page" : undefined}
            className={cn("tabular-nums", p === page && "bg-secondary font-semibold")}
            onClick={() => onChange(p)}
          >
            {p}
          </Button>
        ),
      )}
      <Button variant="ghost" size="icon-sm" disabled={page >= pages} onClick={() => onChange(page + 1)} aria-label="下一页">
        <ChevronRightIcon />
      </Button>
    </nav>
  );
}
