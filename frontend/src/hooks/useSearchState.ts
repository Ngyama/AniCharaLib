import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router";

import type { CharacterSort, Gender } from "@/api/types";

const SORTS: CharacterSort[] = ["relevance", "name", "newest", "most_tagged"];
const GENDERS: Gender[] = ["female", "male", "other", "unknown"];

export interface SearchState {
  q: string;
  attrs: string[];
  gender?: Gender;
  sort: CharacterSort;
  page: number;
}

/** Character search conditions live in the URL, so results are shareable and survive reloads. */
export function useSearchState() {
  const [params, setParams] = useSearchParams();

  const state = useMemo<SearchState>(() => {
    const sort = params.get("sort") as CharacterSort | null;
    const gender = params.get("gender") as Gender | null;
    return {
      q: params.get("q") ?? "",
      attrs: (params.get("attrs") ?? "").split(",").filter(Boolean),
      gender: gender && GENDERS.includes(gender) ? gender : undefined,
      sort: sort && SORTS.includes(sort) ? sort : "relevance",
      page: Math.max(1, Number(params.get("page")) || 1),
    };
  }, [params]);

  const update = useCallback(
    (patch: Partial<SearchState>, options: { replace?: boolean } = {}) => {
      setParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          const set = (key: string, value: string | undefined) =>
            value ? next.set(key, value) : next.delete(key);
          if ("q" in patch) set("q", patch.q?.trim());
          if ("attrs" in patch) set("attrs", patch.attrs?.join(","));
          if ("gender" in patch) set("gender", patch.gender);
          if ("sort" in patch) set("sort", patch.sort === "relevance" ? undefined : patch.sort);
          // Any change of conditions starts again from the first page.
          set("page", patch.page && patch.page > 1 ? String(patch.page) : undefined);
          return next;
        },
        { replace: options.replace },
      );
    },
    [setParams],
  );

  return { state, update };
}
