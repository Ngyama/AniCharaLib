import { Link } from "react-router";

import type { AttributeTag } from "@/api/types";
import { cn } from "@/lib/utils";

export function Swatch({ color, className }: { color: string | null; className?: string }) {
  if (!color) return null;
  return (
    <span
      aria-hidden
      className={cn("inline-block size-2.5 shrink-0 rounded-full ring-1 ring-black/10 ring-inset", className)}
      style={{ background: color }}
    />
  );
}

/** Small, quiet tag used on character cards. */
export function CardTag({ tag }: { tag: AttributeTag }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] leading-4",
        tag.matched ? "bg-accent text-accent-foreground" : "bg-secondary text-muted-foreground",
      )}
    >
      <Swatch color={tag.swatch} className="size-2" />
      {tag.name}
    </span>
  );
}

/** Tag on the detail page — links to a search for that attribute. */
export function AttributeLink({ tag }: { tag: AttributeTag }) {
  return (
    <Link
      to={`/?attrs=${encodeURIComponent(tag.key)}`}
      title={`检索所有「${tag.name}」的角色`}
      className="inline-flex items-center gap-1.5 rounded-full border bg-card px-3 py-1 text-[13px] transition-colors outline-none hover:border-primary/40 hover:bg-accent hover:text-accent-foreground focus-visible:ring-[3px] focus-visible:ring-ring/40"
    >
      <Swatch color={tag.swatch} />
      {tag.name}
    </Link>
  );
}
