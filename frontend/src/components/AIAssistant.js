import { useState, useRef, useEffect } from "react";
import { Bot, X, Mic, Send, Loader2, Sparkles, MicOff, Volume2 } from "lucide-react";
import { askAssistant } from "@/lib/api";

const URGENCY = {
  low: "text-[hsl(var(--lx-green))]",
  medium: "text-primary",
  high: "text-[hsl(var(--destructive))]",
};

export const AIAssistant = () => {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([]); // {role, text, recs}
  const [listening, setListening] = useState(false);
  const recognitionRef = useRef(null);
  const endRef = useRef(null);
  const voiceSupported = typeof window !== "undefined" && (window.SpeechRecognition || window.webkitSpeechRecognition);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);

  useEffect(() => {
    const open = () => setOpen(true);
    window.addEventListener("listrix:open-assistant", open);
    return () => window.removeEventListener("listrix:open-assistant", open);
  }, []);

  const speak = (text) => {
    try {
      if (window.speechSynthesis && text) {
        const u = new SpeechSynthesisUtterance(text);
        u.rate = 1.05; window.speechSynthesis.cancel(); window.speechSynthesis.speak(u);
      }
    } catch {}
  };

  const send = async (text, isVoice = false) => {
    const q = (text ?? query).trim();
    if (!q) return;
    setMessages((m) => [...m, { role: "user", text: q }]);
    setQuery("");
    setLoading(true);
    try {
      const res = await askAssistant({ query: q, voice: isVoice });
      setMessages((m) => [...m, { role: "ai", text: res.answer, recs: res.recommendations || [] }]);
      if (isVoice) speak(res.answer);
    } catch {
      setMessages((m) => [...m, { role: "ai", text: "Sorry, I couldn't process that right now.", recs: [] }]);
    } finally {
      setLoading(false);
    }
  };

  const toggleVoice = () => {
    if (!voiceSupported) return;
    if (listening) { recognitionRef.current?.stop(); return; }
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    const rec = new SR();
    rec.lang = "en-US"; rec.interimResults = false; rec.maxAlternatives = 1;
    rec.onresult = (e) => { const t = e.results[0][0].transcript; setListening(false); send(t, true); };
    rec.onend = () => setListening(false);
    rec.onerror = () => setListening(false);
    recognitionRef.current = rec;
    setListening(true);
    rec.start();
  };

  return (
    <>
      {!open && (
        <button data-testid="assistant-open-button" onClick={() => setOpen(true)}
          className="fixed bottom-24 right-6 z-[60] flex h-14 w-14 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-orangeGlowStrong transition-transform hover:scale-105 active:scale-95">
          <Bot size={24} />
        </button>
      )}
      {open && (
        <div data-testid="assistant-panel" className="fixed bottom-24 right-6 z-[60] flex h-[540px] w-[380px] max-w-[calc(100vw-2rem)] flex-col overflow-hidden rounded-2xl border border-border bg-card shadow-panel">
          <div className="flex items-center justify-between border-b border-border bg-card/80 px-4 py-3">
            <div className="flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground"><Bot size={16} /></span>
              <div><p className="text-sm font-semibold">Live AI Assistant</p><p className="text-[11px] text-muted-foreground">Marketing intelligence · approval required</p></div>
            </div>
            <button data-testid="assistant-close-button" onClick={() => setOpen(false)} className="text-muted-foreground hover:text-foreground"><X size={18} /></button>
          </div>

          <div className="flex-1 space-y-3 overflow-y-auto p-4 lx-scroll">
            {messages.length === 0 && (
              <div className="mt-6 text-center text-sm text-muted-foreground">
                <Sparkles size={22} className="mx-auto mb-2 text-primary" />
                <p>Ask about your listings or business.</p>
                <div className="mt-3 space-y-1.5">
                  {["How is my business doing?", "What should I prioritise today?", "Which items are struggling?"].map((q) => (
                    <button key={q} onClick={() => send(q)} className="block w-full rounded-lg border border-border bg-muted/30 px-3 py-1.5 text-xs text-foreground/80 hover:border-primary/30">{q}</button>
                  ))}
                </div>
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} className={m.role === "user" ? "flex justify-end" : "flex justify-start"}>
                <div className={`max-w-[85%] rounded-xl px-3 py-2 text-sm ${m.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted/40 text-foreground"}`}>
                  <p className="whitespace-pre-line">{m.text}</p>
                  {m.role === "ai" && m.text && (
                    <button onClick={() => speak(m.text)} className="mt-1 inline-flex items-center gap-1 text-[11px] text-muted-foreground hover:text-foreground"><Volume2 size={12} /> Play</button>
                  )}
                  {m.recs?.length > 0 && (
                    <div className="mt-2 space-y-2">
                      {m.recs.map((r, j) => (
                        <div key={j} className="rounded-lg border border-border bg-card/60 p-2">
                          <div className="flex items-center justify-between"><span className="text-xs font-semibold">{r.title}</span><span className={`text-[10px] font-bold uppercase ${URGENCY[r.urgency] || URGENCY.medium}`}>{r.urgency}</span></div>
                          <p className="mt-0.5 text-[11px] text-muted-foreground">{r.detail}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && <div className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 size={16} className="animate-spin" /> Thinking...</div>}
            <div ref={endRef} />
          </div>

          <div className="border-t border-border p-3">
            <div className="flex items-center gap-2">
              {voiceSupported && (
                <button data-testid="assistant-voice-button" onClick={toggleVoice} className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border ${listening ? "border-primary bg-primary/20 text-primary animate-pulse" : "border-border bg-secondary text-muted-foreground hover:text-foreground"}`}>
                  {listening ? <MicOff size={16} /> : <Mic size={16} />}
                </button>
              )}
              <input data-testid="assistant-input" value={query} onChange={(e) => setQuery(e.target.value)} onKeyDown={(e) => e.key === "Enter" && send()}
                placeholder={listening ? "Listening..." : "Ask your AI manager..."}
                className="flex-1 rounded-lg border border-border bg-muted/30 px-3 py-2 text-sm outline-none focus:border-primary/50" />
              <button data-testid="assistant-send-button" onClick={() => send()} disabled={loading} className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground disabled:opacity-50"><Send size={16} /></button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default AIAssistant;
