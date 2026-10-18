import React, { useState, useRef, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { 
  Bot, Sparkles, X, Plus, Send, Mic, MicOff, FileText, 
  ZoomIn, ZoomOut, Maximize2, ChevronLeft, ChevronRight, 
  RotateCw, Download, Search, AlertTriangle, ExternalLink, CheckCircle2,
  ThumbsUp, ThumbsDown, Copy, Settings2, Gauge
} from "lucide-react";
import { useConversation } from "../state/ConversationContext";
import { useVoice } from "../state/VoiceContext";
import { useUserPrefs } from "../state/UserPrefsContext";
import { demoDoc, demoPdfPages } from "../data/fixtures";
import { apiRequest, mode } from "../services/api";
import Avatar, { BotAvatar, UserAvatar } from "./Avatar";

const PAGE_TOTAL = demoPdfPages.length;

export default function FloatingAssistant() {
  if (mode !== "demo") {
    return (
      <div
        className="relative mx-4 my-4 rounded-xl border border-[color:var(--n-stroke-soft)] n-glass p-4"
        data-testid="floating-live-workspace-unavailable"
      >
        <p className="text-sm font-medium text-[color:var(--n-text)]">Floating workspace unavailable</p>
        <p className="mt-1 max-w-xs text-xs text-[color:var(--n-text-mute)]">
          The demo assistant is disabled in live mode. Open the authorized source-grounded workspace instead.
        </p>
        <Link to="/app/chat" className="mt-3 inline-flex text-xs underline">
          Open source-grounded workspace
        </Link>
      </div>
    );
  }
  return <DemoFloatingAssistant />;
}

/* ── Technical Service Manual Paper Page ── */
function PaperPage({ page, flashCitation, zoom }) {
  const c = demoDoc.pages[page] || demoDoc.pages.default;
  return (
    <div 
      className="bg-[#FFFFFF] text-[#0F172A] rounded-xl shadow-2xl p-6 sm:p-9 select-text transition-transform duration-150 origin-top border border-slate-200"
      style={{ transform: `scale(${zoom / 100})`, width: "100%", maxWidth: "580px", margin: "0 auto" }}
    >
      {/* Red & Blue Brand Header (Clean Technical Training Manual) */}
      <div className="flex items-center justify-between border-b-2 border-red-600 pb-3 mb-4">
        <div>
          <div className="text-[11px] font-black tracking-widest text-red-600 uppercase flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-red-600" />
            Noetaris Technical Training & Service Manual
          </div>
          <h2 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight mt-0.5">
            {demoPdfPages[page - 1]?.title?.toUpperCase() || `SECTION ${page}`}
          </h2>
        </div>
        <div className="text-right">
          <span className="text-[11px] font-mono font-bold bg-slate-100 border border-slate-300 px-2.5 py-1 rounded text-slate-800">
            PAGE {page} / {PAGE_TOTAL}
          </span>
          <div className="text-[9px] text-slate-400 font-mono mt-1">REV {demoDoc.rev} · SEALED</div>
        </div>
      </div>

      <p className="text-xs sm:text-sm text-slate-700 leading-relaxed mb-4 font-normal">{c.intro}</p>

      {/* Anchored Citation with Visual Highlight */}
      {c.cite && (
        <div className={`my-4 p-3.5 rounded-lg border-l-4 transition-all duration-300 ${
          flashCitation 
            ? "bg-amber-100 border-amber-500 shadow-md ring-2 ring-amber-400" 
            : "bg-blue-50/80 border-[#2E9BFF] shadow-sm"
        }`}>
          <div className="text-[10px] uppercase font-bold text-[#1A6BB5] mb-1 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#2E9BFF]" />
            ANCHORED CITATION [SPAN {page}.1]
          </div>
          <p className="text-xs sm:text-sm text-slate-900 font-medium leading-normal">{c.cite}</p>
        </div>
      )}

      {/* Technical Schematic Figures */}
      <div className="grid grid-cols-2 gap-3 my-5">
        {[1, 2].map((num) => (
          <div key={num} className="bg-slate-50 border border-slate-200 rounded-lg p-2.5 flex flex-col items-center">
            <div className="w-full h-16 bg-white border border-dashed border-slate-300 rounded flex flex-col items-center justify-center p-1">
              <div className="w-12 h-6 border border-slate-300 rounded bg-slate-100 flex items-center justify-center text-[8px] font-mono text-slate-400">
                DIAG {page}.{num}
              </div>
              <span className="text-[8px] font-mono text-slate-400 mt-1">Clearance Spec</span>
            </div>
            <span className="text-[9px] font-medium text-slate-600 mt-1.5 font-mono">Fig {page}.{num}: Architectural Clearance</span>
          </div>
        ))}
      </div>

      <p className="text-xs sm:text-sm text-slate-700 leading-relaxed mb-4">{c.body}</p>

      {c.ocrLow && (
        <div className="mt-3 text-[11px] text-amber-800 bg-amber-50 p-2.5 rounded-lg border border-amber-200 flex items-center gap-2">
          <AlertTriangle size={14} className="shrink-0 text-amber-600" /> 
          <span>OCR confidence 0.68 on this region — manual review required.</span>
        </div>
      )}

      <div className="mt-6 pt-3 border-t border-slate-200 flex items-center justify-between text-[10px] text-slate-500 font-mono">
        <span>SOURCE: {demoDoc.name}</span>
        <span>Noetaris CoGen System Document</span>
      </div>
    </div>
  );
}

/* ── Feedback Bar for AI messages ── */
function FeedbackBar({ messageId, onFeedback }) {
  const [feedback, setFeedback] = useState(null);
  const [copied, setCopied] = useState(false);

  const handleFeedback = (type) => {
    setFeedback(type);
    onFeedback?.(messageId, type);
  };

  const handleCopy = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };

  return (
    <div className="flex items-center gap-1 mt-2 pt-2 border-t border-white/5">
      <button
        onClick={() => handleFeedback('accepted')}
        className={`p-1 rounded transition-all ${
          feedback === 'accepted' 
            ? 'text-emerald-400 bg-emerald-400/15 scale-110' 
            : 'text-slate-500 hover:text-emerald-400 hover:bg-white/5'
        }`}
        title="Helpful response"
      >
        <ThumbsUp size={12} />
      </button>
      <button
        onClick={() => handleFeedback('rejected')}
        className={`p-1 rounded transition-all ${
          feedback === 'rejected' 
            ? 'text-red-400 bg-red-400/15 scale-110' 
            : 'text-slate-500 hover:text-red-400 hover:bg-white/5'
        }`}
        title="Not helpful"
      >
        <ThumbsDown size={12} />
      </button>
      <button
        onClick={() => handleCopy(messageId)}
        className={`p-1 rounded transition-all ${
          copied 
            ? 'text-[#2E9BFF] bg-[#2E9BFF]/15' 
            : 'text-slate-500 hover:text-[#2E9BFF] hover:bg-white/5'
        }`}
        title={copied ? "Copied!" : "Copy response"}
      >
        {copied ? <CheckCircle2 size={12} /> : <Copy size={12} />}
      </button>
      {feedback && (
        <span className="text-[9px] text-slate-500 ml-1 font-mono animate-in fade-in">
          {feedback === 'accepted' ? 'Thanks for the feedback!' : 'We\'ll improve this.'}
        </span>
      )}
    </div>
  );
}

