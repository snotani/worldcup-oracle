"use client";

import { useMemo, useState } from "react";
import type { BracketSim, Consensus, TeamMeta } from "@/lib/types";
import { modelBrand } from "@/lib/brands";
import { readableOn } from "@/lib/format";
import { ModelLogo } from "@/components/ModelLogo";
import { TeamCrest } from "@/components/primitives";
import { IconTrophy } from "@/components/icons";

function teamLookup(brackets: BracketSim[]): Map<string, TeamMeta> {
  const m = new Map<string, TeamMeta>();
  for (const b of brackets) {
    for (const t of [b.champion, b.runner_up, ...b.finalists]) m.set(t.name, t);
    for (const r of b.rounds)
      for (const match of r.matches) {
        m.set(match.home.name, match.home);
        m.set(match.away.name, match.away);
      }
  }
  return m;
}

function semifinalists(b: BracketSim): TeamMeta[] {
  const sf = b.rounds.find((r) => r.code === "SF");
  if (!sf) return [];
  const out: TeamMeta[] = [];
  for (const match of sf.matches) {
    out.push(match.home, match.away);
  }
  return out;
}

export default function ModelBattleTab({
  brackets,
  consensus,
}: {
  brackets: BracketSim[];
  consensus: Consensus;
}) {
  const teams = useMemo(() => teamLookup(brackets), [brackets]);
  const [playKey, setPlayKey] = useState(0);
  const votes = Object.entries(consensus.champion_votes).sort((a, b) => b[1] - a[1]);
  const cc = consensus.consensus_champion;

  return (
    <div className="reel">
      <div className="reel-card" key={playKey}>
        <div className="reel-head">
          <span className="reel-eyebrow">5 AI MODELS · ONE TROPHY</span>
          <h2 className="reel-title">Who wins the 2026 World Cup?</h2>
        </div>

        <div
          className="reel-hero"
          style={{ ["--team" as string]: cc.meta.color ?? "var(--gold)" }}
        >
          <span className="reel-hero-glow" />
          <span className="reel-hero-badge">
            <IconTrophy size={13} /> CONSENSUS PICK
          </span>
          <TeamCrest team={cc.meta} size={88} />
          <div className="reel-hero-name">{cc.name}</div>
          <div className="reel-hero-sub">
            {cc.votes} of {cc.of} models agree
          </div>
          <div className="reel-votes">
            {votes.map(([name, count]) => {
              const t = teams.get(name);
              return (
                <span className="reel-vote" key={name}>
                  {t && <TeamCrest team={t} size={20} />}
                  <b>{count}</b>
                </span>
              );
            })}
          </div>
        </div>

        <div className="reel-list">
          {brackets.map((b, i) => {
            const brand = modelBrand(b.model_name);
            const four = semifinalists(b);
            return (
              <div className="reel-row" key={b.model_id} style={{ animationDelay: `${250 + i * 220}ms` }}>
                <div className="reel-row-head">
                  <span className="reel-model">
                    <span
                      className="reel-avatar"
                      style={{ background: brand.color, color: readableOn(brand.color) }}
                    >
                      <ModelLogo name={b.model_name} size={15} />
                    </span>
                    <span className="reel-model-name">{brand.label}</span>
                  </span>
                  <span className="reel-pick">
                    <TeamCrest team={b.champion} size={34} />
                    <span className="reel-pick-text">
                      <span className="reel-pick-name">{b.champion.name}</span>
                      <span className="reel-pick-sub">def. {b.runner_up.name}</span>
                    </span>
                  </span>
                </div>
                <div className="reel-four">
                  <span className="reel-four-label">Final 4</span>
                  {four.map((t, j) => (
                    <TeamCrest key={j} team={t} size={20} />
                  ))}
                </div>
              </div>
            );
          })}
        </div>

        <button className="reel-replay" onClick={() => setPlayKey((k) => k + 1)}>
          ▶ Replay reveal
        </button>
      </div>
    </div>
  );
}
