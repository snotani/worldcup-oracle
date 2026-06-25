"use client";

import { useEffect, useState } from "react";
import type { Dashboard } from "@/lib/types";
import ScoreboardView from "@/components/Scoreboard";
import LeaderboardView from "@/components/Leaderboard";
import CardsView from "@/components/Cards";
import { Kpi } from "@/components/primitives";
import { ModelLogo } from "@/components/ModelLogo";
import { modelBrand } from "@/lib/brands";
import { pct } from "@/lib/format";
import {
  IconActivity,
  IconBrain,
  IconSparkles,
  IconTarget,
  IconTrophy,
} from "@/components/icons";

type TabId = "scoreboard" | "battle" | "personas";

const TABS: {
  id: TabId;
  tag: string;
  label: string;
  icon: React.ReactNode;
  note: string;
}[] = [
  {
    id: "scoreboard",
    tag: "Angle A",
    label: "Beat the bookies",
    icon: <IconTarget size={16} />,
    note: "How accurate is the agent? Backtested over finished matches against a coin flip, a home-advantage prior, and a recent-form model.",
  },
  {
    id: "battle",
    tag: "Angle B",
    label: "Model battle",
    icon: <IconTrophy size={16} />,
    note: "The exact same agent spec, run on GPT, Claude, Gemini, Grok and Composer. Who predicts the World Cup best?",
  },
  {
    id: "personas",
    tag: "Angle C",
    label: "The persona",
    icon: <IconSparkles size={16} />,
    note: "Identical predictions, wrapped in a character voice. Same numbers, more mouth — built to be screenshot-shareable.",
  },
];

// The dashboard reads a static JSON payload produced by `oracle export`
// (or swap the URL for the FastAPI /api/dashboard endpoint for live data).
const DATA_URL = "/data/dashboard.json";

export default function Home() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<TabId>("scoreboard");

  useEffect(() => {
    fetch(DATA_URL)
      .then((r) => {
        if (!r.ok) throw new Error(`Failed to load ${DATA_URL} (${r.status})`);
        return r.json();
      })
      .then(setData)
      .catch((e) => setError(String(e)));
  }, []);

  const activeTab = TABS.find((t) => t.id === tab)!;
  const s = data?.summary;

  return (
    <div className="page">
      <header className="appbar">
        <div className="appbar-inner">
          <div className="brand">
            <span className="brand-mark">
              <IconBrain size={20} />
            </span>
            <div>
              <div className="brand-title">
                The <span className="glow">Oracle</span>
              </div>
              <div className="brand-sub">FIFA World Cup 2026 · AI prediction agent</div>
            </div>
          </div>
          <div className="appbar-right">
            <span className={`live ${data?.mock ? "live-demo" : ""}`}>
              <span className="live-dot" />
              {data?.mock ? "DEMO DATA" : "LIVE"}
            </span>
            {data && (
              <span className="muted small">
                updated {new Date(data.generated_at).toLocaleString()}
              </span>
            )}
          </div>
        </div>
      </header>

      <main className="container">
        {/* Hero */}
        <section className="hero">
          <div className="hero-copy">
            <div className="hero-eyebrow">PROBLEM → SPEC → BUILD → EVALS → RESULTS</div>
            <h1 className="hero-title">
              I built an AI agent that predicts the <span className="glow">World Cup</span>.
            </h1>
            <p className="hero-lede">
              One agent, three stories: can it beat the bookies, which model is sharpest, and what
              happens when you give it a personality? Every prediction below is real, traceable, and
              graded.
            </p>
          </div>
          {s && (
            <div className="hero-kpis">
              <Kpi
                icon={<IconTarget size={18} />}
                label="Agent accuracy"
                value={pct(s.headline_accuracy)}
                sub={`over ${s.n_scored} finished matches`}
                accent="var(--accent)"
              />
              <Kpi
                icon={<IconActivity size={18} />}
                label="Edge vs coin flip"
                value={`${s.edge_vs_coin >= 0 ? "+" : ""}${Math.round(s.edge_vs_coin * 100)} pts`}
                sub={`coin flip: ${pct(s.coin_flip_accuracy)}`}
                accent="var(--accent-2)"
              />
              <Kpi
                icon={<IconTrophy size={18} />}
                label="Top model"
                value={
                  s.best_model ? (
                    <span className="kpi-model">
                      <span
                        className="kpi-model-logo"
                        style={{ color: modelBrand(s.best_model.name).color }}
                      >
                        <ModelLogo name={s.best_model.name} size={20} />
                      </span>
                      {modelBrand(s.best_model.name).label}
                    </span>
                  ) : (
                    "--"
                  )
                }
                sub={s.best_model ? `${pct(s.best_model.accuracy)} accuracy` : ""}
                accent="var(--gold)"
              />
              <Kpi
                icon={<IconBrain size={18} />}
                label="Predictions made"
                value={s.total_predictions}
                sub={`${s.n_models} models · ${s.n_upcoming} upcoming`}
                accent="#c08bff"
              />
            </div>
          )}
        </section>

        {/* Tabs */}
        <nav className="tabs">
          {TABS.map((t) => (
            <button
              key={t.id}
              className={`tab ${tab === t.id ? "active" : ""}`}
              onClick={() => setTab(t.id)}
            >
              <span className="tab-icon">{t.icon}</span>
              <span className="tab-text">
                <span className="tab-tag">{t.tag}</span>
                <span className="tab-label">{t.label}</span>
              </span>
            </button>
          ))}
        </nav>

        <p className="angle-note">{activeTab.note}</p>

        {error && (
          <div className="card">
            <h3>Couldn&apos;t load data</h3>
            <p className="muted">{error}</p>
            <p className="muted small">
              Generate it first: <code>cd backend &amp;&amp; oracle export</code>
            </p>
          </div>
        )}

        {!data && !error && (
          <div className="loading">
            <span className="spinner" /> Consulting the Oracle…
          </div>
        )}

        {data && (
          <>
            {tab === "scoreboard" && <ScoreboardView data={data.scoreboard} />}
            {tab === "battle" && (
              <LeaderboardView
                leaderboard={data.leaderboard}
                matches={data.battle_matches}
                insights={data.battle_insights}
              />
            )}
            {tab === "personas" && <CardsView cards={data.cards} />}
          </>
        )}

        <footer className="footer">
          Built with the Cursor Agent SDK · live data from ESPN · {data?.competition ?? "FIFA World Cup 2026"}
        </footer>
      </main>
    </div>
  );
}
