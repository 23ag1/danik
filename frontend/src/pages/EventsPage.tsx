import { useEffect, useMemo, useState } from "react";
import { api } from "../shared/api";
import type { Event } from "../shared/types";

function truncate(text: string, n = 120) {
  return text.length <= n ? text : text.slice(0, n) + "…";
}

export function EventsPage() {
  const [items, setItems] = useState<Event[]>([]);
  const [q, setQ] = useState("");
  const [source, setSource] = useState("");

  useEffect(() => {
    api.getEvents().then(setItems).catch(console.error);
  }, []);

  const sources = useMemo(
    () => Array.from(new Set(items.map((e) => e.source))).sort(),
    [items],
  );

  const filtered = useMemo(() => {
    return items.filter((e) => {
      if (source && e.source !== source) return false;
      if (q && !e.raw_text.toLowerCase().includes(q.toLowerCase())) return false;
      return true;
    });
  }, [items, source, q]);

  return (
    <section className="space-y-6">
      <header>
        <h2 className="text-2xl font-semibold tracking-tight">Все события</h2>
        <p className="mt-1 text-sm text-zinc-500">
          Все записи включая низкий риск ({items.length} всего)
        </p>
      </header>

      <section className="flex flex-wrap gap-3">
        <input
          className="rounded-lg border border-zinc-300 px-3 py-2 text-sm"
          placeholder="Поиск по тексту"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <select
          className="rounded-lg border border-zinc-300 px-3 py-2 text-sm"
          value={source}
          onChange={(e) => setSource(e.target.value)}
        >
          <option value="">Все источники</option>
          {sources.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </section>

      <table className="w-full overflow-hidden rounded-xl border border-zinc-200 bg-white text-left text-sm">
        <thead className="border-b border-zinc-200 bg-zinc-50 text-xs uppercase text-zinc-500">
          <tr>
            <th className="px-4 py-3">#</th>
            <th className="px-4 py-3">Источник</th>
            <th className="px-4 py-3">Текст</th>
            <th className="px-4 py-3">URL</th>
            <th className="px-4 py-3">Дата</th>
          </tr>
        </thead>
        <tbody>
          {filtered.map((ev) => (
            <tr key={ev.id} className="border-t border-zinc-100 hover:bg-zinc-50">
              <td className="px-4 py-3 font-mono text-zinc-400">{ev.id}</td>
              <td className="px-4 py-3 font-mono text-xs">{ev.source}</td>
              <td className="px-4 py-3 max-w-lg text-zinc-700">{truncate(ev.raw_text)}</td>
              <td className="px-4 py-3 font-mono text-xs text-zinc-400">
                {ev.url ? (
                  <a href={ev.url} target="_blank" rel="noreferrer" className="hover:text-teal-700 underline">
                    ссылка
                  </a>
                ) : (
                  "—"
                )}
              </td>
              <td className="px-4 py-3 text-xs text-zinc-400 whitespace-nowrap">
                {new Date(ev.created_at).toLocaleString("ru-RU")}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {filtered.length === 0 && (
        <p className="text-center text-sm text-zinc-500">Записей нет</p>
      )}
    </section>
  );
}
