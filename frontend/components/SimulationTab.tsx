"use client";

import type { AgentFeature, BracketSim } from "@/lib/types";
import { useTimeline } from "@/lib/sim";
import { IconBrain, IconGitBranch, IconFlame } from "@/components/icons";
import { TeamCrest } from "@/components/primitives";
import BracketCanvas from "@/components/bracket/BracketCanvas";
import SimControls from "@/components/bracket/SimControls";
import ChampionReveal from "@/components/bracket/ChampionReveal";
import FeatureReel from "@/components/FeatureReel";

export default function SimulationTab({
  sim,
  features,
}: {
  sim: BracketSim;
  features: AgentFeature[];
}) {
  const tl = useTimeline();

  return (
    <div className="stack">
      <div className="card">
        <div className="card-head">
          <h3>
            <IconBrain size={18} /> What the agent looks at
          </h3>
          <span className="muted small">{features.length} signals per match</span>
        </div>
        <FeatureReel features={features} />
      </div>

      <div className="card">
        <div className="card-head">
          <h3>
            <IconGitBranch size={18} /> The simulation
          </h3>
          <span className="muted small">Round of 32 → Final · press play</span>
        </div>
        <SimControls tl={tl} />
        <BracketCanvas sim={sim} step={tl.step} size="md" />
      </div>

      <ChampionReveal sim={sim} show={tl.done} />

      {sim.upsets.length > 0 && (
        <div className="card">
          <div className="card-head">
            <h3>
              <IconFlame size={18} /> Upsets the agent is calling
            </h3>
          </div>
          <div className="path-chips">
            {sim.upsets.map((u) => (
              <div key={u.id} className="path-chip path-upset">
                <span className="path-round">{u.round_name}</span>
                <span className="path-result">
                  <TeamCrest team={u.winner === "home" ? u.home : u.away} size={16} /> {u.score}
                </span>
                <span className="path-opp">
                  {u.winner_name} over {u.loser_name}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
