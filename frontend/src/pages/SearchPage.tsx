import { useEffect, useState } from "react";
import { DatabaseIcon, SearchIcon, SearchXIcon, SlidersHorizontalIcon, XIcon } from "lucide-react";

import { useAttributeIndex, useCharacters } from "@/api/hooks";
import type { CharacterSort, Gender } from "@/api/types";
import { AttributeFilterDialog } from "@/components/AttributeFilterDialog";
import { CHARACTER_GRID, CharacterCard, CharacterGridSkeleton } from "@/components/CharacterCard";
import { Pagination } from "@/components/Pagination";
import { SelectedFilters } from "@/components/SelectedFilters";
import { EmptyState, ErrorState, PageContainer } from "@/components/States";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useSearchState } from "@/hooks/useSearchState";
import { GENDER_LABELS, SORT_LABELS } from "@/lib/labels";
import { cn } from "@/lib/utils";

const PAGE_SIZE = 24;
const GENDER_OPTIONS: (Gender | undefined)[] = [undefined, "female", "male"];

export function SearchPage() {
  const { state, update } = useSearchState();
  const { data: dictionary, index } = useAttributeIndex();
  const [filterOpen, setFilterOpen] = useState(false);

  // The name box updates the URL after a short pause instead of on every keystroke.
  const [text, setText] = useState(state.q);
  useEffect(() => setText(state.q), [state.q]);
  useEffect(() => {
    if (text.trim() === state.q) return;
    const timer = setTimeout(() => update({ q: text }, { replace: true }), 300);
    return () => clearTimeout(timer);
  }, [text, state.q, update]);

  const result = useCharacters({
    q: state.q,
    attrs: state.attrs,
    gender: state.gender,
    sort: state.sort,
    page: state.page,
    pageSize: PAGE_SIZE,
  });
  const data = result.data;
  const hasConditions = Boolean(state.q || state.attrs.length || state.gender);

  return (
    <PageContainer>
      <header className="max-w-3xl">
        <p className="text-xs font-medium tracking-[0.18em] text-muted-foreground uppercase">Character Discovery</p>
        <h1 className="mt-2 font-display text-3xl font-semibold tracking-tight sm:text-[2.5rem] sm:leading-tight">
          按属性找到你的角色
        </h1>
        <p className="mt-3 text-sm leading-relaxed text-muted-foreground sm:text-[15px]">
          外貌、服装、性格与身份
          {dictionary ? ` —— ${dictionary.total_attributes} 个属性` : ""}
          可以自由组合。同一分组内的条件为「或」，不同分组之间为「且」。
        </p>
      </header>

      {/* search controls */}
      <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <SearchIcon className="pointer-events-none absolute top-1/2 left-3.5 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="搜索角色名、日文名、英文名或别名"
            aria-label="搜索角色名"
            className="h-11 rounded-xl pr-10 pl-10 text-[15px]"
          />
          {text && (
            <button
              type="button"
              onClick={() => {
                setText("");
                update({ q: "" });
              }}
              className="absolute top-1/2 right-3 -translate-y-1/2 rounded-md p-1 text-muted-foreground hover:text-foreground"
              aria-label="清除名称"
            >
              <XIcon className="size-4" />
            </button>
          )}
        </div>
        <Button size="lg" variant={state.attrs.length ? "default" : "outline"} onClick={() => setFilterOpen(true)}>
          <SlidersHorizontalIcon />
          属性筛选
          {state.attrs.length > 0 && (
            <span className="rounded-full bg-primary-foreground/20 px-1.5 text-xs tabular-nums">{state.attrs.length}</span>
          )}
        </Button>
      </div>

      {state.attrs.length > 0 && (
        <div className="mt-4">
          <SelectedFilters
            keys={state.attrs}
            index={index}
            onRemove={(key) => update({ attrs: state.attrs.filter((k) => k !== key) })}
            onClear={() => update({ attrs: [] })}
          />
        </div>
      )}

      {/* result bar */}
      <div className="mt-8 mb-5 flex flex-wrap items-center justify-between gap-3 border-b pb-4">
        <p className="text-sm text-muted-foreground">
          {data ? (
            <>
              <span className="text-lg font-semibold text-foreground tabular-nums">{data.total}</span> 名角色
              {hasConditions && " 符合条件"}
            </>
          ) : (
            " "
          )}
        </p>
        <div className="flex items-center gap-2">
          <div role="radiogroup" aria-label="性别" className="flex rounded-lg bg-secondary p-0.5">
            {GENDER_OPTIONS.map((g) => (
              <button
                key={g ?? "all"}
                type="button"
                role="radio"
                aria-checked={state.gender === g}
                onClick={() => update({ gender: g })}
                className={cn(
                  "rounded-md px-2.5 py-1 text-[13px] transition-colors",
                  state.gender === g ? "bg-card font-medium shadow-sm" : "text-muted-foreground hover:text-foreground",
                )}
              >
                {g ? GENDER_LABELS[g] : "全部"}
              </button>
            ))}
          </div>
          <Select value={state.sort} onValueChange={(v) => update({ sort: v as CharacterSort })}>
            <SelectTrigger className="w-32" aria-label="排序方式">
              <SelectValue />
            </SelectTrigger>
            <SelectContent align="end">
              {(Object.keys(SORT_LABELS) as CharacterSort[]).map((s) => (
                <SelectItem key={s} value={s}>
                  {SORT_LABELS[s]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* results */}
      {result.isPending ? (
        <CharacterGridSkeleton />
      ) : result.isError ? (
        <ErrorState error={result.error} onRetry={() => result.refetch()} />
      ) : data!.total === 0 ? (
        <NoResults
          unknown={data!.unknown_attributes}
          hasConditions={hasConditions}
          canDropLast={state.attrs.length > 1}
          onDropLast={() => update({ attrs: state.attrs.slice(0, -1) })}
          onReset={() => {
            setText("");
            update({ q: "", attrs: [], gender: undefined });
          }}
        />
      ) : (
        <div className={cn("transition-opacity", result.isPlaceholderData && "opacity-60")}>
          <div className={CHARACTER_GRID}>
            {data!.items.map((character) => (
              <CharacterCard key={character.id} character={character} />
            ))}
          </div>
          {data!.items.length === 0 && (
            <p className="py-10 text-center text-sm text-muted-foreground">这一页没有角色了。</p>
          )}
          <div className="mt-10">
            <Pagination page={state.page} pages={data!.pages} onChange={(page) => update({ page })} />
          </div>
        </div>
      )}

      <AttributeFilterDialog
        open={filterOpen}
        onOpenChange={setFilterOpen}
        value={state.attrs}
        onApply={(attrs) => update({ attrs })}
        context={{ q: state.q, gender: state.gender }}
      />
    </PageContainer>
  );
}

function NoResults({
  unknown,
  hasConditions,
  canDropLast,
  onDropLast,
  onReset,
}: {
  unknown: string[];
  hasConditions: boolean;
  canDropLast: boolean;
  onDropLast: () => void;
  onReset: () => void;
}) {
  if (!hasConditions) {
    return (
      <EmptyState icon={<DatabaseIcon />} title="数据库中还没有角色">
        请在 backend 目录运行 <code className="rounded bg-secondary px-1.5 py-0.5 text-xs">python -m app.seed</code>{" "}
        导入演示数据。
      </EmptyState>
    );
  }
  return (
    <EmptyState
      icon={<SearchXIcon />}
      title="没有符合条件的角色"
      action={
        <>
          {canDropLast && (
            <Button variant="outline" onClick={onDropLast}>
              移除最后一个属性
            </Button>
          )}
          <Button variant="ghost" onClick={onReset}>
            清除全部条件
          </Button>
        </>
      }
    >
      {unknown.length > 0
        ? `属性字典中不存在：${unknown.join("、")}。`
        : "严格检索只返回已标注全部条件的角色。可以减少条件，或在同一分组内多选几个属性。"}
    </EmptyState>
  );
}
