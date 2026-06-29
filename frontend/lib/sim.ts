// Helpers that turn a BracketSim into something the animated canvas can render and play:
// the fixed left/right layout of the 2026 knockout tree, who-feeds-whom links, and a small
// play/pause/scrub timeline hook driven by requestAnimationFrame (no animation deps).

import { useCallback, useEffect, useRef, useState } from "react";
import type { BracketMatch, BracketSim, Side } from "./types";

// The 2026 bracket splits cleanly into two halves that meet in the final. These are the
// match ids (see backend/oracle/bracket.py) stacked top-to-bottom so feeders sit adjacent.
export const LAYOUT = {
  left: {
    R32: [1, 3, 2, 5, 11, 12, 9, 10],
    R16: [17, 18, 21, 22],
    QF: [25, 26],
    SF: [29],
  },
  right: {
    R32: [4, 6, 7, 8, 14, 16, 13, 15],
    R16: [19, 20, 23, 24],
    QF: [27, 28],
    SF: [30],
  },
} as const;

export const FINAL_ID = 31;
export const TOTAL_STEPS = 31; // R32(16) + R16(8) + QF(4) + SF(2) + Final(1)

export const ROUND_CODES = ["R32", "R16", "QF", "SF"] as const;

export function matchMap(sim: BracketSim): Map<number, BracketMatch> {
  const m = new Map<number, BracketMatch>();
  for (const r of sim.rounds) for (const match of r.matches) m.set(match.id, match);
  return m;
}

// For each match slot, which earlier match feeds it (null for Round of 32).
export function feederMap(sim: BracketSim): Map<string, number> {
  const f = new Map<string, number>();
  for (const r of sim.rounds) {
    for (const match of r.matches) {
      if (match.feeds) {
        const [target, slot] = match.feeds;
        f.set(`${target}:${slot}`, match.id);
      }
    }
  }
  return f;
}

export function sideOf(matchId: number): "left" | "right" | "final" {
  if (matchId === FINAL_ID) return "final";
  for (const code of ROUND_CODES) {
    if ((LAYOUT.left[code] as readonly number[]).includes(matchId)) return "left";
    if ((LAYOUT.right[code] as readonly number[]).includes(matchId)) return "right";
  }
  return "left";
}

// A match is "decided" once the playhead passes its id; teams in a slot are "known" as soon
// as the match that feeds that slot is decided (so winners visibly flow into the next round).
export function isDecided(matchId: number, step: number): boolean {
  return step >= matchId;
}

export function slotKnown(
  match: BracketMatch,
  slot: Side,
  step: number,
  feeders: Map<string, number>,
): boolean {
  if (match.round === "R32") return true;
  const feeder = feeders.get(`${match.id}:${slot}`);
  return feeder !== undefined && step >= feeder;
}

export interface Timeline {
  step: number;
  playing: boolean;
  speed: number;
  play: () => void;
  pause: () => void;
  toggle: () => void;
  reset: () => void;
  setStep: (s: number) => void;
  setSpeed: (s: number) => void;
  done: boolean;
}

// Advances one bracket match per tick; `speed` scales the dwell time per match.
export function useTimeline(total = TOTAL_STEPS, msPerStep = 850): Timeline {
  const [step, setStep] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const last = useRef<number | null>(null);
  const raf = useRef<number | null>(null);

  useEffect(() => {
    if (!playing) return;
    const tick = (t: number) => {
      if (last.current === null) last.current = t;
      const elapsed = t - last.current;
      if (elapsed >= msPerStep / speed) {
        last.current = t;
        setStep((s) => {
          if (s >= total) {
            setPlaying(false);
            return s;
          }
          return s + 1;
        });
      }
      raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => {
      if (raf.current) cancelAnimationFrame(raf.current);
      last.current = null;
    };
  }, [playing, speed, total, msPerStep]);

  const play = useCallback(() => {
    setStep((s) => (s >= total ? 0 : s));
    setPlaying(true);
  }, [total]);
  const pause = useCallback(() => setPlaying(false), []);
  const toggle = useCallback(() => setPlaying((p) => !p), []);
  const reset = useCallback(() => {
    setPlaying(false);
    setStep(0);
  }, []);

  return {
    step,
    playing,
    speed,
    play,
    pause,
    toggle,
    reset,
    setStep,
    setSpeed,
    done: step >= total,
  };
}
