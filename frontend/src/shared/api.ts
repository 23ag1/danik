import type { Event, EventCreate, Incident, IncidentStatus } from "./types";

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
  createEvent: (body: EventCreate) =>
    request<{ id: number; incident_id: number | null; risk_score: number }>("/events", {
      method: "POST",
      body: JSON.stringify(body),
    }),
};
