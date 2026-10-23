import { Link, useNavigate, useParams } from "react-router";
import { ArrowLeftIcon, BookXIcon, UsersIcon } from "lucide-react";

import { useWork } from "@/api/hooks";
import { ApiError } from "@/api/client";
import { CHARACTER_GRID, CharacterCard, CharacterGridSkeleton } from "@/components/CharacterCard";
import { EmptyState, ErrorState, PageContainer } from "@/components/States";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { WORK_TYPE_LABELS, label } from "@/lib/labels";

export function WorkPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const query = useWork(Number(id));

  return (
    <PageContainer>
      <Button variant="ghost" size="sm" className="-ml-3 mb-4 text-muted-foreground" onClick={() => navigate(-1)}>
        <ArrowLeftIcon /> 返回
      </Button>

      {query.isPending ? (
        <>
          <Skeleton className="h-40 rounded-3xl" />
          <div className="mt-8">
            <CharacterGridSkeleton count={5} />
          </div>
        </>
      ) : query.isError ? (
        query.error instanceof ApiError && query.error.status === 404 ? (
          <EmptyState icon={<BookXIcon />} title="找不到这部作品" action={<Button asChild variant="outline"><Link to="/works">查看全部作品</Link></Button>} />
        ) : (
          <ErrorState error={query.error} onRetry={() => query.refetch()} />
        )
      ) : (
        <>
          <section className="rounded-3xl border bg-card p-6 sm:p-8">
            <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
              <span className="rounded-full bg-secondary px-2.5 py-0.5 font-medium text-secondary-foreground">
                {label(WORK_TYPE_LABELS, query.data.work_type)}
              </span>
              {query.data.release_year && <span className="tabular-nums">{query.data.release_year} 年</span>}
            </div>
            <h1 className="mt-4 font-display text-3xl font-bold tracking-tight sm:text-4xl">{query.data.title}</h1>
            {(query.data.title_original || query.data.title_en) && (
              <p className="mt-2 text-sm text-muted-foreground">
                {[query.data.title_original, query.data.title_en].filter((t) => t && t !== query.data.title).join(" · ")}
              </p>
            )}
            {query.data.summary && (
              <p className="mt-5 max-w-3xl text-[15px] leading-relaxed text-foreground/85">{query.data.summary}</p>
            )}
          </section>

          <div className="mt-10 mb-5 flex items-baseline gap-3 border-b pb-4">
            <h2 className="font-display text-xl font-semibold">登场角色</h2>
            <span className="text-sm text-muted-foreground tabular-nums">{query.data.character_count} 名</span>
          </div>
          {query.data.characters.length === 0 ? (
            <EmptyState icon={<UsersIcon />} title="还没有关联角色" />
          ) : (
            <div className={CHARACTER_GRID}>
              {query.data.characters.map((character) => (
                <CharacterCard key={character.id} character={character} role={character.role} />
              ))}
            </div>
          )}
        </>
      )}
    </PageContainer>
  );
}
