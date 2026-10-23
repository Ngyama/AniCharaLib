import type { CSSProperties } from "react";

import { cn } from "@/lib/utils";

interface PortraitProps {
  name: string;
  imageUrl: string | null;
  /** Swatch colours from the API (hair first, then eyes / skin). */
  palette: string[];
  seed: number;
  className?: string;
}

/**
 * Character image, or — while no licensed artwork exists — a generated placeholder:
 * a tinted card in the character's hair colour with the first glyph of their name.
 */
export function Portrait({ name, imageUrl, palette, seed, className }: PortraitProps) {
  if (imageUrl) {
    return (
      <div className={cn("relative aspect-[3/4] overflow-hidden rounded-xl bg-muted", className)}>
        <img src={imageUrl} alt={name} loading="lazy" className="size-full object-cover" />
      </div>
    );
  }

  const hue = (seed * 47) % 360;
  const fallback = `oklch(0.78 0.035 ${hue})`;
  const hair = palette[0] ?? fallback;
  const accent = palette[1] ?? hair;
  const glyph = Array.from(name.replace(/[·・\s]/g, ""))[0] ?? "?";

  return (
    <div
      role="img"
      aria-label={`${name}（占位图）`}
      className={cn("@container relative aspect-[3/4] overflow-hidden rounded-xl select-none", className)}
      style={
        {
          "--hair": hair,
          "--accent-tone": accent,
          background:
            "radial-gradient(120% 80% at 80% 8%, color-mix(in oklch, var(--hair) 18%, transparent), transparent 60%)," +
            "linear-gradient(165deg, color-mix(in oklch, var(--hair) 34%, var(--portrait-base)) 0%, color-mix(in oklch, var(--hair) 12%, var(--portrait-base)) 100%)",
        } as CSSProperties
      }
    >
      {/* fine diagonal hatching */}
      <div
        aria-hidden
        className="absolute inset-0 opacity-[0.35] mix-blend-soft-light"
        style={{
          backgroundImage:
            "repeating-linear-gradient(135deg, color-mix(in oklch, var(--hair) 50%, white) 0 1px, transparent 1px 9px)",
        }}
      />
      {/* halo ring in the secondary (usually eye) colour */}
      <div
        aria-hidden
        className="absolute top-[9%] right-[10%] aspect-square w-[26%] rounded-full border-[1.5px] opacity-60"
        style={{ borderColor: "color-mix(in oklch, var(--accent-tone) 70%, var(--foreground) 10%)" }}
      />
      <span
        aria-hidden
        className="absolute -bottom-[0.12em] -left-[0.04em] font-display text-[78cqw] leading-none font-bold"
        style={{ color: "color-mix(in oklch, var(--hair) 52%, var(--foreground) 28%)", opacity: 0.42 }}
      >
        {glyph}
      </span>
      <div aria-hidden className="absolute right-[8%] bottom-[7%] flex gap-1">
        {palette.slice(0, 3).map((color, i) => (
          <span
            key={i}
            className="size-[5cqw] min-h-1.5 min-w-1.5 rounded-full ring-1 ring-black/10"
            style={{ background: color }}
          />
        ))}
      </div>
    </div>
  );
}
