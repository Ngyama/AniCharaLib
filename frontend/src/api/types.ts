// Mirrors backend/app/schemas.py. Keep the two in sync.

export type Gender = "female" | "male" | "other" | "unknown";
export type Domain = "appearance" | "personality" | "other";
export type CharacterSort = "relevance" | "name" | "newest" | "most_tagged";

export interface Attribute {
  id: number;
  key: string;
  name: string;
  name_ja: string | null;
  name_en: string | null;
  swatch: string | null;
  parent_key: string | null;
  character_count: number;
}

export interface AttributeGroup {
  id: number;
  key: string;
  name: string;
  name_ja: string | null;
  name_en: string | null;
  featured: boolean;
  attributes: Attribute[];
}

export interface AttributeCategory {
  id: number;
  key: string;
  domain: Domain;
  name: string;
  name_ja: string | null;
  name_en: string | null;
  groups: AttributeGroup[];
}

export interface AttributeDictionary {
  categories: AttributeCategory[];
  total_attributes: number;
}

export interface AttributeTag {
  key: string;
  name: string;
  swatch: string | null;
  matched: boolean;
}

export interface WorkRef {
  id: number;
  key: string;
  title: string;
  work_type: string;
  role: string;
}

export interface CharacterListItem {
  id: number;
  key: string;
  name: string;
  alt_name: string | null;
  gender: Gender;
  image_url: string | null;
  palette: string[];
  works: WorkRef[];
  tags: AttributeTag[];
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface CharacterPage extends Page<CharacterListItem> {
  unknown_attributes: string[];
}

export interface CharacterName {
  name: string;
  language: string;
  name_type: string;
}

export interface AttributeSection {
  key: string;
  domain: Domain;
  name: string;
  groups: { key: string; name: string; attributes: AttributeTag[] }[];
}

export interface CharacterDetail {
  id: number;
  key: string;
  name: string;
  alt_name: string | null;
  names: CharacterName[];
  gender: Gender;
  birth_month: number | null;
  birth_day: number | null;
  age: string | null;
  height_cm: number | null;
  blood_type: string | null;
  summary: string | null;
  image_url: string | null;
  palette: string[];
  works: WorkRef[];
  attribute_sections: AttributeSection[];
}

export interface WorkListItem {
  id: number;
  key: string;
  title: string;
  title_original: string | null;
  title_en: string | null;
  work_type: string;
  release_year: number | null;
  summary: string | null;
  image_url: string | null;
  character_count: number;
}

export interface WorkCharacter extends CharacterListItem {
  role: string;
}

export interface WorkDetail extends WorkListItem {
  characters: WorkCharacter[];
}
