import type { Event, EventCreate, Incident, IncidentStatus, MonitoredSource } from "./types";

const BASE = "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string }>("/health"),
  getIncidents: () => request<Incident[]>("/incidents"),
  patchIncident: (id: number, status: IncidentStatus, analyst_comment?: string) =>
    request<Incident>(`/incidents/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status, analyst_comment }),
    }),
  getEvents: () => request<Event[]>("/events"),
  getSources: () => request<MonitoredSource[]>("/sources"),
  createSource: (body: { name: string; url: string; interval_sec?: number }) =>
    request<MonitoredSource>("/sources", { method: "POST", body: JSON.stringify(body) }),
  patchSource: (id: number, body: { enabled?: boolean; interval_sec?: number }) =>
    request<MonitoredSource>(`/sources/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteSource: (id: number) => request<void>(`/sources/${id}`, { method: "DELETE" }),
  fetchSource: (id: number) => request<{ ingested: number }>(`/sources/${id}/fetch`, { method: "POST" }),
  createEvent: (body: EventCreate) =>
    request<{ id: number; incident_id: number | null; risk_score: number }>("/events", {
      method: "POST",
      body: JSON.stringify(body),
    }),
};
