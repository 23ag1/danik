import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../shared/api";
import type { Incident, IncidentStatus } from "../shared/types";
import { Badge } from "../shared/ui/Badge";

function ScoreRow({ label, value }: { label: string; value: number }) {
  return (
    <li className="space-y-1">
      <p className="flex justify-between text-sm">
        <span className="text-zinc-600">{label}</span>
        <span className="font-mono">{value.toFixed(2)}</span>
      </p>
      <progress className="h-2 w-full accent-teal-600" value={value} max={1} />
    </li>
  );
}

export function IncidentDetailPage() {
  const { id } = useParams();
  const [inc, setInc] = useState<Incident | null>(null);
  const [comment, setComment] = useState("");
  const [msg, setMsg] = useState("");

  useEffect(() => {
    api
      .getIncidents()
      .then((list) => {
        const found = list.find((i) => i.id === Number(id)) ?? null;
        setInc(found);
        setComment(found?.analyst_comment ?? "");
      })
      .catch(console.error);
  }, [id]);

  async function setStatus(status: IncidentStatus) {
    if (!inc) return;
    try {
      const updated = await api.patchIncident(inc.id, status, comment || undefined);
      setInc(updated);
      setMsg("Сохранено");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Ошибка");
    }
  }

  if (!inc) {
    return <p className="text-zinc-500">Инцидент не найден</p>;
  }

  return (
    <section className="space-y-6">
      <Link className="text-sm text-teal-700 hover:underline" to="/incidents">
        Назад к списку
      </Link>

      <header className="space-y-2">
        <h2 className="text-2xl font-semibold">{inc.title}</h2>
        <p className="flex gap-2">
          <Badge label={inc.severity} />
          <Badge label={inc.status} />
          <span className="font-mono text-sm text-zinc-600">
            risk {inc.risk_score.toFixed(2)}
          </span>
        </p>
      </header>

      <section className="rounded-xl border border-zinc-200 bg-white p-5">
        <h3 className="mb-3 text-sm font-medium text-zinc-500">Разбивка риска</h3>
        <ul className="space-y-3">
          <ScoreRow label="Rules" value={inc.rule_score} />
          <ScoreRow label="ML" value={inc.ml_score} />
          <ScoreRow label="Graph" value={inc.graph_score} />
          <ScoreRow label="Anomaly" value={inc.anomaly_score} />
        </ul>
      </section>

      {inc.rule_flags.length > 0 && (
        <p className="flex flex-wrap gap-2">
          {inc.rule_flags.map((f) => (
            <span key={f} className="rounded bg-zinc-100 px-2 py-1 text-xs">
              {f}
            </span>
          ))}
        </p>
      )}

      <textarea
        className="w-full rounded-lg border border-zinc-300 p-3 text-sm"
        rows={3}
        placeholder="Комментарий аналитика"
        value={comment}
        onChange={(e) => setComment(e.target.value)}
      />

      <section className="flex flex-wrap gap-2">
        <button
          type="button"
          className="rounded-lg bg-teal-700 px-4 py-2 text-sm text-white hover:bg-teal-800"
          onClick={() => setStatus("confirmed")}
        >
          Подтвердить
        </button>
        <button
          type="button"
          className="rounded-lg border border-zinc-300 px-4 py-2 text-sm hover:bg-zinc-50"
          onClick={() => setStatus("rejected")}
        >
          Отклонить
        </button>
        <button
          type="button"
          className="rounded-lg border border-zinc-300 px-4 py-2 text-sm hover:bg-zinc-50"
          onClick={() => setStatus("investigating")}
        >
          В работу
        </button>
      </section>

      {msg && <p className="text-sm text-zinc-600">{msg}</p>}
    </section>
  );
}
