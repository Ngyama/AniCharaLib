// Labels for the fixed enums of the API. Attribute categories / tags are never listed here:
// they come from the attribute dictionary endpoint.

import type { CharacterSort, Domain, Gender } from "@/api/types";

export const GENDER_LABELS: Record<Gender, string> = {
  female: "女性",
  male: "男性",
  other: "其他",
  unknown: "不明",
};

export const WORK_TYPE_LABELS: Record<string, string> = {
  anime: "动画",
  visual_novel: "视觉小说",
  manga: "漫画",
  light_novel: "轻小说",
  game: "游戏",
  novel: "小说",
  other: "其他",
};

export const ROLE_LABELS: Record<string, string> = {
  main: "主要角色",
  supporting: "配角",
  minor: "次要角色",
  cameo: "客串",
};

export const LANGUAGE_LABELS: Record<string, string> = {
  zh: "中文",
  ja: "日文",
  en: "英文",
  romaji: "罗马字",
  other: "其他",
};

export const DOMAIN_LABELS: Record<Domain, string> = {
  appearance: "外观",
  personality: "性格",
  other: "其他",
};

export const SORT_LABELS: Record<CharacterSort, string> = {
  relevance: "默认排序",
  name: "按名称",
  newest: "最新收录",
  most_tagged: "资料最丰富",
};

export function label(map: Record<string, string>, key: string): string {
  return map[key] ?? key;
}
