"use client";

import type { Timeline } from "@/lib/sim";
import { TOTAL_STEPS } from "@/lib/sim";

const SPEEDS = [0.5, 1, 1.5, 2];

function roundForStep(step: number): string {
  if (step <= 0) return "Ready";
  if (step <= 16) return `Round of 32 · ${step}/16`;
  if (step <= 24) return `Round of 16 · ${step - 16}/8`;
  if (step <= 28) return `Quarter-finals · ${step - 24}/4`;
  if (step <= 30) return `Semi-finals · ${step - 28}/2`;
  return "Final";
}

export default function SimControls({ tl }: { tl: Timeline }) {
  return (
    <div className="simctl">
      <div className="simctl-row">
        <button className="simbtn simbtn-primary" onClick={tl.toggle}>
          {tl.playing ? (
            <>
              <span className="ico-pause" /> Pause
            </>
          ) : (
            <>
              <span className="ico-play" /> {tl.done ? "Replay" : "Play simulation"}
            </>
          )}
        </button>
        <button className="simbtn" onClick={tl.reset} disabled={tl.step === 0 && !tl.playing}>
          Reset
        </button>
        <div className="simctl-stage">{roundForStep(tl.step)}</div>
        <div className="simctl-speeds">
          {SPEEDS.map((s) => (
            <button
              key={s}
              className={`speedbtn ${tl.speed === s ? "active" : ""}`}
              onClick={() => tl.setSpeed(s)}
            >
              {s}x
            </button>
          ))}
        </div>
      </div>
      <input
        className="simscrub"
        type="range"
        min={0}
        max={TOTAL_STEPS}
        value={tl.step}
        onChange={(e) => {
          tl.pause();
          tl.setStep(Number(e.target.value));
        }}
        style={{ ["--p" as string]: `${(tl.step / TOTAL_STEPS) * 100}%` }}
      />
    </div>
  );
}
