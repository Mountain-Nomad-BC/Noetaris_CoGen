import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Send, Mic, MicOff, Paperclip, StopCircle, Sparkles, FileText, Volume2, History } from "lucide-react";
import { useConversation } from "../../state/ConversationContext";
import { mode, submitChatTurn } from "../../services/api";
import { toast } from "sonner";
import { useVoice } from "../../state/VoiceContext";
import LiveChatPage from './LiveChatPage';

export default function ChatPage() {
  return mode === 'live' ? <LiveChatPage /> : <DemoChatPage />;
}

function DemoChatPage() {
  const { threads, activeId, selectThread, newThread, appendMessage } = useConversation();
  const thread = threads.find((t) => t.id === activeId) || threads[0];
  const messages = thread?.messages || [];
  const pending = useRef(new Map());
  const [busy, setBusy] = useState(false);
  useEffect(() => () => { for (const req of pending.current.values()) req.abort(); pending.current.clear(); window.speechSynthesis?.cancel(); }, []);
  const { draft, setDraft, mic } = useVoice();
  const [speakingId, setSpeakingId] = useState(null);
  const endRef = useRef();
  const nav = useNavigate();
  const tool = (t) => {
    if (t === "Open PDF workspace") return nav("/app/documents/doc-1");
    if (t === "Export transcript") {
      const txt = messages.map((m) => `[${m.role}] ${m.text}`).join("\n\n");
      const url = URL.createObjectURL(new Blob([txt], { type: "text/plain" }));
      const a = document.createElement("a"); a.href = url; a.download = `${thread.title.replace(/[^a-z0-9_-]/gi, '_').slice(0, 48)}.txt`; a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      return;
    }
    setDraft(`${t}: `);
  };

  const listening = mic.state === "listening";

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages.length]);
  const speak = (m) => {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    if (speakingId === m.id) return setSpeakingId(null);
    const u = new SpeechSynthesisUtterance(m.text);
    u.onend = () => setSpeakingId(null);
    setSpeakingId(m.id);
    window.speechSynthesis.speak(u);
  };

  async function send() {
    if (!draft.trim() || busy) return;
    if (listening) mic.stop();
    window.speechSynthesis?.cancel(); setSpeakingId(null);
    const threadId = thread.id;
    const text = draft.trim();
    appendMessage(threadId, { id: crypto.randomUUID(), role: 'user', at: 'now', text });
    setDraft('');
    setBusy(true);
    if (mode === 'demo') {
      appendMessage(threadId, {
        id: crypto.randomUUID(), role: 'assistant', at: 'now',
        text: 'DEMO_FIXTURE — This is an interface preview, not a grounded AI answer. Connect POST /v1/chat and validate the response contract to enable live inference.',
        citations: [],
      });
      setBusy(false);
      return;
    }
    const controller = new AbortController();
    pending.current.set(threadId, controller);
    try {
      const answer = await submitChatTurn({ text, sessionId: threadId, signal: controller.signal });
      appendMessage(threadId, { id: crypto.randomUUID(), role: 'assistant', at: 'now', ...answer });
    } catch (err) {
      if (err.name !== 'AbortError') {
        toast.error(`Chat failed: ${err.message}`);
        appendMessage(threadId, { id: crypto.randomUUID(), role: 'system', at: 'now', text: `Not delivered: ${err.message}` });
      }
    } finally { pending.current.delete(threadId); setBusy(false); }
  }

  return (
    <div className="flex h-[calc(100dvh-64px)] min-h-[380px]" data-testid="chat-page">
      {/* Conversation list */}
      <aside className="w-72 shrink-0 border-r hidden md:flex border-[color:var(--n-stroke-soft)] p-4 flex-col">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-display text-sm uppercase tracking-widest text-[color:var(--n-text-subtle)]">Conversations</h3>
          <button onClick={newThread} className="n-btn-ghost w-7 h-7 flex items-center justify-center text-xs" aria-label="New conversation" data-testid="chat-new-conversation">+</button>
        </div>
        <ul className="space-y-2 overflow-y-auto">
          {threads.map((c)=>(
            <li key={c.id} onClick={()=>selectThread(c.id)} onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); selectThread(c.id); } }} role="button" tabIndex={0} aria-current={c.id===activeId ? "page" : undefined} data-testid={`chat-thread-item-${c.id}`} className={"p-3 rounded-lg cursor-pointer border transition-colors " + (c.id===activeId ? "bg-[rgba(46,155,255,0.08)] border-[rgba(46,155,255,0.25)]" : "border-transparent hover:bg-[rgba(233,239,246,0.03)]")}>
              <div className="text-sm truncate">{c.title}</div>
              <div className="text-[11px] text-[color:var(--n-text-subtle)] mt-1 flex items-center gap-2"><History size={10}/>{c.ago || "now"} · {c.messages.length} msgs</div>
            </li>
          ))}
        </ul>
      </aside>

      {/* Timeline */}
      <div className="flex-1 min-w-0 flex flex-col relative overflow-hidden">
        {/* ribbon behind header */}
        <div className="absolute inset-x-0 top-0 h-24 pointer-events-none opacity-60" style={{
          background:"radial-gradient(500px 100px at 50% 0, rgba(46,155,255,0.18), transparent 70%)"
        }}/>
        <div className="px-7 pt-5 pb-3 flex items-center justify-between relative">
          <div>
            <div className="text-[10px] uppercase tracking-[0.3em] text-[color:var(--n-text-subtle)]">Thread · scoped to current session</div>
            <h2 className="font-display text-2xl" data-testid="chat-thread-title">{thread.title}</h2>
          </div>
          <div className="flex gap-2">
            <span className="n-chip">{mode === "demo" ? "Preview model" : "Backend-selected model"}</span>
            {mode === "demo" && <span className="n-chip-amber n-chip">DEMO_FIXTURE</span>}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-3 md:px-7 pb-36 space-y-5" role="log" aria-live="polite" aria-relevant="additions">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-center pt-24" data-testid="chat-empty-state">
              <Sparkles size={22} className="text-[color:var(--n-cyan)] mb-3"/>
              <div className="font-display text-xl">Start a grounded conversation</div>
              <div className="text-sm text-[color:var(--n-text-mute)] mt-1 max-w-md">Type or use the mic — both land in this same thread with the same citations and scope.</div>
            </div>
          )}
          {messages.map((m) => (
            <div key={m.id} className={"flex gap-3 " + (m.role==="user"?"justify-end":"")} data-testid={`msg-${m.id}`}>
              {m.role!=="user" && <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[color:var(--n-blue)] to-[color:var(--n-violet)] flex items-center justify-center shrink-0"><Sparkles size={14}/></div>}
              <div className={"max-w-[75%] rounded-2xl p-4 text-sm leading-relaxed " + (m.role==="user" ? "bg-[rgba(46,155,255,0.12)] border border-[rgba(46,155,255,0.3)]" : "n-glass")}>
                <div>{m.text}</div>
                {m.citations && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {m.citations.map((c)=>(
                      <div key={c.id} className="n-glass rounded-lg p-2 pr-3 flex items-center gap-2 text-[11px]">
                        <div className="w-6 h-6 rounded-md bg-[rgba(46,155,255,0.15)] flex items-center justify-center text-[10px] font-mono">{c.page}</div>
                        <div>
                          <div className="truncate max-w-[180px]">{c.quote}</div>
                          <div className="text-[color:var(--n-text-subtle)]">p.{c.page} · {c.source}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                <div className="text-[10px] text-[color:var(--n-text-subtle)] mt-2 flex items-center gap-2">
                  {m.at} {m.role!=="user" && <button onClick={()=>speak(m)} className={"flex items-center gap-1 hover:text-[color:var(--n-text)] " + (speakingId===m.id ? "text-[color:var(--n-cyan)]" : "")} data-testid={`msg-playback-${m.id}`}>{speakingId===m.id ? <><StopCircle size={10}/> stop playback</> : <><Volume2 size={10}/> playback (browser TTS)</>}</button>}
                </div>
              </div>
              {m.role==="user" && <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[color:var(--n-cyan)] to-[color:var(--n-blue)] flex items-center justify-center shrink-0 text-[10px] font-semibold text-black">JD</div>}
            </div>
          ))}
          <div ref={endRef}/>
        </div>

        {/* Composer */}
        <div className="absolute bottom-3 left-3 right-3 md:bottom-6 md:left-7 md:right-7">
          <div className="n-glass rounded-2xl p-3 flex items-end gap-3" data-testid="chat-composer">
            <button
              onClick={()=> listening ? mic.stop() : mic.start()}
              className={"shrink-0 w-11 h-11 rounded-xl flex items-center justify-center transition " + (listening ? "bg-[rgba(242,79,97,0.2)] border border-[rgba(242,79,97,0.4)]" : "n-btn-ghost")}
              aria-label="Toggle voice"
              data-testid="chat-mic-btn"
            >
              {listening ? <StopCircle size={16} className="text-[color:var(--n-red)]"/> : <Mic size={16}/>}
            </button>
            <div className="flex-1">
              {listening && (
                <div className="flex items-end gap-0.5 h-6 mb-2" aria-live="polite">
                  {mic.levels.map((v,i)=>(
                    <span key={i} className="w-1 rounded-full" style={{ height: `${Math.max(3, v*24)}px`, background: "linear-gradient(180deg,#5ED6ED,#2E9BFF)" }}/>
                  ))}
                  <span className="text-[11px] text-[color:var(--n-text-subtle)] ml-3 self-center font-mono">
                    {String(Math.floor(mic.elapsed/60)).padStart(2,"0")}:{String(mic.elapsed%60).padStart(2,"0")} · {mic.hasSTT ? (mic.interim ? `draft: “${mic.interim}”` : "Browser speech recognition may use a remote service; do not dictate private data") : "Listening — browser STT unavailable, levels only"}
                  </span>
                </div>
              )}
              {mic.state === "requesting" && <div className="text-[11px] text-[color:var(--n-text-subtle)] mb-2">Requesting microphone permission…</div>}
              {(mic.state === "denied" || mic.state === "unsupported") && (
                <div className="text-[11px] text-[color:var(--n-amber)] mb-2" data-testid="chat-mic-denied">
                  {mic.state === "denied" ? "Microphone permission denied — typing still works in this same thread." : "Microphone not supported in this browser."}
                </div>
              )}
              <textarea
                value={draft}
                onChange={(e)=>setDraft(e.target.value)}
                onKeyDown={(e)=>{ if (e.key==="Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
                rows={1}
                placeholder="Message Noetaris — Enter to send, Shift+Enter for newline"
                className="w-full bg-transparent outline-none resize-none text-sm placeholder:text-[color:var(--n-text-subtle)]"
                data-testid="chat-input"
              />
            </div>
            <button onClick={() => toast.message('Attachment needs the /v1/files integration; use Library for existing demo documents.')} className="n-btn-ghost w-11 h-11 rounded-xl flex items-center justify-center" aria-label="Attach (backend pending)"><Paperclip size={16}/></button>
            <button onClick={send} disabled={busy || !draft.trim()} className="n-cta h-11 px-4 rounded-xl flex items-center gap-2 text-sm disabled:opacity-50" data-testid="chat-send-btn">
              <Send size={14}/> Send
            </button>
          </div>
        </div>
      </div>

      {/* Right rail: scope / tools */}
      <aside className="w-80 shrink-0 border-l border-[color:var(--n-stroke-soft)] p-5 overflow-y-auto hidden xl:block">
        <div className="text-[10px] uppercase tracking-[0.25em] text-[color:var(--n-text-subtle)] mb-2">Context scope</div>
        <div className="n-glass rounded-xl p-3 mb-5">
          <div className="text-sm flex items-center gap-2"><FileText size={14}/> DEMO_FIXTURE_rack_guide.pdf</div>
          <div className="text-[11px] text-[color:var(--n-text-subtle)] mt-1">Revision 4 · 12 pages indexed · OCR 92%</div>
        </div>
        <div className="text-[10px] uppercase tracking-[0.25em] text-[color:var(--n-text-subtle)] mb-2">Tools</div>
        <ul className="space-y-2 text-sm">
          {["Summarize","Compare evidence","Find contradictions","Export transcript","Open PDF workspace"].map((t)=>(
            <li key={t}><button type="button" onClick={()=>tool(t)} data-testid={`chat-tool-${t.toLowerCase().replace(/ /g,'-')}`} className="w-full text-left p-2.5 rounded-lg hover:bg-[rgba(233,239,246,0.03)] flex items-center gap-2">
              <Sparkles size={12} className="text-[color:var(--n-cyan)]"/> {t}
            </button></li>
          ))}
        </ul>
      </aside>
    </div>
  );
}
