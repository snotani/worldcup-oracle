"use client";

import { useMemo, useState } from "react";
import type { BracketSim, Consensus, TeamMeta } from "@/lib/types";
import { useTimeline } from "@/lib/sim";
import { modelBrand } from "@/lib/brands";
import { readableOn } from "@/lib/format";
import { ModelLogo } from "@/components/ModelLogo";
import { TeamCrest } from "@/components/primitives";
import { IconTrophy, IconScale, IconGitBranch } from "@/components/icons";
import BracketCanvas from "@/components/bracket/BracketCanvas";
import SimControls from "@/components/bracket/SimControls";

function buildTeamLookup(brackets: BracketSim[]): Map<string, TeamMeta> {
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

export default function ModelBattleTab({
  brackets,
  consensus,
}: {
  brackets: BracketSim[];
  consensus: Consensus;
}) {
  const [active, setActive] = useState(0);
  const tl = useTimeline();
  const sim = brackets[active];
  const teams = useMemo(() => buildTeamLookup(brackets), [brackets]);

  const votes = Object.entries(consensus.champion_votes).sort((a, b) => b[1] - a[1]);

  return (
    <div className="stack">
      <div className="card">
        <div className="card-head">
          <h3>
            <IconTrophy size={18} /> Five models, five brackets
          </h3>
          <span className="muted small">tap a model to watch its run</span>
        </div>
        <div className="champ-strip">
          {brackets.map((b, i) => {
            const brand = modelBrand(b.model_name);
            return (
              <button
                key={b.model_id}
                className={`champ-cardm ${i === active ? "active" : ""}`}
                onClick={() => setActive(i)}
              >
                <span className="champ-cardm-model">
                  <span
                    className="champ-cardm-avatar"
                    style={{ background: brand.color, color: readableOn(brand.color) }}
                  >
                    <ModelLogo name={b.model_name} size={14} />
                  </span>
                  {brand.label}
                </span>
                <TeamCrest team={b.champion} size={38} />
                <span className="champ-cardm-name">{b.champion.name}</span>
                <span className="champ-cardm-sub">def. {b.runner_up.name}</span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="card">
        <div className="card-head">
          <h3>
            <IconGitBranch size={18} /> {modelBrand(sim.model_name).label}&apos;s predicted path
          </h3>
          <span className="muted small">champion: {sim.champion.name}</span>
        </div>
        <SimControls tl={tl} />
        <BracketCanvas key={sim.model_id} sim={sim} step={tl.step} size="sm" />
      </div>

      <div className="card">
        <div className="card-head">
          <h3>
            <IconScale size={18} /> Where they agree &amp; disagree
          </h3>
          <span className="muted small">
            {consensus.distinct_champions} distinct champions · {Math.round(
              consensus.r32_agreement * 100,
            )}
            % R32 agreement
          </span>
        </div>

        <div className="muted small" style={{ marginBottom: 8 }}>
          Title votes
        </div>
        <div className="consensus-bar">
          {votes.map(([name, count]) => {
            const t = teams.get(name);
            return (
              <span className="vote-pill" key={name}>
                {t && <TeamCrest team={t} size={18} />}
                {name}
                <span className="vote-count">
                  {count}/{consensus.consensus_champion.of}
                </span>
              </span>
            );
          })}
        </div>

        {consensus.contested.length > 0 && (
          <>
            <div className="muted small" style={{ margin: "18px 0 4px" }}>
              Most contested first-round calls
            </div>
            <div>
              {consensus.contested.map((c) => (
                <div className="contested-row" key={c.id}>
                  <span className="contested-teams">
                    <TeamCrest team={c.home} size={20} /> {c.home.name}
                    <span className="muted" style={{ margin: "0 4px" }}>
                      v
                    </span>
                    <TeamCrest team={c.away} size={20} /> {c.away.name}
                  </span>
                  <span className="contested-split">{c.split} split</span>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
