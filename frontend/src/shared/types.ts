export type Severity = "low" | "medium" | "high";
export type IncidentStatus = "new" | "investigating" | "confirmed" | "rejected";

export interface Incident {
  id: number;
  event_id: number;
  title: string;
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

export interface EventCreate {
  source: string;
  user_id: string;
  raw_text: string;
  url?: string | null;
}
