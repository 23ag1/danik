import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../shared/api";
import type { Incident } from "../shared/types";
import { Badge } from "../shared/ui/Badge";

export function DashboardPage() {
  const [items, setItems] = useState<Incident[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .getIncidents()
      .then(setItems)
      .catch((e) => setError(e instanceof Error ? e.message : "Ошибка"));
  }, []);

  const high = items.filter((i) => i.severity === "high").length;
  const open = items.filter((i) => i.status === "new").length;
  const avgRisk =
    items.length > 0
      ? items.reduce((s, i) => s + i.risk_score, 0) / items.length
      : 0;

  return (
    <section className="space-y-8">
      <header>
        <h2 className="text-2xl font-semibold tracking-tight">Сводка</h2>
        <p className="mt-1 text-sm text-zinc-500">Мониторинг подозрительных сообщений</p>
      </header>

      {error && <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}

      <ul className="grid gap-4 sm:grid-cols-3">
        <li className="rounded-xl border border-zinc-200 bg-white p-5">
          <p className="text-sm text-zinc-500">Инцидентов</p>
          <p className="mt-1 font-mono text-3xl font-medium">{items.length}</p>
        </li>
        <li className="rounded-xl border border-zinc-200 bg-white p-5">
          <p className="text-sm text-zinc-500">Новых</p>
          <p className="mt-1 font-mono text-3xl font-medium">{open}</p>
        </li>
        <li className="rounded-xl border border-zinc-200 bg-white p-5">
          <p className="text-sm text-zinc-500">High / средний risk</p>
          <p className="mt-1 font-mono text-3xl font-medium">
            {high} / {avgRisk.toFixed(2)}
          </p>
        </li>
      </ul>

      <section>
        <h3 className="mb-3 text-sm font-medium uppercase tracking-wide text-zinc-500">
          Последние
        </h3>
        {items.length === 0 ? (
          <p className="text-sm text-zinc-500">
            Пока пусто.{" "}
            <Link className="text-teal-700 underline" to="/ingest">
              Загрузить события
            </Link>
          </p>
        ) : (
          <ul className="divide-y divide-zinc-200 rounded-xl border border-zinc-200 bg-white">
            {items.slice(0, 8).map((inc) => (
              <li key={inc.id} className="flex items-center justify-between gap-4 px-4 py-3">
                <Link className="font-medium hover:text-teal-700" to={`/incidents/${inc.id}`}>
                  {inc.title}
                </Link>
                <span className="flex gap-2">
                  <Badge label={inc.severity} />
                  <span className="font-mono text-sm text-zinc-600">{inc.risk_score.toFixed(2)}</span>
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </section>
  );
}
