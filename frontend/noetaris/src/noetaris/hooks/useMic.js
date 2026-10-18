import { useEffect, useRef, useState } from 'react';
import { mode } from '../services/api';

// Browser-only audio visualizer + optional browser speech recognition.
// IMPORTANT: browser SpeechRecognition can involve a remote provider. Do not
// use it for confidential documents without explicit product privacy policy.
const BARS = 20;
const emptyLevels = () => Array(BARS).fill(0);
export default function useMic(onFinal) {
  const [state, setState] = useState('idle');
  const [levels, setLevels] = useState(emptyLevels);
  const [interim, setInterim] = useState('');
  const [elapsed, setElapsed] = useState(0);
  const data = useRef({});
  const finalRef = useRef(onFinal);
  finalRef.current = onFinal;
  const token = useRef(0);
  const alive = useRef(true);

  const cleanup = () => {
    const { raf, stream, ctx, rec, timer } = data.current;
    cancelAnimationFrame(raf); clearInterval(timer);
    try { rec?.abort(); } catch { /* recognition already ended */ }
    stream?.getTracks().forEach(track => track.stop());
    ctx?.close().catch(() => {});
    data.current = {};
  };
  const stop = () => {
    token.current++;
    cleanup();
    if (!alive.current) return;
    setLevels(emptyLevels()); setInterim(''); setElapsed(0); setState('idle');
  };
  const start = async () => {
    if (state === 'listening' || state === 'requesting') return;
    if (!navigator.mediaDevices?.getUserMedia || !(window.AudioContext || window.webkitAudioContext)) {
      setState('unsupported'); return;
    }
    const request = ++token.current;
    setState('requesting');
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      if (!alive.current || token.current !== request) {
        stream.getTracks().forEach(track => track.stop()); return;
      }
      const Context = window.AudioContext || window.webkitAudioContext;
      const ctx = new Context();
      const an = ctx.createAnalyser(); an.fftSize = 64;
      ctx.createMediaStreamSource(stream).connect(an);
      const buf = new Uint8Array(an.frequencyBinCount);
      const current = { stream, ctx, raf: 0, timer: setInterval(() => setElapsed(t => t + 1), 1000), rec: null };
      data.current = current;
      let last = 0;
      const sample = (now) => {
        if (!alive.current || token.current !== request) return;
        if (now - last > 80) {
          an.getByteFrequencyData(buf);
          setLevels(Array.from(buf.slice(0, BARS), v => v / 255));
          last = now;
        }
        current.raf = requestAnimationFrame(sample);
      };
      current.raf = requestAnimationFrame(sample);
      const SR = mode === 'demo' ? window.SpeechRecognition || window.webkitSpeechRecognition : null;
      if (SR) {
        const rec = new SR(); rec.interimResults = true; rec.continuous = true;
        rec.onresult = e => {
          if (!alive.current || token.current !== request) return;
          let finalText = '', draft = '';
          for (let i = e.resultIndex; i < e.results.length; i++) {
            if (e.results[i].isFinal) finalText += e.results[i][0].transcript;
            else draft += e.results[i][0].transcript;
          }
          setInterim(draft);
          if (finalText.trim()) finalRef.current?.(finalText.trim());
        };
        rec.onerror = () => { /* audio levels still work; user can type */ };
        try { rec.start(); current.rec = rec; } catch { /* speech backend unavailable */ }
      }
      setState('listening');
    } catch (err) {
      stream?.getTracks().forEach(track => track.stop());
      if (alive.current && token.current === request) { cleanup(); setState(err.name === 'NotAllowedError' ? 'denied' : 'unsupported'); }
    }
  };
  useEffect(() => { alive.current = true; return () => { alive.current = false; token.current++; cleanup(); }; }, []);
  return { state, levels, interim, elapsed, start, stop, hasSTT: mode === 'demo' && !!(window.SpeechRecognition || window.webkitSpeechRecognition) };
}
