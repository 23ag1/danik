import { useEffect, useState } from "react";
import { api } from "../shared/api";
import type { MonitoredSource } from "../shared/types";

export function SourcesPage() {
  const [items, setItems] = useState<MonitoredSource[]>([]);
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [sourceType, setSourceType] = useState<"rss" | "telegram">("rss");
  const [interval, setInterval] = useState(300);
  const [error, setError] = useState("");
  const [fetching, setFetching] = useState<number | null>(null);

  useEffect(() => {
    api.getSources().then(setItems).catch(console.error);
  }, []);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      const src = await api.createSource({ name, url, source_type: sourceType, interval_sec: interval });
      setItems((prev) => [...prev, src]);
      setName("");
      setUrl("");
      setSourceType("rss");
      setInterval(300);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Ошибка");
    }
  }

  async function handleToggle(src: MonitoredSource) {
    const updated = await api.patchSource(src.id, { enabled: !src.enabled });
    setItems((prev) => prev.map((s) => (s.id === src.id ? updated : s)));
  }

  async function handleDelete(id: number) {
    await api.deleteSource(id);
    setItems((prev) => prev.filter((s) => s.id !== id));
  }

  async function handleFetch(id: number) {
    setFetching(id);
    try {
      const res = await api.fetchSource(id);
      alert(`Загружено новых записей: ${res.ingested}`);
      const sources = await api.getSources();
      setItems(sources);
    } finally {
      setFetching(null);
    }
  }

  return (
    <section className="space-y-8">
      <header>
        <h2 className="text-2xl font-semibold tracking-tight">Источники мониторинга</h2>
        <p className="mt-1 text-sm text-zinc-500">RSS-ленты и Telegram-каналы</p>
      </header>

      <form onSubmit={handleAdd} className="flex flex-wrap gap-3 items-end">
        <div className="flex flex-col gap-1">
          <label className="text-xs text-zinc-500">Название</label>
          <input
            className="rounded-lg border border-zinc-300 px-3 py-2 text-sm"
            placeholder="Коммерсантъ"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-zinc-500">Тип</label>
          <select
            className="rounded-lg border border-zinc-300 px-3 py-2 text-sm"
            value={sourceType}
            onChange={(e) => setSourceType(e.target.value as "rss" | "telegram")}
          >
            <option value="rss">RSS</option>
            <option value="telegram">Telegram</option>
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-zinc-500">{sourceType === "telegram" ? "@канал или ID" : "URL ленты"}</label>
          <input
            className="rounded-lg border border-zinc-300 px-3 py-2 text-sm w-72"
            placeholder={sourceType === "telegram" ? "@channel_name" : "https://example.com/rss.xml"}
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            required
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-zinc-500">Интервал (сек)</label>
          <input
            type="number"
            className="rounded-lg border border-zinc-300 px-3 py-2 text-sm w-24"
            value={interval}
            min={60}
            onChange={(e) => setInterval(Number(e.target.value))}
          />
        </div>
        <button
          type="submit"
          className="rounded-lg bg-teal-700 px-4 py-2 text-sm font-medium text-white hover:bg-teal-800"
        >
          Добавить
        </button>
        {error && <p className="text-sm text-red-600">{error}</p>}
      </form>

      <table className="w-full overflow-hidden rounded-xl border border-zinc-200 bg-white text-left text-sm">
        <thead className="border-b border-zinc-200 bg-zinc-50 text-xs uppercase text-zinc-500">
          <tr>
            <th className="px-4 py-3">Название</th>
            <th className="px-4 py-3">Тип</th>
            <th className="px-4 py-3">URL</th>
            <th className="px-4 py-3">Интервал</th>
            <th className="px-4 py-3">Последний запрос</th>
            <th className="px-4 py-3">Вкл</th>
            <th className="px-4 py-3">Действия</th>
          </tr>
        </thead>
        <tbody>
          {items.map((src) => (
            <tr key={src.id} className="border-t border-zinc-100 hover:bg-zinc-50">
              <td className="px-4 py-3 font-medium">{src.name}</td>
              <td className="px-4 py-3">
                <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${src.source_type === "telegram" ? "bg-blue-100 text-blue-700" : "bg-orange-100 text-orange-700"}`}>
                  {src.source_type}
                </span>
              </td>
              <td className="px-4 py-3 font-mono text-xs text-zinc-500 max-w-xs truncate">
                <a href={src.url} target="_blank" rel="noreferrer" className="hover:text-teal-700 underline">
                  {src.url}
                </a>
              </td>
              <td className="px-4 py-3 font-mono text-xs">{src.interval_sec}с</td>
              <td className="px-4 py-3 text-xs text-zinc-400">
                {src.last_fetched_at
                  ? new Date(src.last_fetched_at).toLocaleString("ru-RU")
                  : "—"}
              </td>
              <td className="px-4 py-3">
                <button
                  onClick={() => handleToggle(src)}
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                    src.enabled
                      ? "bg-teal-100 text-teal-800"
                      : "bg-zinc-100 text-zinc-500"
                  }`}
                >
                  {src.enabled ? "вкл" : "выкл"}
                </button>
              </td>
              <td className="px-4 py-3 flex gap-2">
                <button
                  onClick={() => handleFetch(src.id)}
                  disabled={fetching === src.id}
                  className="rounded-lg border border-zinc-300 px-2 py-1 text-xs hover:bg-zinc-100 disabled:opacity-50"
                >
                  {fetching === src.id ? "..." : "Запросить"}
                </button>
                <button
                  onClick={() => handleDelete(src.id)}
                  className="rounded-lg border border-red-200 px-2 py-1 text-xs text-red-600 hover:bg-red-50"
                >
                  Удалить
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {items.length === 0 && (
        <p className="text-center text-sm text-zinc-500">Источников нет — добавьте первый</p>
      )}
    </section>
  );
}
