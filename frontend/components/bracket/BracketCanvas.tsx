"use client";

import { useCallback, useLayoutEffect, useRef, useState } from "react";
import type { BracketSim } from "@/lib/types";
import {
  FINAL_ID,
  LAYOUT,
  ROUND_CODES,
  feederMap,
  isDecided,
  matchMap,
  sideOf,
  slotKnown,
} from "@/lib/sim";
import { TeamCrest } from "@/components/primitives";
import { IconTrophy } from "@/components/icons";
import { BracketMatchNode } from "./BracketMatch";

interface Conn {
  id: number;
  d: string;
  source: number; // source match id (connector lights up once it's decided)
}

const ROUND_LABEL: Record<string, string> = {
  R32: "Round of 32",
  R16: "Round of 16",
  QF: "Quarters",
  SF: "Semis",
};

export default function BracketCanvas({
  sim,
  step,
  size = "md",
}: {
  sim: BracketSim;
  step: number;
  size?: "sm" | "md";
}) {
  const matches = matchMap(sim);
  const feeders = feederMap(sim);
  const containerRef = useRef<HTMLDivElement>(null);
  const nodeRefs = useRef<Map<number, HTMLDivElement>>(new Map());
  const [conns, setConns] = useState<Conn[]>([]);
  const [dims, setDims] = useState({ w: 0, h: 0 });

  const setNodeRef = useCallback((id: number) => {
    return (el: HTMLDivElement | null) => {
      if (el) nodeRefs.current.set(id, el);
      else nodeRefs.current.delete(id);
    };
  }, []);

  const measure = useCallback(() => {
    const container = containerRef.current;
    if (!container) return;
    const base = container.getBoundingClientRect();
    setDims({ w: base.width, h: base.height });
    const next: Conn[] = [];
    for (const m of matches.values()) {
      if (!m.feeds) continue;
      const [targetId] = m.feeds;
      const srcEl = nodeRefs.current.get(m.id);
      const tgtEl = nodeRefs.current.get(targetId);
      if (!srcEl || !tgtEl) continue;
      const s = srcEl.getBoundingClientRect();
      const t = tgtEl.getBoundingClientRect();
      const side = sideOf(m.id);
      const sx = side === "right" ? s.left - base.left : s.right - base.left;
      const tx =
        side === "right"
          ? t.right - base.left
          : sideOf(targetId) === "final"
            ? t.left - base.left
            : t.left - base.left;
      const sy = s.top - base.top + s.height / 2;
      const ty = t.top - base.top + t.height / 2;
      const mx = (sx + tx) / 2;
      next.push({ id: m.id, source: m.id, d: `M ${sx} ${sy} H ${mx} V ${ty} H ${tx}` });
    }
    setConns(next);
  }, [matches]);

  useLayoutEffect(() => {
    measure();
    const ro = new ResizeObserver(() => measure());
    if (containerRef.current) ro.observe(containerRef.current);
    window.addEventListener("resize", measure);
    return () => {
      ro.disconnect();
      window.removeEventListener("resize", measure);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sim]);

  const renderCol = (sideKey: "left" | "right", code: keyof typeof LAYOUT.left) => {
    const ids = LAYOUT[sideKey][code] as readonly number[];
    return (
      <div className={`bcol bcol-${code.toLowerCase()}`} key={`${sideKey}-${code}`}>
        {ids.map((id) => {
          const m = matches.get(id);
          if (!m) return null;
          const decided = isDecided(id, step);
          return (
            <BracketMatchNode
              key={id}
              ref={setNodeRef(id)}
              match={m}
              homeKnown={slotKnown(m, "home", step, feeders)}
              awayKnown={slotKnown(m, "away", step, feeders)}
              decided={decided}
              active={step === id}
              size={size}
            />
          );
        })}
      </div>
    );
  };

  const final = matches.get(FINAL_ID)!;
  const finalDecided = isDecided(FINAL_ID, step);
  const champion = finalDecided ? final[final.winner] : null;

  return (
    <div className={`bracket-canvas bracket-${size}`} ref={containerRef}>
      <svg className="bracket-lines" width={dims.w} height={dims.h}>
        {conns.map((c) => (
          <path
            key={c.id}
            d={c.d}
            className={`bline ${isDecided(c.source, step) ? "bline-on" : ""}`}
            fill="none"
          />
        ))}
      </svg>

      <div className="bracket-side bracket-left">
        {ROUND_CODES.map((code) => renderCol("left", code))}
      </div>

      <div className="bracket-center">
        <div className="bcenter-label">Final</div>
        <BracketMatchNode
          ref={setNodeRef(FINAL_ID)}
          match={final}
          homeKnown={slotKnown(final, "home", step, feeders)}
          awayKnown={slotKnown(final, "away", step, feeders)}
          decided={finalDecided}
          active={step === FINAL_ID}
          size={size}
        />
        <div className={`champ-pod ${champion ? "champ-on" : ""}`}>
          <IconTrophy size={size === "sm" ? 18 : 26} />
          {champion ? (
            <>
              <TeamCrest team={champion} size={size === "sm" ? 26 : 40} />
              <div className="champ-name">{champion.name}</div>
              <div className="champ-tag">Predicted champion</div>
            </>
          ) : (
            <div className="champ-tag champ-wait">Lifts the trophy?</div>
          )}
        </div>
      </div>

      <div className="bracket-side bracket-right">
        {[...ROUND_CODES].reverse().map((code) => renderCol("right", code))}
      </div>
    </div>
  );
}
