import { forwardRef } from "react";
import type { BracketMatch, Side } from "@/lib/types";
import { TeamCrest } from "@/components/primitives";
import { IconFlame } from "@/components/icons";

function TeamRow({
  side,
  match,
  known,
  decided,
  size,
}: {
  side: Side;
  match: BracketMatch;
  known: boolean;
  decided: boolean;
  size: "sm" | "md";
}) {
  const team = match[side];
  const adv = side === "home" ? match.home_adv : match.away_adv;
  const isWinner = decided && match.winner === side;
  const isLoser = decided && match.winner !== side;
  const crest = size === "sm" ? 16 : 22;

  return (
    <div className={`bm-team ${isWinner ? "bm-win" : ""} ${isLoser ? "bm-lose" : ""}`}>
      <span
        className="bm-fill"
        style={{ width: decided || match.round === "R32" ? `${Math.round(adv * 100)}%` : "0%" }}
      />
      <span className="bm-team-main">
        {known ? (
          <>
            <TeamCrest team={team} size={crest} />
            <span className="bm-name">{size === "sm" ? team.abbr : team.name}</span>
          </>
        ) : (
          <>
            <span className="bm-crest-tbd" style={{ width: crest, height: crest }} />
            <span className="bm-name bm-tbd">TBD</span>
          </>
        )}
      </span>
      {known && (decided || match.round === "R32") && (
        <span className="bm-adv">{Math.round(adv * 100)}%</span>
      )}
    </div>
  );
}

interface Props {
  match: BracketMatch;
  homeKnown: boolean;
  awayKnown: boolean;
  decided: boolean;
  active: boolean;
  size?: "sm" | "md";
  dimmed?: boolean;
}

export const BracketMatchNode = forwardRef<HTMLDivElement, Props>(function BracketMatchNode(
  { match, homeKnown, awayKnown, decided, active, size = "md", dimmed = false },
  ref,
) {
  return (
    <div
      ref={ref}
      className={`bm ${active ? "bm-active" : ""} ${decided ? "bm-decided" : ""} ${
        dimmed ? "bm-dim" : ""
      }`}
      data-match={match.id}
    >
      <TeamRow side="home" match={match} known={homeKnown} decided={decided} size={size} />
      <TeamRow side="away" match={match} known={awayKnown} decided={decided} size={size} />
      <div className="bm-foot">
        {decided ? (
          <span className="bm-score">{match.score}</span>
        ) : (
          <span className="bm-round">{size === "sm" ? "" : match.round}</span>
        )}
        {decided && match.is_result && <span className="bm-badge bm-ft">FT</span>}
        {decided && match.is_upset && (
          <span className="bm-badge bm-upset">
            <IconFlame size={10} /> UPSET
          </span>
        )}
      </div>
    </div>
  );
});
