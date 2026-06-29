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
  const fitRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const nodeRefs = useRef<Map<number, HTMLDivElement>>(new Map());
  const [conns, setConns] = useState<Conn[]>([]);
  const [dims, setDims] = useState({ w: 0, h: 0 });
  const [scale, setScale] = useState(1);

  const setNodeRef = useCallback((id: number) => {
    return (el: HTMLDivElement | null) => {
      if (el) nodeRefs.current.set(id, el);
      else nodeRefs.current.delete(id);
    };
  }, []);

  const measure = useCallback(() => {
    const fit = fitRef.current;
    const container = containerRef.current;
    if (!fit || !container) return;

    // scrollWidth/Height are layout pixels, unaffected by the CSS transform we apply, so we
    // can derive the fit-scale and then convert measured (scaled) positions back to local px.
    const naturalW = container.scrollWidth;
    const naturalH = container.scrollHeight;
    const s = naturalW > 0 ? Math.min(1, fit.clientWidth / naturalW) : 1;

    const base = container.getBoundingClientRect();
    const next: Conn[] = [];
    for (const m of matches.values()) {
      if (!m.feeds) continue;
      const [targetId] = m.feeds;
      const srcEl = nodeRefs.current.get(m.id);
      const tgtEl = nodeRefs.current.get(targetId);
      if (!srcEl || !tgtEl) continue;
      const src = srcEl.getBoundingClientRect();
      const tgt = tgtEl.getBoundingClientRect();
      const side = sideOf(m.id);
      const sx = (((side === "right" ? src.left : src.right) - base.left) / s);
      const tx = (((side === "right" ? tgt.right : tgt.left) - base.left) / s);
      const sy = (src.top - base.top + src.height / 2) / s;
      const ty = (tgt.top - base.top + tgt.height / 2) / s;
      const mx = (sx + tx) / 2;
      next.push({ id: m.id, source: m.id, d: `M ${sx} ${sy} H ${mx} V ${ty} H ${tx}` });
    }
    setScale(s);
    setDims({ w: naturalW, h: naturalH });
    setConns(next);
  }, [matches]);

  useLayoutEffect(() => {
    measure();
    const ro = new ResizeObserver(() => measure());
    if (fitRef.current) ro.observe(fitRef.current);
    if (containerRef.current) ro.observe(containerRef.current);
    window.addEventListener("resize", measure);
    return () => {
      ro.disconnect();
      window.removeEventListener("resize", measure);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sim, size]);

  const renderCol = (sideKey: "left" | "right", code: keyof typeof LAYOUT.left) => {
    const ids = LAYOUT[sideKey][code] as readonly number[];
    return (
      <div className={`bcol bcol-${code.toLowerCase()}`} key={`${sideKey}-${code}`}>
        {ids.map((id) => {
          const m = matches.get(id);
          if (!m) return null;
          return (
            <BracketMatchNode
              key={id}
              ref={setNodeRef(id)}
              match={m}
              homeKnown={slotKnown(m, "home", step, feeders)}
              awayKnown={slotKnown(m, "away", step, feeders)}
              decided={isDecided(id, step)}
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
    <div className="bracket-fit" ref={fitRef} style={{ height: dims.h ? dims.h * scale : undefined }}>
      <div
        className={`bracket-canvas bracket-${size}`}
        ref={containerRef}
        style={{ transform: `scale(${scale})`, transformOrigin: "top left" }}
      >
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
    </div>
  );
}
