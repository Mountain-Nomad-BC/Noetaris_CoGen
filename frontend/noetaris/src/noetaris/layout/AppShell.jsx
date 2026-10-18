import React, { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { 
  Activity, Bell, Bot, BrainCircuit, ChevronRight, Circle, Code2, Coins, 
  Cpu, FileCheck2, FileSearch, FlaskConical, Hexagon, LayoutDashboard, 
  LayoutTemplate, Library, LineChart, ListChecks, LogOut, Menu, MessagesSquare, 
  PanelLeft, Plug, Radar, Scale, Search, Settings, Share2, ShieldCheck, 
  Stamp, TestTube, ToggleRight, Workflow, X 
} from "lucide-react";
import { navDomains, demoNotifications } from "../data/fixtures";
import { mode } from "../services/api";
import Logo from "../brand/Logo";
import { useVoice } from "../state/VoiceContext";
import FloatingAssistant from '../components/FloatingAssistant';
import ProfileDropdown from '../components/ProfileDropdown';

const liveNavDomains = [
  {
    key: "intelligence",
    label: "Intelligence",
    items: [
      { to: "/app", label: "Command Center", icon: "LayoutDashboard" },
      { to: "/app/chat", label: "Conversations", icon: "MessagesSquare" },
      { to: "/app/library", label: "Document Library", icon: "Library" },
      { to: "/app/knowledge", label: "Knowledge Explorer", icon: "Share2" },
      { to: "/app/knowledge/review", label: "Knowledge Review", icon: "ShieldCheck" },
      { to: "/app/research", label: "Research Workspace", icon: "FlaskConical" },
      { to: "/app/memory", label: "Memory / Learning", icon: "BrainCircuit" },
      { to: "/app/learning", label: "Learning", icon: "BrainCircuit" },
      { to: "/app/queue", label: "Task Queue", icon: "ListChecks" },
    ],
  },
  {
    key: "govern",
    label: "Govern",
    items: [
      { to: "/app/approvals", label: "Approvals", icon: "Scale" },
      { to: "/app/costs", label: "Cost / Usage", icon: "Coins" },
      { to: "/app/models", label: "Model Status", icon: "Cpu" },
      { to: "/app/developers", label: "Live API Capabilities", icon: "Cpu" },
      { to: "/app/integrations", label: "Integration Setup", icon: "Plug" },
      { to: "/app/analytics", label: "Measured Activity", icon: "LineChart" },
      { to: "/app/observability", label: "Runtime Observations", icon: "Activity" },
      { to: "/app/audit", label: "Audit Events", icon: "FileCheck2" },
      { to: "/app/governance", label: "Security Policy", icon: "ShieldCheck" },
      { to: "/app/settings", label: "Deployment Settings", icon: "Settings" },
    ],
  },
];

const Icons = { 
  Activity, Bell, Bot, BrainCircuit, ChevronRight, Circle, Code2, Coins, 
  Cpu, FileCheck2, FileSearch, FlaskConical, Hexagon, LayoutDashboard, 
  LayoutTemplate, Library, LineChart, ListChecks, LogOut, Menu, MessagesSquare, 
  PanelLeft, Plug, Radar, Scale, Search, Settings, Share2, ShieldCheck, 
  Stamp, TestTube, ToggleRight, Workflow, X 
};

function Icon({ name, size = 16, className = "" }) {
  const C = Icons[name] || Icons.Circle;
  return <C size={size} className={className} />;
}

export default function AppShell() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [notifications, setNotifications] = useState(mode === "demo" ? demoNotifications : []);
  const { pathname } = useLocation();
  const { mic, draft } = useVoice();

  useEffect(() => setMobileOpen(false), [pathname]);

  useEffect(() => {
    const media = window.matchMedia?.('(prefers-reduced-motion: reduce)');
    const update = () => {
      document.documentElement.dataset.reduceMotion = media?.matches ? 'true' : 'false';
      window.dispatchEvent(new Event('noetaris-motion-change'));
    };
    update();
    media?.addEventListener('change', update);
    return () => media?.removeEventListener('change', update);
  }, []);

  useEffect(() => () => mic.stop(), []); // Stop recording when leaving app shell

  useEffect(() => {
    const handler = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { 
        e.preventDefault(); 
        setPaletteOpen((v) => !v); 
      }
      if (e.key === "Escape") { 
        setPaletteOpen(false); 
        setMobileOpen(false); 
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  const narrow = collapsed && !mobileOpen;

  return (
    <div className="h-screen flex overflow-hidden" data-testid="app-shell">
      {mobileOpen && (
        <div 
          className="fixed inset-0 z-30 bg-black/60 md:hidden" 
          onClick={() => setMobileOpen(false)} 
          data-testid="sidebar-backdrop" 
        />
      )}

      {/* Sidebar Navigation */}
      <aside
        className={`fixed md:static inset-y-0 left-0 z-40 shrink-0 border-r border-[color:var(--n-stroke-soft)] transition-[width,transform] duration-200 ${
          narrow ? "md:w-[68px]" : "md:w-[260px]"
        } w-[260px] ${mobileOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"}`}
        style={{ background: "linear-gradient(180deg, rgba(10,19,33,.98), rgba(5,10,19,.98))" }}
        data-testid="app-sidebar"
      >
        <div className={`h-16 flex items-center border-b border-[color:var(--n-stroke-soft)] ${narrow ? "justify-center px-2" : "px-4"}`}>
          {!narrow && (
            <Link to="/" className="shrink-0" data-testid="sidebar-brand-link">
              <Logo size={28} />
            </Link>
          )}
          <button 
            onClick={() => (mobileOpen ? setMobileOpen(false) : setCollapsed((v) => !v))}
            className={`${narrow ? "" : "ml-auto"} n-btn-ghost w-8 h-8 flex items-center justify-center`} 
            aria-label="Toggle sidebar" 
            data-testid="sidebar-toggle"
          >
            {mobileOpen ? <Icons.X size={14} /> : <Icons.PanelLeft size={14} />}
          </button>
        </div>

        <nav className="py-4 overflow-y-auto h-[calc(100vh-64px)]">
          {(mode === "demo" ? navDomains : liveNavDomains).map((d) => (
            <div key={d.key} className="mb-4">
              {!narrow && (
                <div className="px-5 pb-2 text-[10px] uppercase tracking-[0.2em] text-[color:var(--n-text-subtle)]">
                  {d.label}
                </div>
              )}
              {d.items.map((it) => (
                <NavLink 
                  key={it.to} 
                  to={it.to} 
                  end 
                  title={narrow ? it.label : undefined}
                  className={({ isActive }) =>
                    `group flex items-center gap-3 mx-2 px-3 py-2 rounded-lg text-sm transition-colors border ${narrow ? "justify-center" : ""} ` +
                    (isActive 
                      ? "bg-[rgba(46,155,255,0.1)] text-[color:var(--n-text)] border-[rgba(46,155,255,0.25)]"
                      : "text-[color:var(--n-text-mute)] hover:bg-[rgba(233,239,246,0.03)] hover:text-[color:var(--n-text)] border-transparent")
                  }
                  data-testid={`nav-${it.to.replace(/\//g, "-").slice(1)}`}
                >
                  <Icon name={it.icon} className="shrink-0 transition-transform group-hover:scale-110" />
                  {!narrow && <span className="truncate">{it.label}</span>}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <TopBar 
          openPalette={() => setPaletteOpen(true)} 
          openMenu={() => setMobileOpen(true)} 
          pathname={pathname} 
          unread={mode === "demo" ? notifications.length : null} 
        />
        <main className="flex-1 overflow-y-auto overflow-x-hidden">
          {mode === "live" && <aside className="border-b border-[color:var(--n-stroke-soft)] px-4 py-3 text-sm" aria-label="AI disclosure">AI-assisted workspace. Generated answers can be wrong; verify original sources. <Link className="underline" to="/ai-transparency">AI transparency</Link> ? <Link className="underline" to="/privacy">Privacy</Link></aside>}
          <Outlet context={mode === "demo" ? { notifications, setNotifications } : undefined} />
          {mode !== "demo" && <FloatingAssistant />}
        </main>
      </div>

      {/* Active Voice Floater */}
      {mic.state === 'listening' && (
        <div className="fixed z-50 bottom-3 left-3 md:left-auto md:right-6 max-w-[min(90vw,420px)] n-glass rounded-xl px-4 py-2 text-xs shadow-xl" role="status">
          <div className="flex items-center gap-3">
            <span className="text-[color:var(--n-cyan)] n-animate-shimmer">● Voice active</span>
            <span className="opacity-70">{Math.floor(mic.elapsed / 60)}:{String(mic.elapsed % 60).padStart(2,'0')}</span>
            <button type="button" onClick={mic.stop} className="underline ml-auto">Stop</button>
            <Link to="/app/chat" className="underline">Chat</Link>
          </div>
          <p className="text-[color:var(--n-text-mute)] mt-1 truncate">
            {mic.interim || draft || 'Audio recognition stream active'}
          </p>
        </div>
      )}

      {/* Floating AI Assistant FAB & Side-by-Side Manual */}
      {mode === "demo" && <FloatingAssistant />}

      {/* Command Palette */}
      {paletteOpen && <CommandPalette onClose={() => setPaletteOpen(false)} />}
    </div>
  );
}

function TopBar({ openPalette, openMenu, pathname, unread }) {
  const crumbs = pathname.split("/").filter(Boolean);
  return (
    <header 
      className="sticky top-0 z-20 h-16 border-b border-[color:var(--n-stroke-soft)] flex items-center px-4 md:px-6 gap-3"
      style={{ background: "rgba(5,10,19,0.75)", backdropFilter: "blur(12px)" }} 
      data-testid="app-topbar"
    >
      <button 
        onClick={openMenu} 
        className="md:hidden n-btn-ghost w-9 h-9 flex items-center justify-center" 
        aria-label="Open menu" 
        data-testid="topbar-menu-btn"
      >
        <Icons.Menu size={16} />
      </button>

      {/* Breadcrumbs */}
      <div className="hidden sm:flex items-center gap-2 text-xs text-[color:var(--n-text-mute)] min-w-0">
        {crumbs.map((c, i) => (
          <React.Fragment key={i}>
            {i < crumbs.length - 1 ? (
              <Link to={"/" + crumbs.slice(0, i + 1).join("/")} className="hover:text-[color:var(--n-text)] capitalize">
                {c}
              </Link>
            ) : (
              <span className="text-[color:var(--n-text)] truncate capitalize">{c}</span>
            )}
            {i < crumbs.length - 1 && <Icons.ChevronRight size={12} />}
          </React.Fragment>
        ))}
      </div>

      {/* Global Quick Search */}
      <button 
        onClick={openPalette} 
        className="md:ml-4 flex items-center gap-2 n-glass px-3 py-1.5 rounded-full text-xs text-[color:var(--n-text-mute)] lg:min-w-[260px]" 
        data-testid="topbar-command-palette-trigger"
      >
        <Icons.Search size={14} />
        <span className="opacity-80 hidden lg:inline">Search agents, workflows, docs…</span>
        <kbd className="ml-auto text-[10px] px-1.5 py-0.5 rounded border border-[color:var(--n-stroke-soft)] hidden lg:inline">⌘K</kbd>
      </button>

      {/* Right User & Live Status Section */}
      <div className="ml-auto flex items-center gap-2 md:gap-3">
        {unread === null ? (
          <button
            type="button"
            disabled
            className="relative n-btn-ghost w-9 h-9 flex items-center justify-center opacity-50"
            aria-label="Notifications unavailable"
            title="A live notification feed is not configured"
            data-testid="topbar-notifications"
          >
            <Icons.Bell size={16} />
          </button>
        ) : (
          <Link
            to="/app/notifications"
            className="relative n-btn-ghost w-9 h-9 flex items-center justify-center"
            aria-label="Notifications"
            data-testid="topbar-notifications"
          >
            <Icons.Bell size={16} />
            {unread > 0 && (
              <span
                className="absolute -top-0.5 -right-0.5 w-4 h-4 rounded-full bg-[color:var(--n-red)] text-[9px] flex items-center justify-center"
                data-testid="topbar-notif-count"
              >
                {unread}
              </span>
            )}
          </Link>
        )}

        {/* User Profile Dropdown */}
        <ProfileDropdown />
      </div>
    </header>
  );
}

function CommandPalette({ onClose }) {
  const [q, setQ] = useState("");
  const [idx, setIdx] = useState(0);
  const nav = useNavigate();
  const all = (mode === "demo" ? navDomains : liveNavDomains).flatMap((d) => d.items.map((i) => ({ ...i, domain: d.label })));
  const results = all.filter((i) => i.label.toLowerCase().includes(q.toLowerCase())).slice(0, 10);

  const onKey = (e) => {
    if (e.key === "ArrowDown") { 
      e.preventDefault(); 
      setIdx((i) => Math.min(results.length - 1, i + 1)); 
    }
    if (e.key === "ArrowUp") { 
      e.preventDefault(); 
      setIdx((i) => Math.max(0, i - 1)); 
    }
    if (e.key === "Enter" && results[idx]) { 
      nav(results[idx].to); 
      onClose(); 
    }
  };

  return (
    <div 
      className="fixed inset-0 z-50 flex items-start justify-center pt-32 px-4 bg-[rgba(0,0,0,0.6)]" 
      onClick={onClose} 
      data-testid="command-palette"
    >
      <div className="n-glass w-full max-w-[560px] rounded-2xl p-3" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center gap-2 border-b border-[color:var(--n-stroke-soft)] px-3 pb-3">
          <Icons.Search size={16} className="text-[color:var(--n-text-mute)]" />
          <input 
            autoFocus 
            value={q} 
            onChange={(e) => { setQ(e.target.value); setIdx(0); }} 
            onKeyDown={onKey} 
            placeholder="Jump to…"
            className="bg-transparent flex-1 outline-none text-sm placeholder:text-[color:var(--n-text-subtle)] text-white" 
            data-testid="command-palette-input" 
          />
          <kbd className="text-[10px] px-1.5 py-0.5 rounded border border-[color:var(--n-stroke-soft)] text-slate-400">esc</kbd>
        </div>
        <ul className="mt-2 max-h-72 overflow-y-auto">
          {results.map((r, i) => (
            <li key={r.to}>
              <Link 
                to={r.to} 
                onClick={onClose} 
                onMouseEnter={() => setIdx(i)}
                className={"flex items-center gap-3 px-3 py-2 rounded-lg text-sm " + (i === idx ? "bg-[rgba(46,155,255,0.12)] text-white" : "text-slate-300")} 
                data-testid={`cmd-${r.to}`}
              >
                <Icon name={r.icon} />
                <span>{r.label}</span>
                <span className="ml-auto text-[10px] text-[color:var(--n-text-subtle)] uppercase tracking-widest">{r.domain}</span>
              </Link>
            </li>
          ))}
          {results.length === 0 && (
            <li className="px-3 py-6 text-sm text-[color:var(--n-text-subtle)] text-center">No matches found</li>
          )}
        </ul>
      </div>
    </div>
  );
}
