"use client";

import { useState } from "react";
import type { BattleInsights, BattleMatch, InsightCall, LeaderboardRow } from "@/lib/types";
import TraceView from "./TraceView";
import { ModelBadge, ProbBar, TeamCrest } from "./primitives";
import { ModelLogo } from "./ModelLogo";
import { kickoff, outcomeLabel, pct, prettyStage, readableOn } from "@/lib/format";
import { modelBrand } from "@/lib/brands";
import { IconBolt, IconFlame, IconPin, IconTarget, IconTrophy, IconUsers } from "./icons";

const MEDALS = ["#ffce4f", "#c7d0dd", "#cd8e54"];

/* ---------- Hot takes strip ---------- */

function CallChip({ call }: { call: InsightCall }) {
  const b = modelBrand(call.model);
  return (
    <span className="hot-call">
      <span className="hot-logo" style={{ background: b.color, color: readableOn(b.color) }}>
        <ModelLogo name={call.model} size={13} />
      </span>
      <span>
        <strong>{b.label}</strong> · {call.pick_label}{" "}
        <span className="hot-conf">{pct(call.confidence)}</span>
      </span>
    </span>
  );
}

function HotTakes({ insights }: { insights: BattleInsights }) {
  const { biggest_debate, boldest_call, upset_alert, maverick_model } = insights;
  const mav = maverick_model ? modelBrand(maverick_model.name) : null;
  return (
    <div className="hot-grid">
      {biggest_debate && (
        <div className="hot-card hot-debate">
          <div className="hot-head">
            <IconUsers size={15} /> Biggest debate
          </div>
          <div className="hot-main">{biggest_debate.label}</div>
          <div className="hot-sub">
            <span className="split-badge split-hot">{biggest_debate.split_label}</span>
            <DebateMeter value={biggest_debate.disagreement} />
          </div>
        </div>
      )}
      {boldest_call && (
        <div className="hot-card">
          <div className="hot-head">
            <IconBolt size={15} /> Boldest call
          </div>
          <div className="hot-main hot-main-sm">{boldest_call.label}</div>
          <div className="hot-sub">
            <CallChip call={boldest_call} />
          </div>
        </div>
      )}
      {upset_alert && (
        <div className="hot-card hot-upset">
          <div className="hot-head">
            <IconFlame size={15} /> Upset alert
          </div>
          <div className="hot-main hot-main-sm">{upset_alert.label}</div>
          <div className="hot-sub">
            <CallChip call={upset_alert} />
          </div>
        </div>
      )}
      {mav && maverick_model && (
        <div className="hot-card">
          <div className="hot-head">
            <IconTarget size={15} /> Maverick model
          </div>
          <div className="hot-main hot-mav">
            <span className="hot-logo" style={{ background: mav.color, color: readableOn(mav.color) }}>
              <ModelLogo name={maverick_model.name} size={15} />
            </span>
            {mav.label}
          </div>
          <div className="hot-sub muted small">
            breaks from the room {maverick_model.contrarian}×
          </div>
        </div>
      )}
    </div>
  );
}

function DebateMeter({ value }: { value: number }) {
  const v = Math.min(Math.max(value, 0), 1);
  const hot = v >= 0.5;
  return (
    <span className="debate-meter" title={`Disagreement ${Math.round(v * 100)}%`}>
      <span className="debate-track">
        <span
          className="debate-fill"
          style={{ width: `${Math.max(v * 100, 6)}%`, background: hot ? "#ff7a45" : "#4f8cff" }}
        />
      </span>
    </span>
  );
}

/* ---------- Podium ---------- */

function Podium({ rows }: { rows: LeaderboardRow[] }) {
  const top = rows.slice(0, 3);
  const order = [1, 0, 2];
  return (
    <div className="podium">
      {order
        .filter((i) => top[i])
        .map((i) => {
          const row = top[i];
          const b = modelBrand(row.name);
          return (
            <div className={`podium-col podium-${i + 1}`} key={row.model_id}>
              <div className="podium-medal" style={{ color: MEDALS[i] }}>
                <IconTrophy size={i === 0 ? 22 : 18} />
              </div>
              <div
                className="podium-avatar"
                style={{ background: b.color, color: readableOn(b.color) }}
              >
                <ModelLogo name={row.name} size={i === 0 ? 30 : 26} />
              </div>
              <div className="podium-name">{b.label}</div>
              <div className="podium-acc" style={{ color: MEDALS[i] }}>
                {pct(row.accuracy)}
              </div>
              <div className="muted small">
                {row.correct}/{row.matches} correct
              </div>
              <div className="podium-stand" style={{ height: i === 0 ? 64 : i === 1 ? 46 : 34 }}>
                #{i + 1}
              </div>
            </div>
          );
        })}
    </div>
  );
}

/* ---------- Battle match card ---------- */

