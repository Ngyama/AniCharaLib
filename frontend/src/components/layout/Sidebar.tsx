import { NavLink } from "react-router";
import { BookOpenIcon, MoonIcon, SearchIcon, SunIcon, TagsIcon } from "lucide-react";

import { useAttributeDictionary, useCharacters } from "@/api/hooks";
import { useTheme } from "@/lib/theme";
import { cn } from "@/lib/utils";

const NAV = [
  { to: "/", label: "角色检索", icon: SearchIcon, end: true },
  { to: "/works", label: "作品", icon: BookOpenIcon, end: false },
  { to: "/attributes", label: "属性索引", icon: TagsIcon, end: false },
];

export function Brand() {
  return (
    <NavLink to="/" className="flex items-center gap-2.5 rounded-lg outline-none focus-visible:ring-[3px] focus-visible:ring-ring/40">
      <img src="/favicon.svg" alt="" className="size-8" />
      <span className="leading-tight">
        <span className="block text-[15px] font-semibold tracking-tight">AniCharaLib</span>
        <span className="block text-[11px] text-muted-foreground">ACG 角色图鉴</span>
      </span>
    </NavLink>
  );
}

export function SidebarNav() {
  const { theme, toggle } = useTheme();
  const dictionary = useAttributeDictionary();
  const characters = useCharacters({ pageSize: 1 });

  return (
    <div className="flex h-full flex-col">
      <div className="px-2 pt-2 pb-6">
        <Brand />
      </div>

      <nav className="flex flex-col gap-0.5">
        {NAV.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-xl px-3 py-2 text-sm text-sidebar-foreground transition-colors outline-none hover:text-foreground focus-visible:ring-[3px] focus-visible:ring-ring/40",
                isActive && "bg-sidebar-active font-medium text-foreground shadow-[0_1px_2px_oklch(0.2_0.01_300/0.06)]",
              )
            }
          >
            <Icon className="size-4" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto space-y-3 px-2 pb-1">
        {dictionary.data && characters.data && (
          <dl className="grid grid-cols-2 gap-2 text-xs">
            <div className="rounded-xl bg-sidebar-active/60 px-3 py-2">
              <dt className="text-muted-foreground">角色</dt>
              <dd className="mt-0.5 text-base font-semibold tabular-nums">{characters.data.total}</dd>
            </div>
            <div className="rounded-xl bg-sidebar-active/60 px-3 py-2">
              <dt className="text-muted-foreground">属性</dt>
              <dd className="mt-0.5 text-base font-semibold tabular-nums">{dictionary.data.total_attributes}</dd>
            </div>
          </dl>
        )}
        <button
          type="button"
          onClick={toggle}
          className="flex w-full items-center gap-2 rounded-lg px-1 py-1 text-xs text-muted-foreground transition-colors hover:text-foreground"
        >
          {theme === "dark" ? <SunIcon className="size-3.5" /> : <MoonIcon className="size-3.5" />}
          {theme === "dark" ? "浅色模式" : "深色模式"}
        </button>
        <p className="px-1 text-[11px] leading-relaxed text-muted-foreground/80">V1 演示数据 · 全部为虚构角色</p>
      </div>
    </div>
  );
}
