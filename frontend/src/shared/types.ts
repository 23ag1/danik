export type Severity = "low" | "medium" | "high";
export type IncidentStatus = "new" | "investigating" | "confirmed" | "rejected";

export interface Incident {
  id: number;
  event_id: number;
  title: string;
  raw_text: string;
  risk_score: number;
  severity: Severity;
  rule_score: number;
  ml_score: number;
  graph_score: number;
  anomaly_score: number;
  rule_flags: string[];
  status: IncidentStatus;
  analyst_comment: string | null;
  created_at: string;
  updated_at: string;
}

export interface Event {
  id: number;
  source: string;
  author_hash: string;
  raw_text: string;
  url: string | null;
  created_at: string;
}

export interface MonitoredSource {
  id: number;
  name: string;
  url: string;
  source_type: "rss" | "telegram";
  enabled: boolean;
  interval_sec: number;
  last_fetched_at: string | null;
  created_at: string;
}

export interface EventCreate {
  source: string;
  user_id: string;
  raw_text: string;
  url?: string | null;
}
