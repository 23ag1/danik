import { Link, Outlet, useLocation } from "react-router-dom";

const links = [
  { to: "/", label: "Сводка" },
  { to: "/events", label: "Все события" },
  { to: "/incidents", label: "Инциденты" },
  { to: "/ingest", label: "Загрузка" },
];

export function Layout() {
  const { pathname } = useLocation();

  return (
    <>
      <header className="border-b border-zinc-200/80 bg-white">
        <section className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4">
          <section>
            <p className="text-xs font-medium uppercase tracking-widest text-teal-700">
              Fraud Monitor
            </p>
            <h1 className="text-lg font-semibold tracking-tight">Панель аналитика</h1>
          </section>
          <nav className="flex flex-wrap gap-1">
            {links.map(({ to, label }) => (
              <Link
                key={to}
                to={to}
                className={`rounded-lg px-3 py-2 text-sm transition ${
                  pathname === to || (to !== "/" && pathname.startsWith(to))
                    ? "bg-zinc-900 text-white"
                    : "text-zinc-600 hover:bg-zinc-100"
                }`}
              >
                {label}
              </Link>
            ))}
          </nav>
        </section>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8 min-h-[100dvh]">
        <Outlet />
      </main>
    </>
  );
}
