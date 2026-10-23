import { useEffect, useMemo, useState } from "react";
import { CheckIcon, SearchIcon, XIcon } from "lucide-react";

import { useAttributeIndex, useCharacters, type CharacterSearch, type IndexedAttribute } from "@/api/hooks";
import type { Attribute, AttributeCategory, Domain } from "@/api/types";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { DOMAIN_LABELS } from "@/lib/labels";
import { cn } from "@/lib/utils";
import { Swatch } from "./AttributeChip";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  value: string[];
  onApply: (keys: string[]) => void;
  /** Other active search conditions, so the live result count matches what Apply will show. */
  context: Omit<CharacterSearch, "attrs" | "page" | "pageSize">;
}

/**
 * Large overlay for browsing the attribute dictionary: categories on the left, the
 * selected category's groups and tags on the right, a cross-category search, and a
 * footer with the draft selection and a live result count.
 */
export function AttributeFilterDialog({ open, onOpenChange, value, onApply, context }: Props) {
  const { data, index, isLoading, error } = useAttributeIndex();
  const [draft, setDraft] = useState<string[]>(value);
  const [activeKey, setActiveKey] = useState<string | null>(null);
  const [term, setTerm] = useState("");

  // Start every opening from the applied selection; closing without applying discards the draft.
  const valueKey = value.join(",");
  useEffect(() => {
    if (open) {
      setDraft(valueKey ? valueKey.split(",") : []);
      setTerm("");
    }
  }, [open, valueKey]);

  const categories = data?.categories ?? [];
  const active = categories.find((c) => c.key === activeKey) ?? categories[0];

  const preview = useCharacters({ ...context, attrs: draft, pageSize: 1 }, { enabled: open });

  const selectedPerCategory = useMemo(() => {
    const counts = new Map<string, number>();
    for (const key of draft) {
      const entry = index.get(key);
      if (entry) counts.set(entry.category.key, (counts.get(entry.category.key) ?? 0) + 1);
    }
    return counts;
  }, [draft, index]);

  const toggle = (key: string) =>
    setDraft((current) => (current.includes(key) ? current.filter((k) => k !== key) : [...current, key]));

  const searchResults = useMemo(() => searchDictionary(index, term), [index, term]);
  const selected = new Set(draft);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        showClose={false}
        className="flex h-dvh max-w-none flex-col gap-0 overflow-hidden rounded-none p-0 sm:h-[min(780px,90dvh)] sm:w-[calc(100%-3rem)] sm:max-w-5xl sm:rounded-2xl"
      >
        {/* header */}
        <div className="flex flex-col gap-3 border-b px-5 pt-5 pb-4 sm:flex-row sm:items-center sm:gap-6 sm:px-6">
          <div className="min-w-0 flex-1">
            <DialogTitle className="text-lg">属性筛选</DialogTitle>
            <DialogDescription className="mt-0.5 text-xs">
              同一分组内的属性为「或」，不同分组之间为「且」。
            </DialogDescription>
          </div>
          <div className="relative sm:w-72">
            <SearchIcon className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={term}
              onChange={(e) => setTerm(e.target.value)}
              placeholder="搜索属性，如 双马尾 / ツインテール"
              className="pl-9"
              aria-label="搜索属性"
            />
          </div>
          <Button
            variant="ghost"
            size="icon-sm"
            className="absolute top-4 right-4 sm:static"
            onClick={() => onOpenChange(false)}
            aria-label="关闭"
          >
            <XIcon />
          </Button>
        </div>

        {/* body */}
        <div className="flex min-h-0 flex-1 flex-col sm:flex-row">
          {isLoading ? (
            <div className="flex-1 space-y-3 p-6">
              <Skeleton className="h-6 w-40" />
              <Skeleton className="h-24 w-full" />
            </div>
          ) : error ? (
            <p className="p-6 text-sm text-destructive">属性字典加载失败：{(error as Error).message}</p>
          ) : (
            <>
              <CategoryNav
                categories={categories}
                activeKey={term ? null : active?.key}
                counts={selectedPerCategory}
                onSelect={(key) => {
                  setTerm("");
                  setActiveKey(key);
                }}
              />
              <div className="min-h-0 flex-1 overflow-y-auto px-5 py-5 scrollbar-thin sm:px-7 sm:py-6">
                {term ? (
                  <SearchResults results={searchResults} selected={selected} onToggle={toggle} term={term} />
                ) : (
                  active && <CategoryPanel category={active} selected={selected} onToggle={toggle} />
                )}
              </div>
            </>
          )}
        </div>

        {/* footer */}
        <div className="flex flex-col gap-3 border-t bg-shell/40 px-5 py-3.5 sm:flex-row sm:items-center sm:px-6">
          <div className="flex min-h-8 min-w-0 flex-1 items-center gap-2">
            <span className="shrink-0 text-xs text-muted-foreground">已选 {draft.length}</span>
            <div className="flex min-w-0 gap-1.5 overflow-x-auto no-scrollbar">
              {draft.map((key) => {
                const entry = index.get(key);
                return (
                  <button
                    key={key}
                    type="button"
                    onClick={() => toggle(key)}
                    className="inline-flex shrink-0 items-center gap-1 rounded-full bg-accent py-1 pr-1.5 pl-2.5 text-xs text-accent-foreground transition-colors hover:bg-accent/70"
                    aria-label={`移除 ${entry?.attribute.name ?? key}`}
                  >
                    <Swatch color={entry?.attribute.swatch ?? null} className="size-2" />
                    {entry?.attribute.name ?? key}
                    <XIcon className="size-3 opacity-60" />
                  </button>
                );
              })}
            </div>
          </div>
          <div className="flex shrink-0 items-center justify-end gap-2">
            <Button variant="ghost" disabled={draft.length === 0} onClick={() => setDraft([])}>
              清空
            </Button>
            <Button
              onClick={() => {
                onApply(draft);
                onOpenChange(false);
              }}
              className="min-w-36"
            >
              {preview.data ? `显示 ${preview.data.total} 名角色` : "应用筛选"}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function CategoryNav({
  categories,
  activeKey,
  counts,
  onSelect,
}: {
  categories: AttributeCategory[];
  activeKey: string | null | undefined;
  counts: Map<string, number>;
  onSelect: (key: string) => void;
}) {
  const domains = [...new Set(categories.map((c) => c.domain))];
  return (
    <nav
      aria-label="属性分类"
      className="flex shrink-0 gap-1 overflow-x-auto border-b px-4 py-2.5 no-scrollbar sm:w-56 sm:flex-col sm:overflow-y-auto sm:border-r sm:border-b-0 sm:px-3 sm:py-4 sm:scrollbar-thin"
    >
      {domains.map((domain) => (
        <div key={domain} className="flex shrink-0 gap-1 sm:mb-3 sm:flex-col">
          <p className="hidden px-3 pb-1 text-[11px] font-medium tracking-wider text-muted-foreground/80 sm:block">
            {DOMAIN_LABELS[domain as Domain] ?? domain}
          </p>
          {categories
            .filter((c) => c.domain === domain)
            .map((category) => {
              const count = counts.get(category.key) ?? 0;
              const isActive = category.key === activeKey;
              return (
                <button
                  key={category.key}
                  type="button"
                  onClick={() => onSelect(category.key)}
                  aria-current={isActive ? "true" : undefined}
                  className={cn(
                    "flex shrink-0 items-center justify-between gap-3 rounded-lg px-3 py-1.5 text-left text-sm whitespace-nowrap transition-colors",
                    isActive ? "bg-secondary font-medium text-foreground" : "text-muted-foreground hover:text-foreground",
                  )}
                >
                  {category.name}
                  {count > 0 && (
                    <span className="rounded-full bg-primary px-1.5 text-[11px] leading-[18px] font-medium text-primary-foreground tabular-nums">
                      {count}
                    </span>
                  )}
                </button>
              );
            })}
        </div>
      ))}
    </nav>
  );
}

function CategoryPanel({
  category,
  selected,
  onToggle,
}: {
  category: AttributeCategory;
  selected: Set<string>;
  onToggle: (key: string) => void;
}) {
  return (
    <div className="space-y-7">
      <div className="flex items-baseline gap-3">
        <h3 className="font-display text-xl font-semibold">{category.name}</h3>
        {category.name_ja && <span className="text-xs text-muted-foreground">{category.name_ja}</span>}
      </div>
      {category.groups.map((group) => (
        <section key={group.key} aria-labelledby={`group-${group.key}`}>
          <h4 id={`group-${group.key}`} className="mb-2.5 flex items-baseline gap-2 text-sm font-medium">
            {group.name}
            <span className="text-[11px] font-normal text-muted-foreground">{group.attributes.length}</span>
          </h4>
          <div className="flex flex-wrap gap-1.5">
            {group.attributes.map((attribute) => (
              <AttributeToggle
                key={attribute.key}
                attribute={attribute}
                selected={selected.has(attribute.key)}
                onToggle={onToggle}
              />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

function AttributeToggle({
  attribute,
  selected,
  onToggle,
}: {
  attribute: Attribute;
  selected: boolean;
  onToggle: (key: string) => void;
}) {
  const altNames = [attribute.name_ja, attribute.name_en].filter(Boolean).join(" / ");
  return (
    <button
      type="button"
      aria-pressed={selected}
      aria-label={`${attribute.name}（${attribute.character_count}）`}
      onClick={() => onToggle(attribute.key)}
      title={altNames || undefined}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-[13px] transition-colors outline-none focus-visible:ring-[3px] focus-visible:ring-ring/40",
        selected
          ? "border-primary/50 bg-accent text-accent-foreground"
          : "bg-card hover:border-foreground/20 hover:bg-secondary/60",
      )}
    >
      {selected ? <CheckIcon className="size-3.5" /> : <Swatch color={attribute.swatch} />}
      {attribute.name}
      <span
        className={cn(
          "text-[11px] tabular-nums",
          selected ? "text-accent-foreground/70" : "text-muted-foreground/70",
          attribute.character_count === 0 && "opacity-50",
        )}
      >
        {attribute.character_count}
      </span>
    </button>
  );
}

function searchDictionary(index: Map<string, IndexedAttribute>, term: string) {
  const needle = term.trim().toLowerCase();
  if (!needle) return [];
  const groups = new Map<string, { label: string; entries: IndexedAttribute[] }>();
  for (const entry of index.values()) {
    const { attribute, group, category } = entry;
    const haystack = [attribute.name, attribute.name_ja, attribute.name_en, attribute.key]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    if (!haystack.includes(needle)) continue;
    const bucket = groups.get(group.key) ?? { label: `${category.name} › ${group.name}`, entries: [] };
    bucket.entries.push(entry);
    groups.set(group.key, bucket);
  }
  return [...groups.values()];
}

function SearchResults({
  results,
  selected,
  onToggle,
  term,
}: {
  results: ReturnType<typeof searchDictionary>;
  selected: Set<string>;
  onToggle: (key: string) => void;
  term: string;
}) {
  if (results.length === 0) {
    return <p className="py-10 text-center text-sm text-muted-foreground">没有名称包含「{term}」的属性。</p>;
  }
  return (
    <div className="space-y-6">
      {results.map((bucket) => (
        <section key={bucket.label}>
          <h4 className="mb-2.5 text-xs font-medium text-muted-foreground">{bucket.label}</h4>
          <div className="flex flex-wrap gap-1.5">
            {bucket.entries.map(({ attribute }) => (
              <AttributeToggle
                key={attribute.key}
                attribute={attribute}
                selected={selected.has(attribute.key)}
                onToggle={onToggle}
              />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
