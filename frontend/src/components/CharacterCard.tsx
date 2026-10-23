import { Link } from "react-router";

import type { CharacterListItem } from "@/api/types";
import { Skeleton } from "@/components/ui/skeleton";
import { label, ROLE_LABELS } from "@/lib/labels";
import { CardTag } from "./AttributeChip";
import { Portrait } from "./Portrait";

const CARD_TAGS = 3;

export function CharacterCard({ character, role }: { character: CharacterListItem; role?: string }) {
  const [firstWork, ...otherWorks] = character.works;
  return (
    <Link
      to={`/characters/${character.id}`}
      className="group block rounded-2xl outline-none focus-visible:ring-[3px] focus-visible:ring-ring/40"
    >
      <div className="relative transition-transform duration-300 ease-out group-hover:-translate-y-0.5">
        <Portrait
          name={character.name}
          imageUrl={character.image_url}
          palette={character.palette}
          seed={character.id}
          className="shadow-[0_1px_2px_oklch(0.2_0.01_300/0.05)] transition-shadow duration-300 group-hover:shadow-[0_12px_28px_-14px_oklch(0.2_0.02_300/0.35)]"
        />
        {role && (
          <span className="absolute top-2 left-2 rounded-full bg-card/85 px-2 py-0.5 text-[11px] font-medium backdrop-blur">
            {label(ROLE_LABELS, role)}
          </span>
        )}
      </div>
      <div className="mt-3 px-0.5">
        <h3 className="truncate text-[15px] font-semibold tracking-tight">{character.name}</h3>
        <p className="mt-0.5 truncate text-xs text-muted-foreground">
          {character.alt_name ?? " "}
        </p>
        {firstWork && (
          <p className="mt-1.5 truncate text-xs text-muted-foreground/90">
            {firstWork.title}
            {otherWorks.length > 0 && <span className="text-muted-foreground/70"> 等 {character.works.length} 部</span>}
          </p>
        )}
        {character.tags.length > 0 && (
          <div className="mt-2 flex h-5 flex-wrap gap-1 overflow-hidden">
            {character.tags.slice(0, CARD_TAGS).map((tag) => (
              <CardTag key={tag.key} tag={tag} />
            ))}
          </div>
        )}
      </div>
    </Link>
  );
}

export const CHARACTER_GRID =
  "grid grid-cols-2 gap-x-4 gap-y-7 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6";

export function CharacterGridSkeleton({ count = 10 }: { count?: number }) {
  return (
    <div className={CHARACTER_GRID}>
      {Array.from({ length: count }, (_, i) => (
        <div key={i}>
          <Skeleton className="aspect-[3/4] rounded-xl" />
          <Skeleton className="mt-3 h-4 w-2/3" />
          <Skeleton className="mt-1.5 h-3 w-1/2" />
        </div>
      ))}
    </div>
  );
}
