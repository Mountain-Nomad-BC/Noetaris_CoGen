import React, { useEffect, useState, Suspense, lazy } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight, Mail, Github, KeyRound, Shield } from "lucide-react";
import Logo from "../../brand/Logo";
import { mode } from "../../services/api";
import LiveSignIn from './LiveSignIn';

const HeroScene = lazy(() => import("../../brand/HeroScene"));

export default function LoginPage() {
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showHeroScene, setShowHeroScene] = useState(false);

  useEffect(() => {
    const desktop = window.matchMedia("(min-width: 1024px)");
    const update = () => setShowHeroScene(desktop.matches);
    update();
    desktop.addEventListener?.("change", update);
    return () => desktop.removeEventListener?.("change", update);
  }, []);

  if (mode === 'live') return <LiveSignIn />;

  return (
    <div className="min-h-screen grid grid-cols-1 lg:grid-cols-[1.1fr_1fr]" data-testid="login-page">
      {/* Left: Prism */}
      <div className="relative overflow-hidden hidden lg:block min-h-screen border-r border-[color:var(--n-stroke-soft)]">
        <div className="absolute inset-0 pointer-events-none" style={{
          background: "radial-gradient(900px 500px at 50% 55%, rgba(46,155,255,0.22), transparent 70%), radial-gradient(600px 400px at 80% 90%, rgba(196,30,42,0.15), transparent 70%)"
        }} />
        {showHeroScene && (
          <Suspense fallback={null}>
            <HeroScene />
          </Suspense>
        )}
        <div className="absolute top-10 left-10 right-10 flex flex-wrap gap-2 z-10">
          {["Source access gated", "PDF viewer unqualified", "Governance unqualified", "Preview disclosures"].map((t) => (
            <span key={t} className="n-chip">{t}</span>
          ))}
        </div>
        <div className="absolute bottom-8 left-8 right-8 n-glass p-5 rounded-2xl">
          <div className="text-[11px] uppercase tracking-[0.25em] text-[color:var(--n-text-subtle)] mb-2">Preview access</div>
          <div className="font-display text-2xl mb-1">Explore the current preview.</div>
          <div className="text-sm text-[color:var(--n-text-mute)]">
            This preview does not authenticate source access or certify isolation, citation fidelity, or workflow readiness.
          </div>
        </div>
      </div>

      {/* Right: Auth card */}
      <div className="relative flex flex-col items-center justify-center px-6 md:px-8 py-16">
        <div className="w-full max-w-[420px]">
          <Link to="/" className="mb-10 inline-block" data-testid="login-brand-link"><Logo /></Link>

          <h2 className="font-display text-3xl mb-2">Welcome back</h2>
          <p className="text-[color:var(--n-text-mute)] text-sm mb-8">
            {mode === 'demo' ? 'Explore a clearly labeled demonstration. No credentials or authentication are used.' : 'Live sign-in is blocked until server-authenticated sessions are integrated.'}
          </p>

          <form onSubmit={(e)=>{e.preventDefault(); if (mode === 'demo') nav('/app');}} className="space-y-4" data-testid="login-form">
            <label className="block">
              <span className="text-xs uppercase tracking-widest text-[color:var(--n-text-subtle)]">Demo email (not authenticated)</span>
              <div className="mt-2 relative">
                <Mail size={14} className="absolute z-10 left-3 top-1/2 -translate-y-1/2 text-[color:var(--n-text-subtle)]" />
                <input
                  value={email} onChange={(e)=>setEmail(e.target.value)}
                  className="w-full h-11 pl-9 pr-3 rounded-xl n-glass text-sm placeholder:text-[color:var(--n-text-subtle)] outline-none focus:border-[color:var(--n-cyan)]"
                  type="email" required autoComplete="off" placeholder="you@domain.com"
                  data-testid="login-email-input"
                />
              </div>
            </label>
            <label className="block">
              <span className="text-xs uppercase tracking-widest text-[color:var(--n-text-subtle)]">Local token</span>
              <div className="mt-2 relative">
                <KeyRound size={14} className="absolute z-10 left-3 top-1/2 -translate-y-1/2 text-[color:var(--n-text-subtle)]" />
                <input
                  value={password} onChange={(e)=>setPassword(e.target.value)}
                  className="w-full h-11 pl-9 pr-3 rounded-xl n-glass text-sm placeholder:text-[color:var(--n-text-subtle)] outline-none focus:border-[color:var(--n-cyan)]"
                  type="password" autoComplete="off" disabled={mode === 'demo'} placeholder="No token needed for preview"
                  data-testid="login-password-input"
                />
              </div>
            </label>

            <button
              type="submit" disabled={mode === 'live'}
              className="n-cta disabled:opacity-50 disabled:cursor-not-allowed w-full h-11 flex items-center justify-center gap-2 text-sm"
              data-testid="login-submit-btn"
            >
              {mode === 'demo' ? 'Enter preview' : 'Authentication not integrated'} <ArrowRight size={14} />
            </button>
          </form>

          <div className="my-6 flex items-center gap-3 text-[11px] uppercase tracking-widest text-[color:var(--n-text-subtle)]">
            <div className="flex-1 n-divider" /> or <div className="flex-1 n-divider" />
          </div>

          <div className="space-y-2">
            <button
              disabled
              className="w-full h-10 rounded-xl n-btn-ghost flex items-center justify-center gap-2 text-sm opacity-60 cursor-not-allowed"
              title="Google sign-in is unavailable in this preview"
              data-testid="login-google-btn"
            >
              <GoogleIcon /> Google sign-in unavailable <span className="ml-auto n-chip-amber n-chip">PREVIEW</span>
            </button>
            <button
              disabled
              className="w-full h-10 rounded-xl n-btn-ghost flex items-center justify-center gap-2 text-sm opacity-60 cursor-not-allowed"
              title="GitHub sign-in is unavailable in this preview"
              data-testid="login-github-btn"
            >
              <Github size={14} /> GitHub sign-in unavailable <span className="ml-auto n-chip-amber n-chip">PREVIEW</span>
            </button>
          </div>

          <div className="mt-10 flex items-center gap-2 text-[11px] text-[color:var(--n-text-subtle)]">
            <Shield size={12} />
            Authority remains server-side. Demo mode cannot change global policy.
          </div>
        </div>
      </div>
    </div>
  );
}

const GoogleIcon = () => (
  <svg width="14" height="14" viewBox="0 0 48 48"><path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.6 32.1 29.2 35 24 35c-6.1 0-11-4.9-11-11s4.9-11 11-11c2.8 0 5.4 1 7.4 2.8l5.7-5.7C33.6 7.1 29 5 24 5 13.5 5 5 13.5 5 24s8.5 19 19 19 19-8.5 19-19c0-1.3-.1-2.3-.4-3.5z"/><path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 15.1 19 12 24 12c2.8 0 5.4 1 7.4 2.8l5.7-5.7C33.6 7.1 29 5 24 5 16.2 5 9.5 9.3 6.3 14.7z"/><path fill="#4CAF50" d="M24 43c5 0 9.6-1.9 13.1-5l-6-5c-2 1.4-4.4 2.1-7.1 2.1-5.2 0-9.6-2.9-11.4-7.1l-6.5 5C9.5 38.7 16.2 43 24 43z"/><path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.9 2.5-2.5 4.6-4.6 6.1l6 5c-.4.4 6.3-4.6 6.3-15.1 0-1.3-.1-2.3-.4-3.5z"/></svg>
);
