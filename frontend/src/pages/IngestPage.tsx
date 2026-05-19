import { FormEvent, useState } from "react";
import { api } from "../shared/api";

export function IngestPage() {
  const [source, setSource] = useState("telegram");
  const [userId, setUserId] = useState("");
  const [rawText, setRawText] = useState("");
  const [log, setLog] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setLog("");
    try {
      const res = await api.createEvent({ source, user_id: userId, raw_text: rawText });
      setLog(
        `Событие #${res.id} создано. Risk: ${res.risk_score.toFixed(2)}` +
          (res.incident_id ? `, инцидент #${res.incident_id}` : ""),
      );
      setRawText("");
    } catch (err) {
      setLog(err instanceof Error ? err.message : "Ошибка");
    } finally {
      setBusy(false);
    }
  }

  async function onCsv(file: File) {
    const text = await file.text();
    const rawLines = text.trim().split(/\r?\n/);
    const lines = rawLines[0]?.toLowerCase().startsWith("source") ? rawLines.slice(1) : rawLines;
    setBusy(true);
    let ok = 0;
    for (const line of lines) {
      if (!line.trim()) continue;
      const parts = line.split(",");
      if (parts.length < 3) continue;
      const [src, uid, body, url] = parts;
      try {
        await api.createEvent({
          source: src.trim(),
          user_id: uid.trim(),
          raw_text: body.trim(),
          url: url?.trim() || null,
        });
        ok += 1;
      } catch {
        /* skip bad rows */
      }
    }
    setLog(`CSV: отправлено ${ok} из ${lines.length} строк`);
    setBusy(false);
  }

  return (
    <section className="mx-auto max-w-xl space-y-8">
      <header>
        <h2 className="text-2xl font-semibold tracking-tight">Загрузка</h2>
        <p className="mt-1 text-sm text-zinc-500">Ручной ввод или CSV: source,user_id,text,url</p>
      </header>

      <form className="space-y-4 rounded-xl border border-zinc-200 bg-white p-5" onSubmit={onSubmit}>
        <label className="block text-sm">
          Источник
          <input
            className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2"
            value={source}
            onChange={(e) => setSource(e.target.value)}
            required
          />
        </label>
        <label className="block text-sm">
          User ID
          <input
            className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            required
          />
        </label>
        <label className="block text-sm">
          Текст
          <textarea
            className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2"
            rows={4}
            value={rawText}
            onChange={(e) => setRawText(e.target.value)}
            required
          />
        </label>
        <button
          type="submit"
          disabled={busy}
          className="rounded-lg bg-teal-700 px-4 py-2 text-sm text-white disabled:opacity-50"
        >
          Отправить
        </button>
      </form>

      <label className="block rounded-xl border border-dashed border-zinc-300 bg-white p-6 text-center text-sm">
        CSV файл
        <input
          type="file"
          accept=".csv,text/csv"
          className="mt-2 block w-full text-xs"
          disabled={busy}
          onChange={(e) => e.target.files?.[0] && onCsv(e.target.files[0])}
        />
      </label>

      {log && <p className="rounded-lg bg-zinc-100 px-3 py-2 text-sm">{log}</p>}
    </section>
  );
}
