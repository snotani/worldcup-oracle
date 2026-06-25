"use client";

import { useMemo, useState } from "react";
import type { PersonaCard } from "@/lib/types";
import TraceView from "./TraceView";
import { Donut, TeamCrest } from "./primitives";
import { kickoff, outcomeLabel, pct, prettyStage } from "@/lib/format";
import { modelBrand, personaBrand } from "@/lib/brands";
import { ModelLogo } from "./ModelLogo";
import { IconPin } from "./icons";

function Card({ c }: { c: PersonaCard }) {
  const pb = personaBrand(c.persona);
  const brand = c.model_id ? modelBrand(c.model_id) : null;
  return (
    <div className="card persona-card" style={{ background: pb.gradient }}>
      <div className="persona-glow" style={{ background: pb.color }} />
      <div className="persona-top">
        <div className="persona-id">
          <span className="persona-avatar" style={{ borderColor: pb.color }}>
            {pb.emoji}
          </span>
          <div>
            <div className="persona-name" style={{ color: pb.color }}>
              {c.persona_name}
            </div>
            <div className="muted small">{prettyStage(c.stage)}</div>
          </div>
        </div>
        <div className="muted small persona-kick">{kickoff(c.kickoff_utc)}</div>
      </div>

      <div className="persona-matchup">
        <div className="pm-team">
          <TeamCrest team={c.home} name={c.home_team} size={48} />
          <span className="pm-name">{c.home_team}</span>
        </div>
        <span className="pm-vs">vs</span>
        <div className="pm-team">
          <TeamCrest team={c.away} name={c.away_team} size={48} />
          <span className="pm-name">{c.away_team}</span>
        </div>
      </div>

      {c.persona_message && <p className="persona-quote">“{c.persona_message}”</p>}

      <div className="persona-verdict">
        <Donut probs={c.probs} size={120} />
        <div className="verdict-side">
          <div className="verdict-pick" style={{ color: pb.color }}>
            {outcomeLabel(c.pick, c.home_team, c.away_team)}
          </div>
          {c.predicted_score && <div className="verdict-score">{c.predicted_score}</div>}
          <div className="verdict-probs">
            <span>
              <i className="swatch sw-h" /> {c.home_team} {pct(c.probs.home)}
            </span>
            <span>
              <i className="swatch sw-d" /> Draw {pct(c.probs.draw)}
            </span>
            <span>
              <i className="swatch sw-a" /> {c.away_team} {pct(c.probs.away)}
            </span>
          </div>
        </div>
      </div>

      <div className="persona-foot">
        <span className="watermark">⚡ The Oracle</span>
        {c.venue && (
          <span className="muted small">
            <IconPin size={11} /> {c.venue}
          </span>
        )}
        {brand && (
          <span className="powered-by muted small">
            powered by
            <span className="powered-logo" style={{ color: brand.color }}>
              <ModelLogo name={c.model_id!} size={13} />
            </span>
            {brand.label}
          </span>
        )}
      </div>

      <TraceView trace={c.trace} />
    </div>
  );
}

// Angle C: same predictions, wrapped in a character voice. Built to be screenshot-shareable.
export default function CardsView({ cards }: { cards: PersonaCard[] }) {
  const personas = useMemo(() => {
    const seen = new Map<string, string>();
    cards.forEach((c) => seen.set(c.persona, c.persona_name));
    return Array.from(seen.entries()).map(([id, name]) => ({ id, name }));
  }, [cards]);
  const [active, setActive] = useState<string>("all");
  const shown = active === "all" ? cards : cards.filter((c) => c.persona === active);

  return (
    <div className="stack">
      <div className="persona-switch">
        <button
          className={`pswitch ${active === "all" ? "active" : ""}`}
          onClick={() => setActive("all")}
        >
          All voices
        </button>
        {personas.map((p) => {
          const pb = personaBrand(p.id);
          return (
            <button
              key={p.id}
              className={`pswitch ${active === p.id ? "active" : ""}`}
              onClick={() => setActive(p.id)}
              style={active === p.id ? { borderColor: pb.color, color: pb.color } : undefined}
            >
              <span>{pb.emoji}</span> {p.name}
            </button>
          );
        })}
      </div>

      <div className="grid cols-2">
        {shown.map((c) => (
          <Card key={`${c.match_id}-${c.persona}`} c={c} />
        ))}
      </div>
    </div>
  );
}
