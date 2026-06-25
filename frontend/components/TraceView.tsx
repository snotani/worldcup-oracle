"use client";

import { useState } from "react";
import type { RunTrace } from "@/lib/types";
import {
  IconBrain,
  IconBolt,
  IconChevron,
  IconDatabase,
  IconGitBranch,
  IconScale,
  IconSparkles,
  IconTarget,
} from "./icons";

// Maps a trace step name to an icon so the "how the agent thought" timeline reads
// like a real pipeline. This is the explainability centerpiece for the video.
function stepIcon(name: string) {
  const n = name.toLowerCase();
  if (n.includes("context") || n.includes("fetch") || n.includes("data")) return <IconDatabase size={14} />;
  if (n.includes("prompt") || n.includes("build")) return <IconGitBranch size={14} />;
  if (n.includes("model") || n.includes("call") || n.includes("llm")) return <IconBrain size={14} />;
  if (n.includes("parse") || n.includes("valid")) return <IconScale size={14} />;
  if (n.includes("persona")) return <IconSparkles size={14} />;
  if (n.includes("store") || n.includes("save")) return <IconBolt size={14} />;
  return <IconTarget size={14} />;
}

export default function TraceView({ trace }: { trace: RunTrace }) {
  const [open, setOpen] = useState(false);
  if (!trace?.steps?.length) return null;
  return (
    <div className="trace">
      <button className={`trace-toggle ${open ? "open" : ""}`} onClick={() => setOpen((v) => !v)}>
        <IconBrain size={14} />
        <span>
          {open ? "Hide" : "Watch"} the agent think
          <span className="trace-meta">
            {trace.steps.length} steps · {Math.round(trace.total_ms)} ms
          </span>
        </span>
        <IconChevron size={16} className={`trace-caret ${open ? "up" : ""}`} />
      </button>
      {open && (
        <div className="trace-steps">
          {trace.steps.map((s) => (
            <div className="trace-step" key={s.index}>
              <div className="trace-rail">
                <span className="trace-dot">{stepIcon(s.name)}</span>
              </div>
              <div className="trace-content">
                <div className="trace-name">{s.name}</div>
                <div className="trace-detail">{s.detail}</div>
              </div>
              <div className="trace-ms">{Math.round(s.duration_ms)} ms</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
