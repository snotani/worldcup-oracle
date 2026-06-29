// Types mirroring the payload produced by the backend `oracle export` / FastAPI /api/dashboard.

export type Probs = { home: number; draw: number; away: number };
export type Outcome = "home" | "draw" | "away";
export type Side = "home" | "away";

export interface TeamMeta {
  name: string;
  abbr: string | null;
  logo: string | null;
  color: string | null;
  rating?: number;
  form?: string[];
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

export interface AgentFeature {
  key: string;
  label: string;
  detail: string;
}

export interface BracketMatch {
  id: number;
  round: string; // R32 | R16 | QF | SF | F
  round_name: string;
  venue: string | null;
  home: TeamMeta;
  away: TeamMeta;
  home_adv: number;
  away_adv: number;
  winner: Side;
  winner_name: string;
  loser_name: string;
  score: string;
  confidence: number;
  is_result: boolean;
  is_upset: boolean;
  feeds: [number, string] | null;
  rationale: string;
}

export interface RoundGroup {
  code: string;
  name: string;
  matches: BracketMatch[];
}

export interface BracketSim {
  model_id: string;
  model_name: string;
  champion: TeamMeta;
  runner_up: TeamMeta;
  finalists: TeamMeta[];
  final: BracketMatch;
  rounds: RoundGroup[];
  path: BracketMatch[];
  upsets: BracketMatch[];
  trace: RunTrace;
}

export interface ContestedMatch {
  id: number;
  home: TeamMeta;
  away: TeamMeta;
  tally: Record<string, number>;
  split: string;
}

export interface Consensus {
  champion_votes: Record<string, number>;
  finalist_votes: Record<string, number>;
  consensus_champion: { name: string; votes: number; of: number; meta: TeamMeta };
  distinct_champions: number;
  r32_agreement: number;
  contested: ContestedMatch[];
}

export interface Dashboard {
  generated_at: string;
  mock: boolean;
  competition: string;
  agent_features: AgentFeature[];
  simulation: BracketSim;
  model_brackets: BracketSim[];
  consensus: Consensus;
  models: { name: string; model_id: string }[];
}
