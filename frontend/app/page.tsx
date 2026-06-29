"use client";

import { useEffect, useState } from "react";
import type { Dashboard } from "@/lib/types";
import SimulationTab from "@/components/SimulationTab";
import ModelBattleTab from "@/components/ModelBattleTab";
import { Kpi, TeamCrest } from "@/components/primitives";
import { modelBrand } from "@/lib/brands";
import { ModelLogo } from "@/components/ModelLogo";
import {
  IconBrain,
  IconGitBranch,
  IconTrophy,
  IconUsers,
  IconScale,
  IconFlame,
} from "@/components/icons";

type TabId = "simulation" | "battle";

const TABS: { id: TabId; tag: string; label: string; icon: React.ReactNode; note: string }[] = [
  {
    id: "simulation",
    tag: "Video 1",
    label: "The Oracle",
    icon: <IconBrain size={16} />,
    note: "I built an AI agent that predicts the World Cup winner. Here are the signals it uses, then a full simulation of the live bracket - every game, both sides of the draw, all the way to who lifts the trophy.",
  },
  {
    id: "battle",
    tag: "Video 2",
    label: "Model Battle",
    icon: <IconTrophy size={16} />,
    note: "I made the top 5 AI models - Claude, ChatGPT, Gemini, Grok and Composer - fight to predict the whole bracket. Same data, same rules: who do they crown, and where do they completely disagree?",
  },
];

const DATA_URL = "/data/dashboard.json";

export default function Home() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<TabId>("simulation");

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
  const sim = data?.simulation;
  const consensus = data?.consensus;
  const cChamp = consensus?.consensus_champion;
  const cBrand = sim ? modelBrand(sim.model_name) : null;

  return (
    <div className="page">
      <header className="appbar">
        <div className="appbar-inner">
          <div className="brand">
            <span className="brand-mark">
              <IconTrophy size={20} />
            </span>
            <div>
              <div className="brand-title">
                The <span className="glow">Oracle</span>
              </div>
              <div className="brand-sub">FIFA World Cup 2026 · bracket prediction agent</div>
            </div>
          </div>
          <div className="appbar-right">
            <span className={`live ${data?.mock ? "live-demo" : ""}`}>
              <span className="live-dot" />
              {data?.mock ? "DEMO DATA" : "LIVE"}
            </span>
            {data && (
              <span className="muted small">
                updated {new Date(data.generated_at).toLocaleDateString()}
              </span>
            )}
          </div>
        </div>
      </header>

      <main className="container">
        <section className="hero">
          <div className="hero-copy">
            <div className="hero-eyebrow">
              {tab === "simulation"
                ? "ONE AGENT · WHOLE BRACKET · ONE CHAMPION"
                : "CLAUDE · CHATGPT · GEMINI · GROK · COMPOSER"}
            </div>
            <h1 className="hero-title">
              {tab === "simulation" ? (
                <>
                  I built an AI agent that predicts the{" "}
                  <span className="glow">World Cup winner</span>.
                </>
              ) : (
                <>
                  I made the top 5 AI models <span className="glow">fight</span> over the
                  bracket.
                </>
              )}
            </h1>
            <p className="hero-lede">
              {tab === "simulation"
                ? "It pulls live form, ratings and stats for every knockout team, then plays the tournament forward - resolving each tie and advancing the winner until one nation is left standing."
                : "Identical bracket, identical inputs. Each model simulates all 31 knockout games to a champion. Watch their paths and see where the smartest models flat-out disagree."}
            </p>
          </div>

          {data && tab === "simulation" && sim && (
            <div className="hero-kpis">
              <Kpi
                icon={<IconTrophy size={18} />}
                label="Predicted champion"
                value={
                  <span className="kpi-model">
                    <TeamCrest team={sim.champion} size={22} /> {sim.champion.name}
                  </span>
                }
                sub={`beat ${sim.runner_up.name} ${sim.final.score}`}
                accent="var(--gold)"
              />
              <Kpi
                icon={<IconUsers size={18} />}
                label="Finalists"
                value={sim.finalists.map((f) => f.abbr).join(" · ")}
                sub="the two left standing"
                accent="var(--accent-2)"
              />
              <Kpi
                icon={<IconFlame size={18} />}
                label="Upsets called"
                value={sim.upsets.length}
                sub="lower-rated side advancing"
                accent="var(--danger)"
              />
              <Kpi
                icon={<IconBrain size={18} />}
                label="Powered by"
                value={
                  cBrand ? (
                    <span className="kpi-model">
                      <span className="kpi-model-logo" style={{ color: cBrand.color }}>
                        <ModelLogo name={sim.model_name} size={20} />
                      </span>
                      {cBrand.label}
                    </span>
                  ) : (
                    "--"
                  )
                }
                sub={`${data.agent_features.length} signals / match`}
                accent="var(--purple)"
              />
            </div>
          )}

          {data && tab === "battle" && consensus && cChamp && (
            <div className="hero-kpis">
              <Kpi
                icon={<IconTrophy size={18} />}
                label="Consensus champion"
                value={
                  <span className="kpi-model">
                    <TeamCrest team={cChamp.meta} size={22} /> {cChamp.name}
                  </span>
                }
                sub={`${cChamp.votes} of ${cChamp.of} models agree`}
                accent="var(--gold)"
              />
              <Kpi
                icon={<IconUsers size={18} />}
                label="Distinct champions"
                value={consensus.distinct_champions}
                sub="different winners picked"
                accent="var(--accent-2)"
              />
              <Kpi
                icon={<IconScale size={18} />}
                label="R32 agreement"
                value={`${Math.round(consensus.r32_agreement * 100)}%`}
                sub="same first-round calls"
                accent="var(--accent)"
              />
              <Kpi
                icon={<IconGitBranch size={18} />}
                label="Models"
                value={data.model_brackets.length}
                sub="one bracket each"
                accent="var(--purple)"
              />
            </div>
          )}
        </section>

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
              Generate it first: <code>cd backend &amp;&amp; oracle export --mock</code>
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
            {tab === "simulation" && (
              <SimulationTab sim={data.simulation} features={data.agent_features} />
            )}
            {tab === "battle" && (
              <ModelBattleTab brackets={data.model_brackets} consensus={data.consensus} />
            )}
          </>
        )}

        <footer className="footer">
          Built with the Cursor Agent SDK · live data from ESPN · {data?.competition ?? "FIFA World Cup 2026"}
        </footer>
      </main>
    </div>
  );
}