function BattleCard({ m }: { m: BattleMatch }) {
  const [openTrace, setOpenTrace] = useState<string | null>(null);
  const unanimous = (m.distinct_picks ?? 1) <= 1;
  return (
    <div className={`card battle-card ${!unanimous ? "battle-split" : ""}`}>
      <div className="battle-head">
        <div className="battle-toprow">
          {m.split_label && (
            <span className={`split-badge ${unanimous ? "split-calm" : "split-hot"}`}>
              {!unanimous && <IconFlame size={12} />}
              {m.split_label}
            </span>
          )}
          {typeof m.disagreement === "number" && <DebateMeter value={m.disagreement} />}
        </div>
        <div className="vs">
          <span className="vs-side">
            <TeamCrest team={m.home} name={m.home_team} size={40} />
            <span className="vs-name">{m.home_team}</span>
          </span>
          <span className="vs-mid">VS</span>
          <span className="vs-side vs-side-right">
            <span className="vs-name">{m.away_team}</span>
            <TeamCrest team={m.away} name={m.away_team} size={40} />
          </span>
        </div>
        <div className="battle-meta muted small">
          <span>{prettyStage(m.stage)}</span>
          <span>· {kickoff(m.kickoff_utc)}</span>
          {m.venue && (
            <span className="battle-venue">
              <IconPin size={12} /> {m.venue}
            </span>
          )}
        </div>
        {m.consensus && (
          <div className={`consensus ${unanimous ? "" : "consensus-split"}`}>
            <IconUsers size={13} />
            <span>
              {unanimous
                ? `All ${m.consensus.of} models agree: `
                : `${m.consensus.votes}/${m.consensus.of} lean `}
              <strong>{outcomeLabel(m.consensus.pick, m.home_team, m.away_team)}</strong>
            </span>
          </div>
        )}
      </div>

      <div className="picks">
        {m.picks.map((p) => (
          <div
            className={`pickrow ${p.against_consensus ? "pickrow-rogue" : ""}`}
            key={p.model_id}
          >
            <div className="pickrow-model">
              <ModelBadge name={p.name} size="sm" />
              {p.is_maverick && !p.against_consensus && (
                <span className="mini-tag" title="Furthest from the crowd">
                  maverick
                </span>
              )}
            </div>
            <div className="pickrow-bar">
              <ProbBar probs={p.probs} pick={p.pick} height={9} />
            </div>
            <div className="pickrow-pick">
              <span
                className={`pickchip ${p.against_consensus ? "pickchip-rogue" : ""}`}
                title={`${pct(p.confidence)} confidence`}
              >
                {p.against_consensus && <IconFlame size={11} />}
                {outcomeLabel(p.pick, m.home_team, m.away_team)}
              </span>
              {p.predicted_score && <span className="muted small">{p.predicted_score}</span>}
            </div>
            <button
              className="pickrow-why"
              onClick={() => setOpenTrace((cur) => (cur === p.model_id ? null : p.model_id))}
              title="See reasoning"
            >
              <IconBolt size={14} />
            </button>
          </div>
        ))}
      </div>

      {m.picks.map(
        (p) =>
          openTrace === p.model_id && (
            <div className="why-panel" key={`why-${p.model_id}`}>
              <div className="why-head">
                <ModelBadge name={p.name} size="sm" showProvider />
              </div>
              <p className="why-text">{p.rationale}</p>
              <TraceView trace={p.trace} />
            </div>
          ),
      )}
    </div>
  );
}

// Angle B: the model battle. Standings over finished matches + each model's upcoming picks.
export default function LeaderboardView({
  leaderboard,
  matches,
  insights,
}: {
  leaderboard: LeaderboardRow[];
  matches: BattleMatch[];
  insights?: BattleInsights;
}) {
  const maxAcc = Math.max(...leaderboard.map((r) => r.accuracy), 0.01);
  const hasInsights =
    insights && (insights.biggest_debate || insights.boldest_call || insights.upset_alert);
  return (
    <div className="stack">
      {hasInsights && <HotTakes insights={insights} />}

      <div className="card">
        <div className="card-head">
          <h3>
            <IconTrophy size={16} /> The leaderboard
          </h3>
          <span className="muted small">same agent spec · different brains</span>
        </div>

        {leaderboard.length >= 3 && <Podium rows={leaderboard} />}

        <div className="standings">
          {leaderboard.map((row, i) => {
            const b = modelBrand(row.name);
            return (
              <div className={`standrow ${i === 0 ? "standrow-lead" : ""}`} key={row.model_id}>
                <div className="stand-rank">{i + 1}</div>
                <div className="stand-model">
                  <ModelBadge name={row.name} modelId={row.model_id} showProvider />
                </div>
                <div className="stand-bar">
                  <div className="stand-track">
                    <div
                      className="stand-fill"
                      style={{
                        width: `${(row.accuracy / maxAcc) * 100}%`,
                        background: b.color,
                      }}
                    />
                  </div>
                </div>
                <div className="stand-acc">{pct(row.accuracy)}</div>
                <div className="stand-rec muted small">
                  {row.correct}/{row.matches}
                </div>
                <div className="stand-brier muted small">Brier {row.brier.toFixed(3)}</div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="section-title">
        <h3>The debates — who picks what</h3>
        <span className="muted small">
          {matches.length} fixtures · sorted by disagreement
        </span>
      </div>
      <div className="grid cols-2">
        {matches.map((m) => (
          <BattleCard key={m.match_id} m={m} />
        ))}
      </div>
    </div>
  );
}
