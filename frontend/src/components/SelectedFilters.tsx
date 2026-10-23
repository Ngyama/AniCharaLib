import { Fragment } from "react";
import { AlertTriangleIcon, XIcon } from "lucide-react";

import type { IndexedAttribute } from "@/api/hooks";
import { Swatch } from "./AttributeChip";

/**
 * Applied attribute conditions, bundled per group so the search logic is visible:
 * attributes inside a bundle are OR-ed, bundles are AND-ed.
 */
export function SelectedFilters({
  keys,
  index,
  onRemove,
  onClear,
}: {
  keys: string[];
  index: Map<string, IndexedAttribute>;
  onRemove: (key: string) => void;
  onClear: () => void;
}) {
  if (keys.length === 0) return null;

  const groups = new Map<string, { label: string; entries: IndexedAttribute[] }>();
  const unknown: string[] = [];
  for (const key of keys) {
    const entry = index.get(key);
    if (!entry) {
      unknown.push(key);
      continue;
    }
    const bucket = groups.get(entry.group.key) ?? { label: entry.group.name, entries: [] };
    bucket.entries.push(entry);
    groups.set(entry.group.key, bucket);
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      {[...groups.entries()].map(([groupKey, bucket], i) => (
        <Fragment key={groupKey}>
          {i > 0 && <span className="text-[11px] text-muted-foreground">且</span>}
          <div className="inline-flex items-center gap-1 rounded-full border bg-card py-1 pr-1 pl-3 text-[13px]">
            <span className="mr-0.5 text-xs text-muted-foreground">{bucket.label}</span>
            {bucket.entries.map(({ attribute }, j) => (
              <Fragment key={attribute.key}>
                {j > 0 && <span className="text-[11px] text-muted-foreground">或</span>}
                <span className="inline-flex items-center gap-1 rounded-full bg-accent py-0.5 pr-1 pl-2 text-accent-foreground">
                  <Swatch color={attribute.swatch} className="size-2" />
                  {attribute.name}
                  <button
                    type="button"
                    onClick={() => onRemove(attribute.key)}
                    className="rounded-full p-0.5 opacity-60 transition-opacity hover:opacity-100"
                    aria-label={`移除 ${attribute.name}`}
                  >
                    <XIcon className="size-3" />
                  </button>
                </span>
              </Fragment>
            ))}
          </div>
        </Fragment>
      ))}
      {unknown.map((key) => (
        <span
          key={key}
          className="inline-flex items-center gap-1 rounded-full border border-destructive/40 py-1 pr-1 pl-2.5 text-[13px] text-destructive"
          title="属性字典中不存在该属性"
        >
          <AlertTriangleIcon className="size-3.5" />
          未知属性 {key}
          <button
            type="button"
            onClick={() => onRemove(key)}
            className="rounded-full p-0.5 opacity-70 hover:opacity-100"
            aria-label={`移除 ${key}`}
          >
            <XIcon className="size-3" />
          </button>
        </span>
      ))}
      <button
        type="button"
        onClick={onClear}
        className="ml-1 text-xs text-muted-foreground underline-offset-4 transition-colors hover:text-foreground hover:underline"
      >
        清除全部
      </button>
    </div>
  );
}
