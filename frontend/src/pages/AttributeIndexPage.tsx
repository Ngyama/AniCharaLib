import { Link } from "react-router";

import { useAttributeDictionary } from "@/api/hooks";
import type { Domain } from "@/api/types";
import { Swatch } from "@/components/AttributeChip";
import { ErrorState, PageContainer } from "@/components/States";
import { Skeleton } from "@/components/ui/skeleton";
import { DOMAIN_LABELS } from "@/lib/labels";
import { cn } from "@/lib/utils";

/** Read-only overview of the whole attribute dictionary; every tag links to a search. */
export function AttributeIndexPage() {
  const query = useAttributeDictionary();

  return (
    <PageContainer>
      <header>
        <p className="text-xs font-medium tracking-[0.18em] text-muted-foreground uppercase">Attribute Index</p>
        <h1 className="mt-2 font-display text-3xl font-semibold tracking-tight">属性索引</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          全部 {query.data?.total_attributes ?? "…"} 个属性。数字为已标注该属性的角色数，点击即可检索。
        </p>
      </header>

      {query.isPending ? (
        <div className="mt-8 space-y-4">
          {Array.from({ length: 3 }, (_, i) => (
            <Skeleton key={i} className="h-48 rounded-3xl" />
          ))}
        </div>
      ) : query.isError ? (
        <div className="mt-8">
          <ErrorState error={query.error} onRetry={() => query.refetch()} />
        </div>
      ) : (
        <>
          <nav className="sticky top-0 z-10 -mx-4 mt-6 flex gap-1 overflow-x-auto bg-panel/90 px-4 py-3 backdrop-blur no-scrollbar sm:-mx-8 sm:px-8 lg:-mx-10 lg:px-10">
            {query.data.categories.map((c) => (
              <a
                key={c.key}
                href={`#cat-${c.key}`}
                className="shrink-0 rounded-full bg-secondary px-3 py-1 text-[13px] text-muted-foreground transition-colors hover:text-foreground"
              >
                {c.name}
              </a>
            ))}
          </nav>
          <div className="mt-4 space-y-5">
            {query.data.categories.map((category) => (
              <section key={category.key} id={`cat-${category.key}`} className="scroll-mt-16 rounded-3xl border bg-card p-5 sm:p-7">
                <div className="flex items-baseline gap-3">
                  <h2 className="font-display text-xl font-semibold">{category.name}</h2>
                  <span className="text-xs text-muted-foreground">
                    {DOMAIN_LABELS[category.domain as Domain]} · {category.name_ja}
                  </span>
                </div>
                <div className="mt-5 grid gap-x-10 gap-y-6 lg:grid-cols-2">
                  {category.groups.map((group) => (
                    <div key={group.key}>
                      <h3 className="mb-2 text-sm font-medium">{group.name}</h3>
                      <div className="flex flex-wrap gap-1.5">
                        {group.attributes.map((a) => (
                          <Link
                            key={a.key}
                            to={`/?attrs=${encodeURIComponent(a.key)}`}
                            className={cn(
                              "inline-flex items-center gap-1.5 rounded-lg border bg-panel px-2.5 py-1 text-[13px] transition-colors hover:border-primary/40 hover:bg-accent hover:text-accent-foreground",
                              a.character_count === 0 && "text-muted-foreground",
                            )}
                          >
                            <Swatch color={a.swatch} />
                            {a.name}
                            <span className="text-[11px] text-muted-foreground/80 tabular-nums">{a.character_count}</span>
                          </Link>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            ))}
          </div>
        </>
      )}
    </PageContainer>
  );
}