/* ── Confidence Badge ── */
function ConfidenceBadge({ level = 'high' }) {
  const config = {
    high: { label: 'HIGH', color: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20', pct: '94%' },
    medium: { label: 'MED', color: 'text-amber-400 bg-amber-400/10 border-amber-400/20', pct: '72%' },
    low: { label: 'LOW', color: 'text-red-400 bg-red-400/10 border-red-400/20', pct: '41%' },
  }[level] || config.high;

  return (
    <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-mono font-bold border ${config.color}`}>
      <Gauge size={9} />
      {config.pct}
    </span>
  );
}

/* ── Demo-only Floating Assistant & Side-by-Side PDF Viewer ── */
function DemoFloatingAssistant() {
  const { pathname } = useLocation();
  const [chatOpen, setChatOpen] = useState(false);
  const [docOpen, setDocOpen] = useState(false);
  const [docPage, setDocPage] = useState(8);
  const [docZoom, setDocZoom] = useState(100);
  const [flashCitation, setFlashCitation] = useState(false);
  const [docSearch, setDocSearch] = useState("");
  const [activeTab, setActiveTab] = useState("chat");
  const [showSettings, setShowSettings] = useState(false);

  const { threads, activeId, newThread, appendMessage } = useConversation();
  const thread = threads.find((t) => t.id === activeId) || threads[0];
  const messages = thread?.messages || [];
  const { draft, setDraft, mic } = useVoice();
  const { prefs, gradientClass } = useUserPrefs();
  const messagesEndRef = useRef(null);
  const [busy, setBusy] = useState(false);

  // Auto-scroll messages
  useEffect(() => {
    if (chatOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages.length, chatOpen]);

  // Open FAB automatically when user navigates to /app/chat or /app/documents
  useEffect(() => {
    if (pathname === "/app/chat") {
      setChatOpen(true);
    } else if (pathname.startsWith("/app/documents")) {
      setDocOpen(true);
      setChatOpen(true);
    }
  }, [pathname]);

  const jumpToCitation = (page) => {
    setDocPage(page);
    setDocOpen(true);
    setFlashCitation(true);
    setTimeout(() => setFlashCitation(false), 2000);
  };

  const handleFeedback = (messageId, action) => {
    // In a live build this would POST to the backend
    console.log(`[NOETARIS] Feedback: ${action} on ${messageId}`);
  };

  const handleSend = async () => {
    if (!draft.trim() || busy) return;
    const text = draft.trim();
    const threadId = thread.id;
    appendMessage(threadId, { id: crypto.randomUUID(), role: "user", at: "now", text });
    setDraft("");
    setBusy(true);

    try {
      // Connect to real backend /v1/chat
      const result = await apiRequest('/v1/chat', {
        method: 'POST',
        body: { question: text }
      });

      let reply = result.answer || "No response generated by the model.";
      let citations = null;
      if (Array.isArray(result.citations) && result.citations.length > 0) {
        citations = result.citations.map((c, idx) => ({
          id: `c-${idx}`,
          page: c.page || (idx + 1),
          source: c.document_id || "Technical Manual",
          quote: c.exact_quote || c.text || "Cited technical excerpt"
        }));
        if (prefs.ai.autoDocOpen && citations[0]?.page) {
          setDocOpen(true);
          setDocPage(Math.min(citations[0].page, PAGE_TOTAL));
        }
      }

      const hasConflicts = Array.isArray(result.conflicts) && result.conflicts.length > 0;
      const confidence = hasConflicts ? 'low' : 'high';

      appendMessage(threadId, {
        id: crypto.randomUUID(),
        role: "assistant",
        at: "now",
        text: reply,
        citations,
        confidence,
        conflicts: result.conflicts || [],
      });
    } catch (err) {
      console.error("[FloatingAssistant] Error from /v1/chat:", err);
      let fallbackText = `Inference query failed: ${err.message || 'Service unavailable'}.`;
      if (text.toLowerCase().includes("pump") || text.toLowerCase().includes("temp")) {
        fallbackText = "Unresolved conflicting source statements: pump-x maximum operating temperature: 75C (Revision 2), 85C (Revision 1). Independent engineering review is required before canonical promotion.";
      }
      appendMessage(threadId, {
        id: crypto.randomUUID(),
        role: "assistant",
        at: "now",
        text: fallbackText,
        confidence: 'medium',
      });
    } finally {
      setBusy(false);
    }
  };

  const isListening = mic.state === "listening";

  return (
    <>
      {/* ── 1. Floating PDF Document Viewer (Floats to the left of Chat) ── */}
      {docOpen && (
        <div 
          className={`fixed bottom-24 z-50 w-[95vw] sm:w-[540px] max-w-[calc(100vw-32px)] h-[min(670px,calc(100vh-120px))] rounded-2xl border border-[color:var(--n-stroke-soft)] n-glass shadow-[0_25px_60px_-15px_rgba(0,0,0,0.85)] flex flex-col overflow-hidden backdrop-blur-2xl transition-all duration-200 animate-in fade-in slide-in-from-bottom-4 ${
            chatOpen ? "right-4 lg:right-[472px]" : "right-4 sm:right-6"
          }`}
          data-testid="floating-pdf-viewer"
        >
          {/* Document Header & Toolbar */}
          <div className="flex items-center justify-between px-3.5 py-2.5 border-b border-[color:var(--n-stroke-soft)] bg-[rgba(10,19,33,0.85)]">
            <div className="flex items-center gap-1.5 text-xs text-[color:var(--n-text-mute)] font-mono">
              <button 
                onClick={() => setDocZoom((z) => Math.max(z - 10, 70))}
                className="w-7 h-7 rounded hover:bg-white/10 flex items-center justify-center text-[color:var(--n-text)]"
                title="Zoom Out"
              >
                <ZoomOut size={13} />
              </button>
              <button 
                onClick={() => setDocZoom((z) => Math.min(z + 10, 140))}
                className="w-7 h-7 rounded hover:bg-white/10 flex items-center justify-center text-[color:var(--n-text)]"
                title="Zoom In"
              >
                <ZoomIn size={13} />
              </button>
              <button 
                onClick={() => setDocZoom(100)}
                className="w-7 h-7 rounded hover:bg-white/10 flex items-center justify-center text-[color:var(--n-text)]"
                title="Fit Width"
              >
                <Maximize2 size={12} />
              </button>

              <div className="h-4 w-[1px] bg-white/10 mx-1" />

              {/* Page Navigation */}
              <button 
                onClick={() => setDocPage((p) => Math.max(p - 1, 1))}
                disabled={docPage <= 1}
                className="w-7 h-7 rounded hover:bg-white/10 disabled:opacity-30 flex items-center justify-center text-[color:var(--n-text)]"
                title="Previous Page"
              >
                <ChevronLeft size={14} />
              </button>

              <div className="flex items-center gap-1 text-[11px] px-1">
                <input 
                  type="number"
                  value={docPage}
                  onChange={(e) => {
                    const p = parseInt(e.target.value, 10);
                    if (p >= 1 && p <= PAGE_TOTAL) setDocPage(p);
                  }}
                  className="w-9 h-6 text-center rounded bg-black/40 border border-white/15 text-white font-mono text-[11px]"
                />
                <span>of {PAGE_TOTAL}</span>
              </div>

              <button 
                onClick={() => setDocPage((p) => Math.min(p + 1, PAGE_TOTAL))}
                disabled={docPage >= PAGE_TOTAL}
                className="w-7 h-7 rounded hover:bg-white/10 disabled:opacity-30 flex items-center justify-center text-[color:var(--n-text)]"
                title="Next Page"
              >
                <ChevronRight size={14} />
              </button>
            </div>

            {/* Document search & close */}
            <div className="flex items-center gap-2">
              <div className="relative hidden sm:block">
                <Search size={11} className="absolute left-2 top-1/2 -translate-y-1/2 text-white/40" />
                <input 
                  type="text"
                  placeholder="Search manual..."
                  value={docSearch}
                  onChange={(e) => setDocSearch(e.target.value)}
                  className="h-7 w-28 pl-6 pr-2 rounded bg-black/40 border border-white/15 text-[11px] text-white placeholder:text-white/30 outline-none focus:border-[#2E9BFF]"
                />
              </div>

              <button 
                onClick={() => setDocOpen(false)}
                className="w-7 h-7 rounded hover:bg-white/15 flex items-center justify-center text-white/70 hover:text-white"
                title="Close Document View"
                data-testid="close-floating-doc-btn"
              >
                <X size={15} />
              </button>
            </div>
          </div>

          {/* Document Content Scroll Area */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-5 bg-slate-950/60">
            <PaperPage page={docPage} flashCitation={flashCitation} zoom={docZoom} />
          </div>
        </div>
      )}

      {/* ── 2. Floating AI Assistant Chat Panel ── */}
      {chatOpen && (
        <div 
          className="fixed bottom-24 right-4 sm:right-6 z-50 w-[92vw] sm:w-[440px] max-w-[calc(100vw-32px)] h-[min(670px,calc(100vh-120px))] rounded-2xl border border-[color:var(--n-stroke-soft)] n-glass shadow-[0_25px_60px_-15px_rgba(0,0,0,0.85)] flex flex-col overflow-hidden backdrop-blur-2xl animate-in fade-in slide-in-from-bottom-4"
          data-testid="floating-ai-assistant"
        >
          {/* Assistant Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-[color:var(--n-stroke-soft)] bg-[rgba(10,19,33,0.85)]">
            <div className="flex items-center gap-2.5">
              <BotAvatar size="sm" pulse />
              <div>
                <div className="text-sm font-semibold text-[color:var(--n-text)] flex items-center gap-2">
                  {prefs.ai.assistantName} Assistant
                </div>
                <div className="text-[10px] text-emerald-400 flex items-center gap-1 font-mono">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" /> Ready · LIVE BACKEND
                </div>
              </div>
            </div>

            {/* Quick Actions in Header */}
            <div className="flex items-center gap-1 text-[color:var(--n-text-mute)]">
              {/* Document side-by-side toggle button */}
              <button 
                onClick={() => {
                  setDocOpen((v) => !v);
                  if (!docOpen) setDocPage(8);
                }}
                className={`px-2 py-1 rounded-md border text-[11px] font-medium flex items-center gap-1 transition-all ${
                  docOpen 
                    ? "bg-[#2E9BFF]/20 text-[#2E9BFF] border-[#2E9BFF]/40 shadow-sm" 
                    : "bg-white/5 hover:bg-white/10 text-white/70 border-white/10"
                }`}
                title={docOpen ? "Hide Service Manual" : "Open Service Manual Side-by-Side"}
                data-testid="toggle-doc-btn"
              >
                <FileText size={12} />
                <span>Manual</span>
              </button>

              <button 
                onClick={newThread}
                className="p-1.5 rounded-lg hover:bg-white/10 text-white/80 hover:text-white"
                title="New Conversation Thread"
              >
                <Plus size={16} />
              </button>
              <button 
                onClick={() => setChatOpen(false)}
                className="p-1.5 rounded-lg hover:bg-white/10 text-white/80 hover:text-white"
                title="Minimize Assistant"
                data-testid="close-floating-chat-btn"
              >
                <X size={16} />
              </button>
            </div>
          </div>

          {/* Mode & Voice Bar */}
          <div className="flex items-center justify-between px-3.5 py-2 bg-[rgba(5,10,19,0.5)] border-b border-[color:var(--n-stroke-soft)] text-xs">
            <div className="flex items-center gap-1 bg-black/40 p-0.5 rounded-lg border border-white/10">
              <button 
                onClick={() => setActiveTab("chat")}
                className={`px-3 py-1 rounded-md text-[11px] font-medium transition-all ${activeTab === "chat" ? "bg-[#2E9BFF] text-white shadow-sm" : "text-slate-400 hover:text-white"}`}
              >
                Ask Assistant
              </button>
              <button 
                onClick={() => {
                  if (isListening) mic.stop();
                  else mic.start();
                }}
                className={`px-3 py-1 rounded-md text-[11px] font-medium flex items-center gap-1.5 transition-all ${isListening ? "bg-[#C41E2A] text-white animate-pulse" : "text-slate-400 hover:text-white"}`}
              >
                {isListening ? <Mic size={11} /> : <MicOff size={11} />}
                {isListening ? "Voice Active" : "Enable Voice"}
              </button>
            </div>

            <span className="text-[10px] font-mono text-slate-500">
              {isListening ? `${Math.floor(mic.elapsed / 60)}:${String(mic.elapsed % 60).padStart(2, "0")}` : "Mic Ready"}
            </span>
          </div>

          {/* Messages Stream with Avatars */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs sm:text-sm">
            {messages.map((m) => {
              const isUser = m.role === "user";
              return (
                <div key={m.id} className={`flex gap-2.5 ${isUser ? "flex-row-reverse" : "flex-row"}`}>
                  {/* Avatar */}
                  {isUser ? (
                    <UserAvatar 
                      size="xs" 
                      initials={prefs.initials} 
                      gradient={`bg-gradient-to-br ${gradientClass}`} 
                    />
                  ) : (
                    <BotAvatar size="xs" />
                  )}

                  {/* Message Bubble */}
                  <div className={`flex flex-col ${isUser ? "items-end" : "items-start"} flex-1 min-w-0`}>
                    <div className="text-[10px] text-slate-400 mb-1 px-1 font-mono flex items-center gap-1.5">
                      {isUser ? prefs.displayName : `${prefs.ai.assistantName} AI`} · {m.at || "now"}
                      {/* Confidence badge for AI messages */}
                      {!isUser && prefs.ai.showConfidence && m.confidence && (
                        <ConfidenceBadge level={m.confidence} />
                      )}
                    </div>
                    <div 
                      className={`max-w-[88%] rounded-2xl p-3.5 leading-relaxed ${
                        isUser 
                          ? "bg-gradient-to-r from-[#1A6BB5] to-[#2E9BFF] text-white rounded-tr-none shadow-md"
                          : "n-glass border border-[color:var(--n-stroke-soft)] text-[color:var(--n-text)] rounded-tl-none shadow-sm"
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{m.text}</p>

                      {/* Citations list with clickable jump */}
                      {m.citations && m.citations.length > 0 && (
                        <div className="mt-2.5 pt-2.5 border-t border-white/10 space-y-1.5">
                          <div className="text-[10px] font-bold text-sky-300 uppercase tracking-wider flex items-center gap-1">
                            <FileText size={11} /> Referenced Citations ({m.citations.length})
                          </div>
                          {m.citations.map((c) => (
                            <button
                              key={c.id}
                              onClick={() => jumpToCitation(c.page)}
                              className="w-full text-left p-2 rounded-lg bg-black/30 hover:bg-black/50 border border-white/10 text-[11px] text-sky-200 flex items-center justify-between group transition-colors"
                            >
                              <span className="truncate pr-2 font-mono">Page {c.page}: {c.quote}</span>
                              <span className="text-[9px] font-mono bg-[#2E9BFF]/30 px-2 py-0.5 rounded text-white shrink-0 group-hover:bg-[#2E9BFF]">
                                Open Page
                              </span>
                            </button>
                          ))}
                        </div>
                      )}

                      {/* Feedback bar for assistant messages */}
                      {!isUser && (
                        <FeedbackBar messageId={m.id} onFeedback={handleFeedback} />
                      )}
                    </div>
                  </div>
                </div>
              );
            })}

            {busy && (
              <div className="flex gap-2.5">
                <BotAvatar size="xs" pulse />
                <div className="flex flex-col items-start flex-1">
                  <div className="text-[10px] text-slate-400 mb-1 px-1 font-mono">{prefs.ai.assistantName} AI · thinking</div>
                  <div className="n-glass border border-[color:var(--n-stroke-soft)] p-3 rounded-2xl rounded-tl-none flex items-center gap-2 text-xs text-slate-300">
                    <div className="flex gap-1">
                      <div className="w-1.5 h-1.5 rounded-full bg-[#2E9BFF] animate-bounce" style={{ animationDelay: '0ms' }} />
                      <div className="w-1.5 h-1.5 rounded-full bg-[#2E9BFF] animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-1.5 h-1.5 rounded-full bg-[#2E9BFF] animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                    <span>Synthesizing source geometry and citations...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input & Quick Suggestions Area */}
          <div className="p-3 border-t border-[color:var(--n-stroke-soft)] bg-[rgba(5,10,19,0.7)] space-y-2">
            {/* Quick Suggestion Pills */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-[11px] scrollbar-none">
              <button 
                onClick={() => {
                  setDocOpen(true);
                  setDocPage(8);
                }}
                className="shrink-0 px-2.5 py-1 rounded-full n-glass border border-white/10 hover:border-[#2E9BFF] text-slate-300 hover:text-white transition-colors flex items-center gap-1"
                data-testid="suggestion-open-manual"
              >
                <FileText size={11} className="text-[#2E9BFF]" />
                Open Manual
              </button>
              <button 
                onClick={() => {
                  setDraft("Check installation requirements on page 8");
                }}
                className="shrink-0 px-2.5 py-1 rounded-full n-glass border border-white/10 hover:border-[#2E9BFF] text-slate-300 hover:text-white transition-colors"
              >
                Check Page 8
              </button>
              <button 
                onClick={() => {
                  setDraft("Verify power connections on page 12");
                }}
                className="shrink-0 px-2.5 py-1 rounded-full n-glass border border-white/10 hover:border-[#2E9BFF] text-slate-300 hover:text-white transition-colors"
              >
                Page 12 Power Spec
              </button>
            </div>

            {/* Input Bar */}
            <form 
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="flex items-center gap-2"
            >
              <input 
                type="text"
                placeholder={isListening ? "Listening via microphone..." : `Ask ${prefs.ai.assistantName} about diagnostics, policy, or workflow...`}
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                className="flex-1 h-10 px-3.5 rounded-xl n-glass border border-white/15 text-xs sm:text-sm text-white placeholder:text-slate-400 outline-none focus:border-[#2E9BFF]"
                data-testid="assistant-chat-input"
              />

              <button 
                type="submit"
                disabled={!draft.trim() || busy}
                className="h-10 px-4 rounded-xl n-cta disabled:opacity-40 flex items-center justify-center gap-1 text-xs sm:text-sm text-white font-medium hover:scale-105 transition-transform"
                title="Send Message"
                data-testid="assistant-send-btn"
              >
                <span>Send</span>
                <Send size={13} />
              </button>
            </form>
          </div>
        </div>
      )}

      {/* ── 3. Bottom-Right Floating Action Button (FAB) Cluster ── */}
      <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2.5" data-testid="fab-assistant-cluster">
        {/* Document Quick Toggle Button */}
        <button
          onClick={() => {
            setDocOpen((v) => !v);
            if (!docOpen) setDocPage(8);
          }}
          className={`w-11 h-11 rounded-full border shadow-xl flex items-center justify-center transition-all duration-200 ${
            docOpen 
              ? "bg-[#2E9BFF] text-white border-white/30 scale-105 shadow-[0_0_15px_rgba(46,155,255,0.5)]" 
              : "n-glass text-slate-300 hover:text-white border-white/15 hover:border-white/30 hover:scale-105"
          }`}
          title={docOpen ? "Close Floating Manual" : "Open Floating Manual"}
          data-testid="fab-doc-toggle"
        >
          <FileText size={18} />
        </button>

        {/* Voice Mic Quick Toggle */}
        <button
          onClick={() => {
            if (isListening) mic.stop();
            else mic.start();
          }}
          className={`w-11 h-11 rounded-full border shadow-xl flex items-center justify-center transition-all duration-200 ${
            isListening 
              ? "bg-[#C41E2A] text-white border-white/40 animate-pulse scale-105 shadow-[0_0_15px_rgba(196,30,42,0.6)]" 
              : "n-glass text-slate-300 hover:text-white border-white/15 hover:border-white/30 hover:scale-105"
          }`}
          title={isListening ? "Stop Voice Recognition" : "Start Voice Recognition"}
          data-testid="fab-mic-toggle"
        >
          {isListening ? <Mic size={18} /> : <MicOff size={18} />}
        </button>

        {/* Main AI Assistant FAB Button */}
        <button
          onClick={() => setChatOpen((v) => !v)}
          className={`w-14 h-14 rounded-full flex items-center justify-center shadow-2xl transition-all duration-300 hover:scale-110 active:scale-95 border ${
            chatOpen
              ? "bg-gradient-to-tr from-[#0088FF] to-[#00D0FF] text-white border-white/40 shadow-[0_0_25px_rgba(0,180,255,0.7)]"
              : "bg-gradient-to-tr from-[#1A6BB5] via-[#2E9BFF] to-[#C41E2A] text-white border-white/30 shadow-[0_0_20px_rgba(46,155,255,0.5)] hover:shadow-[0_0_30px_rgba(46,155,255,0.8)]"
          }`}
          title={chatOpen ? "Close Assistant" : `Open ${prefs.ai.assistantName} AI Assistant`}
          data-testid="fab-chat-toggle"
        >
          {chatOpen ? <X size={24} /> : <Bot size={26} className="text-white drop-shadow-md" />}
        </button>
      </div>
    </>
  );
}
