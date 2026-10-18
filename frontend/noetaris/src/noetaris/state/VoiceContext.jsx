import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import useMic from '../hooks/useMic';

// Mounted at the application root: navigating chat → PDF → library does not
// tear down the microphone or discard dictated text. Browser STT is optional.
const VoiceContext = createContext(null);
export function VoiceProvider({ children }) {
  const [draft, setDraft] = useState('');
  const mic = useMic(text => setDraft(d => `${d}${d ? ' ' : ''}${text}`));
  useEffect(() => {
    const clear = () => { mic.stop(); setDraft(''); window.speechSynthesis?.cancel(); };
    window.addEventListener('noetaris-identity-cleared', clear);
    return () => window.removeEventListener('noetaris-identity-cleared', clear);
  }, [mic.stop]);
  const value = useMemo(() => ({ draft, setDraft, mic }), [draft, mic]);
  return <VoiceContext.Provider value={value}>{children}</VoiceContext.Provider>;
}
export function useVoice() {
  const value = useContext(VoiceContext);
  if (!value) throw new Error('VoiceProvider is required');
  return value;
}
