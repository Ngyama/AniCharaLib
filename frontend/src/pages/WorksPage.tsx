import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router";
import { BookOpenIcon, SearchIcon } from "lucide-react";

import { useWorks } from "@/api/hooks";
import type { WorkListItem } from "@/api/types";
import { Pagination } from "@/components/Pagination";
import { EmptyState, ErrorState, PageContainer } from "@/components/States";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { WORK_TYPE_LABELS, label } from "@/lib/labels";
import { cn } from "@/lib/utils";

const PAGE_SIZE = 24;
const TYPE_FILTERS = [undefined, "anime", "visual_novel", "manga", "light_novel", "game"];

export function WorksPage() {
  const [params, setParams] = useSearchParams();
  const q = params.get("q") ?? "";
  const workType = params.get("type") ?? undefined;
  const page = Math.max(1, Number(params.get("page")) || 1);

  const setParam = (key: string, value: string | undefined) =>
    setParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        if (value) next.set(key, value);
        else next.delete(key);
        if (key !== "page") next.delete("page");
        return next;
      },
      { replace: key === "q" },
    );

  const [text, setText] = useState(q);
  useEffect(() => setText(q), [q]);
  useEffect(() => {
    if (text.trim() === q) return;
    const timer = setTimeout(() => setParam("q", text.trim() || undefined), 300);
    return () => clearTimeout(timer);
  }, [text, q]);

  const works = useWorks({ q, workType, page, pageSize: PAGE_SIZE });

  return (
    <PageContainer>
      <header>
        <p className="text-xs font-medium tracking-[0.18em] text-muted-foreground uppercase">Works</p>
        <h1 className="mt-2 font-display text-3xl font-semibold tracking-tight">作品</h1>
        <p className="mt-2 text-sm text-muted-foreground">同一角色只收录一次，并关联到其出场的全部作品。</p>
      </header>

      <div className="mt-7 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="flex gap-1 overflow-x-auto no-scrollbar">
          {TYPE_FILTERS.map((type) => (
            <button
              key={type ?? "all"}
              type="button"
              onClick={() => setParam("type", type)}
              className={cn(
                "shrink-0 rounded-full px-3.5 py-1.5 text-[13px] transition-colors",
                workType === type ? "bg-foreground text-background" : "bg-secondary text-muted-foreground hover:text-foreground",
              )}
            >
              {type ? label(WORK_TYPE_LABELS, type) : "全部"}
            </button>
          ))}
        </div>
        <div className="relative md:w-72">
          <SearchIcon className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input value={text} onChange={(e) => setText(e.target.value)} placeholder="搜索作品标题" className="pl-9" aria-label="搜索作品" />
        </div>
      </div>

      <div className="mt-6">
        {works.isPending ? (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {Array.from({ length: 6 }, (_, i) => (
              <Skeleton key={i} className="h-44 rounded-2xl" />
            ))}
          </div>
        ) : works.isError ? (
          <ErrorState error={works.error} onRetry={() => works.refetch()} />
        ) : works.data.total === 0 ? (
          <EmptyState icon={<BookOpenIcon />} title={q || workType ? "没有符合条件的作品" : "还没有收录作品"} />
        ) : (
          <>
            <div className={cn("grid gap-4 sm:grid-cols-2 xl:grid-cols-3", works.isPlaceholderData && "opacity-60")}>
              {works.data.items.map((work) => (
                <WorkCard key={work.id} work={work} />
              ))}
            </div>
            <div className="mt-10">
              <Pagination page={page} pages={works.data.pages} onChange={(p) => setParam("page", String(p))} />
            </div>
          </>
        )}
      </div>
    </PageContainer>
  );
}

function WorkCard({ work }: { work: WorkListItem }) {
  return (
    <Link
      to={`/works/${work.id}`}
      className="group flex flex-col rounded-2xl border bg-card p-5 transition-[border-color,box-shadow] hover:border-primary/30 hover:shadow-[0_12px_28px_-18px_oklch(0.2_0.02_300/0.35)]"
    >
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span className="rounded-full bg-secondary px-2.5 py-0.5 font-medium text-secondary-foreground">
          {label(WORK_TYPE_LABELS, work.work_type)}
        </span>
        {work.release_year && <span className="tabular-nums">{work.release_year}</span>}
      </div>
      <h2 className="mt-4 font-display text-lg leading-snug font-semibold group-hover:text-primary">{work.title}</h2>
      {work.title_original && work.title_original !== work.title && (
        <p className="mt-1 text-xs text-muted-foreground">{work.title_original}</p>
      )}
      {work.summary && <p className="mt-3 line-clamp-2 text-sm leading-relaxed text-muted-foreground">{work.summary}</p>}
      <p className="mt-auto pt-4 text-xs text-muted-foreground">
        <span className="font-semibold text-foreground tabular-nums">{work.character_count}</span> 名角色
      </p>
    </Link>
  );
}
