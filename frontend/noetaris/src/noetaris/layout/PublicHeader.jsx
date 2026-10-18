import React, { useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { Search, ArrowRight, Menu, X } from "lucide-react";
import Logo from "../brand/Logo";

const links = [
  { to: "/platform", label: "Platform" },
  { to: "/capabilities", label: "Capabilities" },
  { to: "/architecture", label: "Architecture" },
  { to: "/developers", label: "Developers" },
  { to: "/docs", label: "Docs" },
  { to: "/contact", label: "Contact" },
];

export default function PublicHeader() {
  const { pathname } = useLocation();
  const [open, setOpen] = useState(false);
  return (
    <header
      className="sticky top-0 z-30 w-full border-b border-[color:var(--n-stroke-soft)] backdrop-blur-xl"
      style={{ background: "rgba(5, 10, 19, 0.65)" }}
      data-testid="public-header"
    >
      <div className="max-w-[1440px] mx-auto flex items-center px-4 md:px-8 h-16 gap-4 md:gap-6">
        <Link to="/" className="shrink-0" data-testid="brand-home-link">
          <Logo />
        </Link>
        <nav className="hidden xl:flex items-center gap-4 xl:gap-7 ml-2 xl:ml-6">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              className={({ isActive }) =>
                "n-nav-link text-sm " + (isActive || pathname === l.to ? "active" : "")
              }
              data-testid={`nav-${l.label.toLowerCase()}`}
            >
              {l.label}
            </NavLink>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-3">
          <Link to="/docs" className="hidden sm:flex n-btn-ghost w-9 h-9 items-center justify-center" aria-label="Open documentation" data-testid="public-search-btn">
            <Search size={16} />
          </Link>
          <Link to="/login" className="hidden sm:flex n-btn-ghost px-4 h-9 items-center text-sm" data-testid="public-signin-link">
            Sign In
          </Link>
          <Link to="/login" className="n-cta px-4 h-9 hidden sm:flex items-center text-sm gap-2 whitespace-nowrap" data-testid="public-getstarted-link">
            Check Access <ArrowRight size={14} />
          </Link>
          <button onClick={() => setOpen((v) => !v)} className="xl:hidden n-btn-ghost w-9 h-9 flex items-center justify-center" aria-label="Menu" aria-expanded={open} aria-controls="public-mobile-nav" data-testid="public-menu-btn">
            {open ? <X size={16} /> : <Menu size={16} />}
          </button>
        </div>
      </div>
      {open && (
        <nav id="public-mobile-nav" className="xl:hidden border-t border-[color:var(--n-stroke-soft)] px-4 py-3 flex flex-col gap-1" data-testid="public-mobile-nav">
          {[...links, { to: "/login", label: "Sign In" }].map((l) => (
            <Link key={l.to} to={l.to} onClick={() => setOpen(false)} className="py-2.5 px-2 rounded-lg text-sm text-[color:var(--n-text-mute)] hover:bg-[rgba(46,155,255,0.08)]">{l.label}</Link>
          ))}
        </nav>
      )}
    </header>
  );
}
