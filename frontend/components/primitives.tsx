import type { Outcome, Probs, TeamMeta } from "@/lib/types";
import { pct, readableOn } from "@/lib/format";
import { modelBrand } from "@/lib/brands";
import { ModelLogo } from "./ModelLogo";

/* ---------- Team crest (logo with graceful fallback to colored monogram) ---------- */

export function TeamCrest({
  team,
  name,
  size = 34,
}: {
  team?: TeamMeta;
  name?: string;
  size?: number;
}) {
  const label = team?.name ?? name ?? "?";
  const abbr = team?.abbr ?? label.slice(0, 3).toUpperCase();
  const color = team?.color ?? "#243049";
  if (team?.logo) {
    // eslint-disable-next-line @next/next/no-img-element
    return (
      <img
        src={team.logo}
        alt={label}
        width={size}
        height={size}
        className="crest"
        style={{ width: size, height: size }}
      />
    );
  }
  return (
    <span
      className="crest crest-fallback"
      style={{
        width: size,
        height: size,
        background: color,
        color: readableOn(color),
        fontSize: size * 0.32,
      }}
    >
      {abbr}
    </span>
  );
}

/* ---------- Probability bar (segmented H / D / A) ---------- */

export function ProbBar({
  probs,
  pick,
  height = 12,
  showLabels = false,
  homeName = "Home",
  awayName = "Away",
}: {
  probs: Probs;
  pick?: Outcome;
  height?: number;
  showLabels?: boolean;
  homeName?: string;
  awayName?: string;
}) {
  const segs: { key: Outcome; w: number; cls: string }[] = [
    { key: "home", w: probs.home, cls: "seg-h" },
    { key: "draw", w: probs.draw, cls: "seg-d" },
    { key: "away", w: probs.away, cls: "seg-a" },
  ];
  return (
    <div className="probwrap">
      <div className="probbar" style={{ height }}>
        {segs.map((s) => (
          <span
            key={s.key}
            className={`${s.cls} ${pick && pick === s.key ? "seg-pick" : ""}`}
            style={{ width: `${Math.max(s.w * 100, 0)}%` }}
          />
        ))}
      </div>
      {showLabels && (
        <div className="problabels">
          <span className="lab-h">
            {homeName} <b>{pct(probs.home)}</b>
          </span>
          <span className="lab-d">
            Draw <b>{pct(probs.draw)}</b>
          </span>
          <span className="lab-a">
            {awayName} <b>{pct(probs.away)}</b>
          </span>
        </div>
      )}
    </div>
  );
}

/* ---------- Donut (probability ring used on persona cards) ---------- */

export function Donut({ probs, size = 132 }: { probs: Probs; size?: number }) {
  const r = size / 2 - 12;
  const c = 2 * Math.PI * r;
  const segs = [
    { v: probs.home, color: "var(--c-home)" },
    { v: probs.draw, color: "var(--c-draw)" },
    { v: probs.away, color: "var(--c-away)" },
  ];
  let offset = 0;
  const top = Math.max(probs.home, probs.draw, probs.away);
  const topLabel = top === probs.home ? "HOME" : top === probs.away ? "AWAY" : "DRAW";
  return (
    <div className="donut" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <g transform={`rotate(-90 ${size / 2} ${size / 2})`}>
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth={14}
          />
          {segs.map((s, i) => {
            const len = s.v * c;
            const el = (
              <circle
                key={i}
                cx={size / 2}
                cy={size / 2}
                r={r}
                fill="none"
                stroke={s.color}
                strokeWidth={14}
                strokeDasharray={`${len} ${c - len}`}
                strokeDashoffset={-offset}
                strokeLinecap="butt"
              />
            );
            offset += len;
            return el;
          })}
        </g>
      </svg>
      <div className="donut-center">
        <div className="donut-pct">{pct(top)}</div>
        <div className="donut-label">{topLabel}</div>
      </div>
    </div>
  );
}

/* ---------- Model badge (brand avatar + label) ---------- */

export function ModelBadge({
  name,
  modelId,
  size = "md",
  showProvider = false,
}: {
  name: string;
  modelId?: string;
  size?: "sm" | "md";
  showProvider?: boolean;
}) {
  const b = modelBrand(name);
  const dim = size === "sm" ? 24 : 30;
  return (
    <span className="modelbadge">
      <span
        className="model-avatar"
        style={{ background: b.color, color: readableOn(b.color), width: dim, height: dim }}
      >
        <ModelLogo name={name} size={dim * 0.58} />
      </span>
      <span className="model-meta">
        <span className="model-label">{b.label}</span>
        {showProvider && <span className="model-provider">{b.provider}</span>}
        {!showProvider && modelId && <span className="model-provider">{modelId}</span>}
      </span>
    </span>
  );
}

/* ---------- KPI stat tile ---------- */

export function Kpi({
  icon,
  label,
  value,
  sub,
  accent = "var(--accent)",
}: {
  icon: React.ReactNode;
  label: string;
  value: React.ReactNode;
  sub?: React.ReactNode;
  accent?: string;
}) {
  return (
    <div className="kpi">
      <div className="kpi-icon" style={{ color: accent, background: `${accent}1a` }}>
        {icon}
      </div>
      <div className="kpi-body">
        <div className="kpi-label">{label}</div>
        <div className="kpi-value">{value}</div>
        {sub && <div className="kpi-sub">{sub}</div>}
      </div>
    </div>
  );
}

/* ---------- Recent-form pips (W/D/L) ---------- */

export function FormPips({ form }: { form: string[] }) {
  if (!form?.length) return null;
  return (
    <span className="formpips">
      {form.map((r, i) => (
        <span key={i} className={`pip pip-${r.toLowerCase()}`}>
          {r}
        </span>
      ))}
    </span>
  );
}
