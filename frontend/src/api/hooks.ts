import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useMemo } from "react";

import { apiGet } from "./client";
import type {
  Attribute,
  AttributeCategory,
  AttributeDictionary,
  AttributeGroup,
  CharacterDetail,
  CharacterPage,
  CharacterSort,
  Gender,
  Page,
  WorkDetail,
  WorkListItem,
} from "./types";

export interface CharacterSearch {
  q?: string;
  attrs?: string[];
  gender?: Gender;
  workId?: number;
  sort?: CharacterSort;
  page?: number;
  pageSize?: number;
}

export function useCharacters(search: CharacterSearch, options: { enabled?: boolean } = {}) {
  const params = {
    q: search.q?.trim(),
    attrs: search.attrs?.length ? search.attrs.join(",") : undefined,
    gender: search.gender,
    work_id: search.workId,
    sort: search.sort,
    page: search.page,
    page_size: search.pageSize,
  };
  return useQuery({
    queryKey: ["characters", params],
    queryFn: ({ signal }) => apiGet<CharacterPage>("/api/characters", params, signal),
    placeholderData: keepPreviousData,
    enabled: options.enabled ?? true,
  });
}

export function useCharacter(id: number) {
  return useQuery({
    queryKey: ["character", id],
    queryFn: ({ signal }) => apiGet<CharacterDetail>(`/api/characters/${id}`, {}, signal),
    enabled: Number.isFinite(id),
  });
}

export function useWorks(params: { q?: string; workType?: string; page?: number; pageSize?: number }) {
  const query = { q: params.q?.trim(), work_type: params.workType, page: params.page, page_size: params.pageSize };
  return useQuery({
    queryKey: ["works", query],
    queryFn: ({ signal }) => apiGet<Page<WorkListItem>>("/api/works", query, signal),
    placeholderData: keepPreviousData,
  });
}

export function useWork(id: number) {
  return useQuery({
    queryKey: ["work", id],
    queryFn: ({ signal }) => apiGet<WorkDetail>(`/api/works/${id}`, {}, signal),
    enabled: Number.isFinite(id),
  });
}

export function useAttributeDictionary() {
  return useQuery({
    queryKey: ["attributes"],
    queryFn: ({ signal }) => apiGet<AttributeDictionary>("/api/attributes", {}, signal),
    staleTime: 5 * 60_000,
  });
}

export interface IndexedAttribute {
  attribute: Attribute;
  group: AttributeGroup;
  category: AttributeCategory;
}

/** The dictionary plus a key → attribute lookup (with its group and category). */
export function useAttributeIndex() {
  const query = useAttributeDictionary();
  const index = useMemo(() => {
    const byKey = new Map<string, IndexedAttribute>();
    for (const category of query.data?.categories ?? []) {
      for (const group of category.groups) {
        for (const attribute of group.attributes) byKey.set(attribute.key, { attribute, group, category });
      }
    }
    return byKey;
  }, [query.data]);
  return { ...query, index };
}
