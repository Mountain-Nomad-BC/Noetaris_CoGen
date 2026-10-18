import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

const Context = createContext(null);
const STORAGE_KEY = 'noetaris.userPrefs.v1';

const defaultPrefs = {
  // Profile
  displayName: 'Jane Dohen',
  initials: 'JD',
  avatarGradient: 'blue-red', // 'blue-red' | 'blue-cyan' | 'red-amber' | 'green-cyan' | 'purple-pink'
  role: 'Administrator',
  org: 'Nomadic Lab Engineering',

  // AI Assistant preferences
  ai: {
    responseVerbosity: 'balanced', // 'concise' | 'balanced' | 'detailed'
    autoCitation: true,
    autoDocOpen: true,
    showConfidence: true,
    assistantName: 'Noetaris',
    voiceEnabled: true,
  },

  // Appearance
  appearance: {
    fontSize: 'default', // 'compact' | 'default' | 'large'
    animationsEnabled: true,
    accentColor: 'blue', // 'blue' | 'cyan' | 'red' | 'amber' | 'green'
  },
};

const GRADIENT_MAP = {
  'blue-red': 'from-[#1A6BB5] to-[#C41E2A]',
  'blue-cyan': 'from-[#1A6BB5] to-[#5ED6ED]',
  'red-amber': 'from-[#C41E2A] to-[#F2B35E]',
  'green-cyan': 'from-[#48C7A1] to-[#5ED6ED]',
  'purple-pink': 'from-[#8F85E8] to-[#F24F61]',
};

function restore() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return defaultPrefs;
    const parsed = JSON.parse(raw);
    // Deep merge with defaults to handle new keys
    return {
      ...defaultPrefs,
      ...parsed,
      ai: { ...defaultPrefs.ai, ...(parsed.ai || {}) },
      appearance: { ...defaultPrefs.appearance, ...(parsed.appearance || {}) },
    };
  } catch {
    return defaultPrefs;
  }
}

export function UserPrefsProvider({ children }) {
  const [prefs, setPrefs] = useState(restore);

  useEffect(() => {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs)); } catch { /* quota */ }
  }, [prefs]);

  // Listen for identity-cleared to reset prefs
  useEffect(() => {
    const handler = () => setPrefs(defaultPrefs);
    window.addEventListener('noetaris-identity-cleared', handler);
    return () => window.removeEventListener('noetaris-identity-cleared', handler);
  }, []);

  const updateProfile = useCallback((updates) => {
    setPrefs(p => ({ ...p, ...updates }));
  }, []);

  const updateAI = useCallback((updates) => {
    setPrefs(p => ({ ...p, ai: { ...p.ai, ...updates } }));
  }, []);

  const updateAppearance = useCallback((updates) => {
    setPrefs(p => ({ ...p, appearance: { ...p.appearance, ...updates } }));
  }, []);

  const resetAll = useCallback(() => {
    setPrefs(defaultPrefs);
    try { localStorage.removeItem(STORAGE_KEY); } catch {}
  }, []);

  const gradientClass = GRADIENT_MAP[prefs.avatarGradient] || GRADIENT_MAP['blue-red'];

  const value = useMemo(() => ({
    prefs,
    gradientClass,
    gradientMap: GRADIENT_MAP,
    updateProfile,
    updateAI,
    updateAppearance,
    resetAll,
  }), [prefs, gradientClass, updateProfile, updateAI, updateAppearance, resetAll]);

  return <Context.Provider value={value}>{children}</Context.Provider>;
}

export function useUserPrefs() {
  const value = useContext(Context);
  if (!value) throw new Error('UserPrefsProvider is required');
  return value;
}
