import type { MetricSummary, Scoreboard } from "@/lib/types";
import { outcomeLabel, pct, pct1, shortDate } from "@/lib/format";
import { ProbBar, TeamCrest } from "./primitives";
import { IconCheck, IconTarget, IconX } from "./icons";

const PREDICTOR_LABELS: Record<string, string> = {
  coin_flip: "Coin flip",
  home_advantage: "Home advantage",
  form_model: "Recent-form model",
};

function predictorLabel(name: string): string {
  if (name.startsWith("agent:")) return "The Oracle (AI agent)";
  return PREDICTOR_LABELS[name] ?? name;
}

// Angle A: accuracy + calibration of the agent vs baselines over finished matches.
export default function ScoreboardView({ data }: { data: Scoreboard }) {
  const summaries: MetricSummary[] = [...data.summaries].sort(
    (a, b) => b.accuracy - a.accuracy || a.brier - b.brier,
  );
  const maxAcc = Math.max(...summaries.map((s) => s.accuracy), 0.01);
  const agent = summaries.find((s) => s.name.startsWith("agent:"));
  const hits = data.rows.filter((r) => r.agent_correct).length;

  return (
    <div className="stack">
      <div className="grid cols-7-5">
        {/* Predictor comparison */}
        <div className="card">
          <div className="card-head">
            <h3>
              <IconTarget size={16} /> Accuracy vs the baselines
            </h3>
            <span className="muted small">{data.n_matches} finished matches</span>
          </div>

          <div className="bars">
            {summaries.map((s) => {
              const isAgent = s.name.startsWith("agent:");
              return (
                <div className={`barrow ${isAgent ? "barrow-agent" : ""}`} key={s.name}>
                  <div className="barrow-label">
                    <span className="barrow-name">{predictorLabel(s.name)}</span>
                    {isAgent && <span className="tag tag-gold">AGENT</span>}
                  </div>
                  <div className="barrow-track">
                    <div
                      className={`barrow-fill ${isAgent ? "fill-agent" : ""}`}
                      style={{ width: `${(s.accuracy / maxAcc) * 100}%` }}
                    />
                    <span className="barrow-val">{pct1(s.accuracy)}</span>
                  </div>
                  <div className="barrow-sub muted small">
                    Brier {s.brier.toFixed(3)} · Log loss {s.log_loss.toFixed(3)}
                  </div>
                </div>
              );
            })}
          </div>
          <p className="muted small footnote">
            Lower Brier &amp; log loss = better-calibrated probabilities. The agent has to beat a
            coin flip, a home-advantage prior, and a recent-form model to earn its keep.
          </p>
        </div>

        {/* Headline calibration / record */}
        <div className="card card-stat">
          <div className="card-head">
            <h3>The Oracle&apos;s record</h3>
          </div>
          <div className="big-stat">
            <div className="big-stat-num">{agent ? pct(agent.accuracy) : "--"}</div>
            <div className="big-stat-label">correct outcomes</div>
          </div>
          <div className="donut-legend" style={{ justifyContent: "center", marginBottom: 14 }}>
            <span className="record-chip record-win">
              <IconCheck size={13} /> {hits} hits
            </span>
            <span className="record-chip record-lose">
              <IconX size={13} /> {data.rows.length - hits} misses
            </span>
          </div>
          {agent && (
            <div className="metric-grid">
              <div className="metric-cell">
                <div className="metric-cell-num">{agent.brier.toFixed(3)}</div>
                <div className="metric-cell-label">Brier score</div>
              </div>
              <div className="metric-cell">
                <div className="metric-cell-num">{agent.log_loss.toFixed(3)}</div>
                <div className="metric-cell-label">Log loss</div>
              </div>
            </div>
          )}
          {agent && agent.calibration?.length > 0 && (
            <div className="calib">
              <div className="calib-title muted small">Calibration — confidence vs reality</div>
              {agent.calibration
                .filter((b) => b.count > 0)
                .map((b, i) => (
                  <div className="calib-row" key={i}>
                    <span className="calib-band">
                      {Math.round(b.lower * 100)}–{Math.round(b.upper * 100)}%
                    </span>
                    <div className="calib-track">
                      <div className="calib-conf" style={{ width: `${b.avg_confidence * 100}%` }} />
                      <div className="calib-real" style={{ width: `${b.accuracy * 100}%` }} />
                    </div>
                    <span className="muted small">n={b.count}</span>
                  </div>
                ))}
              <div className="calib-key muted small">
                <span className="dot dot-conf" /> said · <span className="dot dot-real" /> actual
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Match-by-match feed */}
      <div className="card">
        <div className="card-head">
          <h3>Match-by-match</h3>
          <span className="muted small">every call the agent made, graded</span>
        </div>
        <div className="match-feed">
          {data.rows.map((r) => (
            <div className={`feed-row ${r.agent_correct ? "feed-hit" : "feed-miss"}`} key={r.match_id}>
              <div className="feed-date muted small">{shortDate(r.kickoff_utc)}</div>
              <div className="feed-match">
                <span className="feed-team feed-team-home">
                  <span className="feed-team-name">{r.home_team}</span>
                  <TeamCrest team={r.home} name={r.home_team} size={26} />
                </span>
                <span className="feed-score">{r.actual_score}</span>
                <span className="feed-team feed-team-away">
                  <TeamCrest team={r.away} name={r.away_team} size={26} />
                  <span className="feed-team-name">{r.away_team}</span>
                </span>
              </div>
              <div className="feed-pick">
                <span className="muted small">picked</span>{" "}
                <strong>{outcomeLabel(r.agent_pick, r.home_team, r.away_team)}</strong>
                <div className="feed-prob">
                  <ProbBar probs={r.agent_probs} pick={r.agent_pick} height={6} />
                </div>
              </div>
              <div className={`feed-result ${r.agent_correct ? "win" : "lose"}`}>
                {r.agent_correct ? <IconCheck size={16} /> : <IconX size={16} />}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
