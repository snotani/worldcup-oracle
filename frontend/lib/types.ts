// Types mirroring the payload produced by the backend `oracle export` / FastAPI /api/dashboard.

export type Probs = { home: number; draw: number; away: number };

export type Outcome = "home" | "draw" | "away";

export interface TeamMeta {
  name: string;
  abbr: string | null;
  logo: string | null;
  color: string | null;
}

export interface TraceStep {
  index: number;
  name: string;
  detail: string;
  data: Record<string, unknown>;
  started_at: string;
  duration_ms: number;
}

export interface RunTrace {
  trace_id: string;
  label: string;
  model_id: string | null;
  started_at: string;
  total_ms: number;
  steps: TraceStep[];
}

export interface CalibrationBin {
  lower: number;
  upper: number;
  count: number;
  avg_confidence: number;
  accuracy: number;
}

export interface MetricSummary {
  name: string;
  n: number;
  accuracy: number;
  brier: number;
  log_loss: number;
  calibration: CalibrationBin[];
}

export interface ScoreboardRow {
  match_id: number;
  home_team: string;
  away_team: string;
  home?: TeamMeta;
  away?: TeamMeta;
  kickoff_utc?: string | null;
  stage?: string | null;
  venue?: string | null;
  actual_outcome: Outcome;
  actual_score: string;
  agent_pick: Outcome;
  agent_correct: boolean;
  agent_probs: Probs;
  agent_confidence?: number;
}

export interface Scoreboard {
  model_id: string;
  n_matches: number;
  summaries: MetricSummary[];
  rows: ScoreboardRow[];
}

export interface LeaderboardRow {
  name: string;
  model_id: string;
  matches: number;
  correct: number;
  accuracy: number;
  brier: number;
  log_loss: number;
}

export interface BattlePick {
  name: string;
  model_id: string;
  pick: Outcome;
  probs: Probs;
  predicted_score: string | null;
  confidence: number;
  rationale: string;
  trace: RunTrace;
  delta_vs_crowd?: number;
  against_consensus?: boolean;
  is_maverick?: boolean;
}

export interface BattleMatch {
  match_id: number;
  home_team: string;
  away_team: string;
  home?: TeamMeta;
  away?: TeamMeta;
  kickoff_utc: string | null;
  stage: string | null;
  venue?: string | null;
  consensus?: { pick: Outcome; votes: number; of: number };
  vote_split?: Record<Outcome, number>;
  distinct_picks?: number;
  split_label?: string;
  prob_spread?: number;
  score_spread?: number;
  disagreement?: number;
  maverick?: { name: string; model_id: string; pick: Outcome; delta: number };
  picks: BattlePick[];
}

export interface InsightCall {
  match_id: number;
  label: string;
  model: string;
  model_id: string;
  pick: Outcome;
  pick_label: string;
  confidence: number;
  against_consensus?: boolean;
}

export interface BattleInsights {
  biggest_debate?: {
    match_id: number;
    label: string;
    home?: TeamMeta;
    away?: TeamMeta;
    split_label: string;
    disagreement: number;
  };
  boldest_call?: InsightCall;
  upset_alert?: InsightCall | null;
  maverick_model?: { name: string; model_id: string; contrarian: number; delta: number } | null;
}

export interface PersonaCard {
  match_id: number;
  home_team: string;
  away_team: string;
  home?: TeamMeta;
  away?: TeamMeta;
  kickoff_utc: string | null;
  stage?: string | null;
  venue?: string | null;
  persona: string;
  persona_name: string;
  persona_message: string | null;
  pick: Outcome;
  probs: Probs;
  predicted_score: string | null;
  confidence?: number;
  rationale?: string;
  model_id?: string;
  trace: RunTrace;
}

export interface DashboardSummary {
  headline_accuracy: number;
  headline_brier: number;
  coin_flip_accuracy: number;
  edge_vs_coin: number;
  n_scored: number;
  n_upcoming: number;
  n_models: number;
  total_predictions: number;
  best_model: LeaderboardRow | null;
  default_model: string;
}

export interface Dashboard {
  generated_at: string;
  mock: boolean;
  competition: string;
  summary?: DashboardSummary;
  scoreboard: Scoreboard;
  leaderboard: LeaderboardRow[];
  battle_insights?: BattleInsights;
  battle_matches: BattleMatch[];
  cards: PersonaCard[];
  personas: { id: string; name: string; tagline: string }[];
}
