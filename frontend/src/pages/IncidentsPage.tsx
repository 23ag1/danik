import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../shared/api";
import type { Incident, IncidentStatus, Severity } from "../shared/types";
import { Badge } from "../shared/ui/Badge";

export function IncidentsPage() {
  const [items, setItems] = useState<Incident[]>([]);
  const [status, setStatus] = useState<IncidentStatus | "">("");
  const [severity, setSeverity] = useState<Severity | "">("");
  const [q, setQ] = useState("");

  useEffect(() => {
    api.getIncidents().then(setItems).catch(console.error);
  }, []);

  const filtered = useMemo(() => {
    return items.filter((i) => {
      if (status && i.status !== status) return false;
      if (severity && i.severity !== severity) return false;
      if (q && !i.title.toLowerCase().includes(q.toLowerCase())) return false;
      return true;
    });
  }, [items, status, severity, q]);

  return (
    <section className="space-y-6">
      <header>
        <h2 className="text-2xl font-semibold tracking-tight">Инциденты</h2>
      </header>

      <section className="flex flex-wrap gap-3">
        <input
          className="rounded-lg border border-zinc-300 px-3 py-2 text-sm"
          placeholder="Поиск по названию"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <select
          className="rounded-lg border border-zinc-300 px-3 py-2 text-sm"
          value={status}
          onChange={(e) => setStatus(e.target.value as IncidentStatus | "")}
        >
          <option value="">Все статусы</option>
          <option value="new">new</option>
          <option value="investigating">investigating</option>
          <option value="confirmed">confirmed</option>
          <option value="rejected">rejected</option>
        </select>
        <select
          className="rounded-lg border border-zinc-300 px-3 py-2 text-sm"
          value={severity}
          onChange={(e) => setSeverity(e.target.value as Severity | "")}
        >
          <option value="">Все severity</option>
          <option value="low">low</option>
          <option value="medium">medium</option>
          <option value="high">high</option>
        </select>
      </section>

      <table className="w-full overflow-hidden rounded-xl border border-zinc-200 bg-white text-left text-sm">
        <thead className="border-b border-zinc-200 bg-zinc-50 text-xs uppercase text-zinc-500">
          <tr>
            <th className="px-4 py-3">ID</th>
            <th className="px-4 py-3">Название</th>
            <th className="px-4 py-3">Risk</th>
            <th className="px-4 py-3">Severity</th>
            <th className="px-4 py-3">Status</th>
          </tr>
        </thead>
        <tbody>
          {filtered.map((inc) => (
            <tr key={inc.id} className="border-t border-zinc-100 hover:bg-zinc-50">
              <td className="px-4 py-3 font-mono">{inc.id}</td>
              <td className="px-4 py-3">
                <Link className="font-medium hover:text-teal-700" to={`/incidents/${inc.id}`}>
                  {inc.title}
                </Link>
              </td>
              <td className="px-4 py-3 font-mono">{inc.risk_score.toFixed(2)}</td>
              <td className="px-4 py-3">
                <Badge label={inc.severity} />
              </td>
              <td className="px-4 py-3">
                <Badge label={inc.status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {filtered.length === 0 && (
        <p className="text-center text-sm text-zinc-500">Ничего не найдено</p>
      )}
    </section>
  );
}
