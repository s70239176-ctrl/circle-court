import { Link, NavLink, Outlet } from "react-router-dom";
import { Bot, FilePlus2, Gavel, LayoutDashboard } from "lucide-react";

const nav = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/create", label: "Create", icon: FilePlus2 },
  { to: "/agent", label: "Agent", icon: Bot }
];

export function Layout() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-court-line bg-[#0b0d12]/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
          <Link to="/" className="flex items-center gap-3">
            <div className="grid h-9 w-9 place-items-center rounded-md bg-court-mint text-court-ink">
              <Gavel size={18} />
            </div>
            <div>
              <div className="text-base font-semibold">Circle Court</div>
              <div className="text-xs text-slate-400">Agent-native escrow resolution</div>
            </div>
          </Link>
          <nav className="flex gap-1">
            {nav.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex h-10 items-center gap-2 rounded-md px-3 text-sm ${isActive ? "bg-white/10 text-white" : "text-slate-400 hover:text-white"}`
                }
              >
                <item.icon size={16} />
                <span className="hidden sm:inline">{item.label}</span>
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
