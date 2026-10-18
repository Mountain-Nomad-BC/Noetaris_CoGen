import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { demoConversation } from '../data/fixtures';
import { mode } from '../services/api';

const Context = createContext(null);
const KEY = 'noetaris.demo.conversation.v2';
const sample = { ...demoConversation, messages: [...demoConversation.messages] };
const seed = mode === 'demo' ? { activeId: sample.id, threads: [sample] } : { activeId: null, threads: [] };
function restore() {
  if (mode !== 'demo') return seed;
  try {
    const data = JSON.parse(sessionStorage.getItem(KEY));
    if (data && Array.isArray(data.threads) && data.threads.length && data.threads.length <= 100 &&
        data.threads.every(t => typeof t.id === 'string' && Array.isArray(t.messages) && t.messages.length <= 300)) return data;
  } catch { /* storage not available or data invalid */ }
  return seed;
}
export function ConversationProvider({ children }) {
  const [state, setState] = useState(restore);
  useEffect(() => {
    if (mode !== 'demo') return;
    try { sessionStorage.setItem(KEY, JSON.stringify(state)); } catch { /* private browsing / full quota */ }
  }, [state]);
  const reset = useCallback(() => { setState(seed); try { sessionStorage.removeItem(KEY); } catch {} }, []);
  useEffect(() => {
    window.addEventListener('noetaris-identity-cleared', reset);
    return () => window.removeEventListener('noetaris-identity-cleared', reset);
  }, [reset]);
  const selectThread = useCallback(id => setState(s => s.threads.some(t => t.id === id) ? { ...s, activeId: id } : s), []);
  const newThread = useCallback(() => {
    const id = `local-${crypto.randomUUID()}`;
    setState(s => ({ activeId: id, threads: [{ id, title: 'New conversation', ago: 'now', messages: [] }, ...s.threads].slice(0, 100) }));
    return id;
  }, []);
  const appendMessage = useCallback((threadId, message) => setState(s => ({ ...s, threads: s.threads.map(t => t.id === threadId ? {
    ...t, title: t.title === 'New conversation' && message.role === 'user' ? message.text.slice(0, 40) : t.title,
    messages: [...t.messages, message].slice(-300),
  } : t) })), []);
  const value = useMemo(() => ({ ...state, selectThread, newThread, appendMessage, reset }), [state, selectThread, newThread, appendMessage, reset]);
  return <Context.Provider value={value}>{children}</Context.Provider>;
}
export function useConversation() {
  const value = useContext(Context);
  if (!value) throw new Error('ConversationProvider is required');
  return value;
}
