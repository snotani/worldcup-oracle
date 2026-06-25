import type { Outcome, Probs } from "./types";

export const pct = (x: number): string => `${Math.round(x * 100)}%`;
export const pct1 = (x: number): string => `${(x * 100).toFixed(1)}%`;

export function outcomeLabel(outcome: string, home: string, away: string): string {
  if (outcome === "home") return home;
  if (outcome === "away") return away;
  return "Draw";
}

export function kickoff(iso: string | null | undefined): string {
  if (!iso) return "TBD";
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function shortDate(iso: string | null | undefined): string {
  if (!iso) return "TBD";
  const d = new Date(iso);
  return d.toLocaleString(undefined, { month: "short", day: "numeric" });
}

export function timeOnly(iso: string | null | undefined): string {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleString(undefined, { hour: "2-digit", minute: "2-digit" });
}

export function probBar(p: Probs) {
  return [
    { cls: "h", w: p.home },
    { cls: "d", w: p.draw },
    { cls: "a", w: p.away },
  ];
}

export function maxOutcome(p: Probs): Outcome {
  if (p.home >= p.draw && p.home >= p.away) return "home";
  if (p.away >= p.home && p.away >= p.draw) return "away";
  return "draw";
}

export function prettyStage(stage: string | null | undefined): string {
  if (!stage) return "World Cup";
  return stage
    .split("-")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

// Pick a readable text color (black/white) for a given hex background.
export function readableOn(hex: string | null | undefined): string {
  if (!hex) return "#fff";
  const c = hex.replace("#", "");
  if (c.length < 6) return "#fff";
  const r = parseInt(c.slice(0, 2), 16);
  const g = parseInt(c.slice(2, 4), 16);
  const b = parseInt(c.slice(4, 6), 16);
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return luminance > 0.6 ? "#0a0e16" : "#ffffff";
}
