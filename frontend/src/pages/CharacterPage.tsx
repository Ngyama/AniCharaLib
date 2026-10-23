import type { ReactNode } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { ArrowLeftIcon, ArrowUpRightIcon, UserXIcon } from "lucide-react";

import { useCharacter } from "@/api/hooks";
import { ApiError } from "@/api/client";
import type { AttributeSection, CharacterDetail, Domain } from "@/api/types";
import { AttributeLink } from "@/components/AttributeChip";
import { Portrait } from "@/components/Portrait";
import { EmptyState, ErrorState, PageContainer } from "@/components/States";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { GENDER_LABELS, LANGUAGE_LABELS, ROLE_LABELS, WORK_TYPE_LABELS, label } from "@/lib/labels";

const SECTION_TITLES: Record<Domain, string> = {
  appearance: "外观属性",
  personality: "性格",
  other: "其他属性",
};

export function CharacterPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const query = useCharacter(Number(id));

  return (
    <PageContainer>
      <Button variant="ghost" size="sm" className="-ml-3 mb-4 text-muted-foreground" onClick={() => navigate(-1)}>
        <ArrowLeftIcon /> 返回
      </Button>
      {query.isPending ? (
        <DetailSkeleton />
      ) : query.isError ? (
        query.error instanceof ApiError && query.error.status === 404 ? (
          <EmptyState icon={<UserXIcon />} title="找不到这个角色" action={<Button asChild variant="outline"><Link to="/">回到角色检索</Link></Button>}>
            角色可能已被移除，或链接有误。
          </EmptyState>
        ) : (
          <ErrorState error={query.error} onRetry={() => query.refetch()} />
        )
      ) : (
        <CharacterView character={query.data} />
      )}
    </PageContainer>
  );
}

function CharacterView({ character }: { character: CharacterDetail }) {
  const facts: [string, ReactNode][] = [["性别", GENDER_LABELS[character.gender]]];
  if (character.birth_month && character.birth_day)
    facts.push(["生日", `${character.birth_month} 月 ${character.birth_day} 日`]);
  if (character.age) facts.push(["年龄", character.age]);
  if (character.height_cm) facts.push(["身高", `${character.height_cm} cm`]);
  if (character.blood_type) facts.push(["血型", `${character.blood_type} 型`]);

  const otherNames = character.names.filter((n) => !(n.language === "zh" && n.name === character.name));
  const byDomain = (domain: Domain) => character.attribute_sections.filter((s) => s.domain === domain);

  return (
    <div className="space-y-5">
      {/* hero */}
      <section className="grid gap-6 rounded-3xl border bg-card p-4 sm:grid-cols-[minmax(0,240px)_1fr] sm:p-6 lg:grid-cols-[280px_1fr] lg:gap-10 lg:p-8">
        <Portrait
          name={character.name}
          imageUrl={character.image_url}
          palette={character.palette}
          seed={character.id}
          className="mx-auto w-full max-w-[280px] rounded-2xl"
        />
        <div className="min-w-0">
          <h1 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">{character.name}</h1>
          {character.alt_name && <p className="mt-1.5 text-lg text-muted-foreground">{character.alt_name}</p>}

          {character.works.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {character.works.map((work) => (
                <Link
                  key={work.id}
                  to={`/works/${work.id}`}
                  className="group inline-flex items-center gap-1.5 rounded-full bg-secondary px-3 py-1 text-[13px] transition-colors hover:bg-accent hover:text-accent-foreground"
                >
                  {work.title}
                  <ArrowUpRightIcon className="size-3.5 opacity-50 transition-opacity group-hover:opacity-100" />
                </Link>
              ))}
            </div>
          )}

          <dl className="mt-6 grid grid-cols-2 gap-x-6 gap-y-4 sm:grid-cols-3 xl:grid-cols-5">
            {facts.map(([term, value]) => (
              <div key={term}>
                <dt className="text-xs text-muted-foreground">{term}</dt>
                <dd className="mt-0.5 text-[15px] font-medium">{value}</dd>
              </div>
            ))}
          </dl>

          {character.summary && (
            <p className="mt-6 max-w-2xl text-[15px] leading-relaxed text-foreground/85">{character.summary}</p>
          )}

          {otherNames.length > 0 && (
            <div className="mt-6 border-t pt-5">
              <h2 className="text-xs text-muted-foreground">其他名称</h2>
              <ul className="mt-2 flex flex-wrap gap-x-5 gap-y-1.5 text-sm">
                {otherNames.map((n) => (
                  <li key={`${n.language}-${n.name}`} className="flex items-baseline gap-1.5">
                    <span className="shrink-0 text-[11px] whitespace-nowrap text-muted-foreground">
                      {label(LANGUAGE_LABELS, n.language)}
                      {n.name_type === "alias" && "别名"}
                    </span>
                    {n.name}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </section>

      {(["appearance", "personality", "other"] as Domain[]).map((domain) => {
        const sections = byDomain(domain);
        return sections.length > 0 ? (
          <AttributeCard key={domain} title={SECTION_TITLES[domain]} sections={sections} />
        ) : null;
      })}
      {character.attribute_sections.length === 0 && (
        <p className="rounded-2xl border border-dashed px-6 py-8 text-center text-sm text-muted-foreground">
          这个角色还没有标注任何属性。
        </p>
      )}

      {character.works.length > 0 && (
        <section className="rounded-3xl border bg-card p-5 sm:p-7">
          <h2 className="font-display text-lg font-semibold">所属作品</h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {character.works.map((work) => (
              <Link
                key={work.id}
                to={`/works/${work.id}`}
                className="group flex items-center justify-between gap-3 rounded-2xl border bg-panel px-4 py-3.5 transition-colors hover:border-primary/30 hover:bg-accent/50"
              >
                <div className="min-w-0">
                  <p className="truncate font-medium">{work.title}</p>
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    {label(WORK_TYPE_LABELS, work.work_type)} · {label(ROLE_LABELS, work.role)}
                  </p>
                </div>
                <ArrowUpRightIcon className="size-4 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

function AttributeCard({ title, sections }: { title: string; sections: AttributeSection[] }) {
  // A domain with a single category (性格, 其他属性) would just repeat the card title.
  const showCategoryNames = sections.length > 1;
  return (
    <section className="rounded-3xl border bg-card p-5 sm:p-7">
      <h2 className="font-display text-lg font-semibold">{title}</h2>
      <div className="mt-4 divide-y">
        {sections.map((section) => (
          <div key={section.key} className="grid gap-3 py-4 first:pt-1 last:pb-0 md:grid-cols-[120px_1fr] md:gap-6">
            {showCategoryNames && <h3 className="text-sm font-medium md:pt-1">{section.name}</h3>}
            <div className={showCategoryNames ? "space-y-3" : "space-y-3 md:col-span-2"}>
              {section.groups.map((group) => (
                <div key={group.key} className="flex flex-col gap-2 sm:flex-row sm:items-start sm:gap-4">
                  <span className="w-28 shrink-0 pt-1 text-xs text-muted-foreground">{group.name}</span>
                  <div className="flex flex-wrap gap-1.5">
                    {group.attributes.map((tag) => (
                      <AttributeLink key={tag.key} tag={tag} />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function DetailSkeleton() {
  return (
    <div className="grid gap-8 rounded-3xl border p-6 sm:grid-cols-[240px_1fr]">
      <Skeleton className="aspect-[3/4] rounded-2xl" />
      <div className="space-y-4">
        <Skeleton className="h-9 w-1/2" />
        <Skeleton className="h-5 w-1/3" />
        <Skeleton className="h-20 w-full" />
      </div>
    </div>
  );
}
