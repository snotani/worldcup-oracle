"use client";

import type { BracketSim } from "@/lib/types";
import { TeamCrest } from "@/components/primitives";
import { IconTrophy } from "@/components/icons";

export default function ChampionReveal({ sim, show }: { sim: BracketSim; show: boolean }) {
  if (!show) return null;
  const champ = sim.champion;
  return (
    <div className="reveal">
      <div className="reveal-top" style={{ ["--team" as string]: champ.color ?? "var(--gold)" }}>
        <span className="reveal-glow" />
        <IconTrophy size={20} />
        <span className="reveal-eyebrow">Predicted champion</span>
        <TeamCrest team={champ} size={64} />
        <div className="reveal-name">{champ.name}</div>
        <div className="reveal-sub">
          beat {sim.runner_up.name} {sim.final.score} in the final
        </div>
      </div>

      <div className="reveal-path">
        <div className="reveal-path-title">{champ.name}&apos;s road to the trophy</div>
        <div className="path-chips">
          {sim.path.map((m) => (
            <div key={m.id} className={`path-chip ${m.is_upset ? "path-upset" : ""}`}>
              <span className="path-round">{m.round_name}</span>
              <span className="path-result">
                <TeamCrest team={m.winner === "home" ? m.home : m.away} size={16} />
                {m.score}
                <TeamCrest team={m.winner === "home" ? m.away : m.home} size={16} />
              </span>
              <span className="path-opp">vs {m.loser_name}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
