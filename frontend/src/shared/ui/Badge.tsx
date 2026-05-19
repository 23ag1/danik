const styles: Record<string, string> = {
  low: "bg-zinc-100 text-zinc-700",
  medium: "bg-amber-50 text-amber-800",
  high: "bg-rose-50 text-rose-800",
  new: "bg-sky-50 text-sky-800",
  investigating: "bg-violet-50 text-violet-800",
  confirmed: "bg-teal-50 text-teal-800",
  rejected: "bg-zinc-200 text-zinc-600",
};

export function Badge({ label }: { label: string }) {
  const key = label.toLowerCase();
  return (
    <span
      className={`inline-block rounded px-2 py-0.5 text-xs font-medium uppercase tracking-wide ${styles[key] ?? "bg-zinc-100 text-zinc-700"}`}
    >
      {label}
    </span>
  );
}
