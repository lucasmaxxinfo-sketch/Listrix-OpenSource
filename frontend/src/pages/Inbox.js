import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Loader2, RefreshCw, Inbox as InboxIcon, AlertTriangle, TrendingUp, MessageSquare, Sparkles, Bell, ArrowUpRight } from "lucide-react";
import { api, draftReply, markInboxRead } from "@/lib/api";

const META = {
  AI_ALERT: { icon: AlertTriangle, tone: "text-[hsl(var(--destructive))]", bg: "bg-[rgba(239,68,68,0.12)]" },
  OPPORTUNITY: { icon: TrendingUp, tone: "text-[hsl(var(--lx-green))]", bg: "bg-[rgba(34,197,94,0.12)]" },
  ACTION_RECOMMENDED: { icon: Sparkles, tone: "text-primary", bg: "bg-[rgba(255,122,26,0.12)]" },
  BUYER_MESSAGE: { icon: MessageSquare, tone: "text-[hsl(var(--lx-blue))]", bg: "bg-[rgba(59,130,246,0.12)]" },
  SYSTEM: { icon: Bell, tone: "text-muted-foreground", bg: "bg-muted/40" },
};
const PRIO = {
  high: "border-[rgba(239,68,68,0.3)] text-[hsl(var(--destructive))]",
  medium: "border-primary/30 text-primary",
  low: "border-border text-muted-foreground",
};

export default function Inbox() {
  const navigate = useNavigate();
  const [msgs, setMsgs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [replyOpen, setReplyOpen] = useState(null);
  const [replyText, setReplyText] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try { const { data } = await api.get("/inbox"); setMsgs(data); } catch { toast.error("Failed to load inbox"); } finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);

  const refresh = async () => {
    setRefreshing(true);
    try { const r = await api.post("/inbox/refresh"); await load(); toast.success(r.data.gmail_imported ? `Inbox refreshed (+${r.data.gmail_imported} Gmail)` : "Inbox refreshed"); } catch { toast.error("Refresh failed"); } finally { setRefreshing(false); }
  };
  const sendReply = async (m) => {
    if (!replyText.trim()) return toast.error("Write a reply first");
    try { await draftReply(m.id, replyText.trim()); toast.success("Reply saved as draft (sending is manual)"); setReplyOpen(null); setReplyText(""); await load(); } catch { toast.error("Failed to save reply"); }
  };
  const markRead = async (m) => { try { await markInboxRead(m.id); await load(); } catch { /* noop */ } };

  return (
    <div data-testid="inbox-page">
      <div className="mb-5 flex items-center justify-between">
        <p className="text-sm text-muted-foreground">Business operations inbox — alerts, opportunities & buyer signals.</p>
        <button data-testid="inbox-refresh-button" onClick={refresh} disabled={refreshing} className="inline-flex items-center gap-2 rounded-lg bg-primary px-3.5 py-2 text-sm font-semibold text-primary-foreground shadow-orangeGlow hover:shadow-orangeGlowStrong disabled:opacity-60">{refreshing ? <Loader2 size={15} className="animate-spin" /> : <RefreshCw size={15} />} Refresh</button>
      </div>
      {loading ? <div className="flex h-64 items-center justify-center text-muted-foreground"><Loader2 className="animate-spin" size={26} /></div>
      : msgs.length === 0 ? (
        <div className="flex h-64 flex-col items-center justify-center rounded-xl border border-dashed border-border bg-card/30 text-muted-foreground"><InboxIcon size={28} className="mb-3" /><p className="text-sm">Inbox is empty. Click Refresh to populate it.</p></div>
      ) : (
        <div className="space-y-3">
          {msgs.map((m) => {
            const meta = META[m.type] || META.SYSTEM; const Icon = meta.icon;
            return (
              <div key={m.id} data-testid="inbox-message" className="flex items-start gap-3 rounded-xl border border-border bg-card/60 p-4 shadow-panelSoft">
                <span className={`mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${meta.bg} ${meta.tone}`}><Icon size={17} /></span>
                <div className="min-w-0 flex-1">
                  <div className="mb-1 flex justify-end gap-1.5">
                    {!m.read && <button onClick={() => markRead(m)} className="rounded-md border border-border px-2 py-1 text-[11px] font-medium text-muted-foreground hover:text-foreground">Mark read</button>}
                    <button onClick={() => { setReplyOpen(replyOpen === m.id ? null : m.id); setReplyText(m.reply_draft || ""); }} className="rounded-md border border-border px-2 py-1 text-[11px] font-medium text-muted-foreground hover:text-foreground">{replyOpen === m.id ? "Close" : "Reply"}</button>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`rounded-md border px-1.5 py-0.5 text-[10px] font-bold uppercase ${PRIO[m.priority] || PRIO.low}`}>{m.priority}</span>
                    <span className="text-sm font-semibold">{m.title}</span>
                    {m.simulated && <span className="text-[10px] text-muted-foreground">(simulated)</span>}
                    {m.source === "gmail" && <span className="rounded bg-[rgba(59,130,246,0.12)] px-1.5 py-0.5 text-[10px] font-semibold text-[hsl(var(--lx-blue))]">Gmail</span>}
                    {!m.read && <span className="h-1.5 w-1.5 rounded-full bg-primary" />}
                  </div>
                  <p className="mt-1 text-sm text-foreground/80">{m.body}</p>
                  {m.from && <p className="mt-0.5 text-[11px] text-muted-foreground">from {m.from}</p>}
                  {m.suggested_action && <p className="mt-1 text-xs text-primary">Suggested: {m.suggested_action}</p>}
                  {m.reply_draft && <p className="mt-2 rounded-md border border-primary/20 bg-[rgba(255,122,26,0.07)] px-2.5 py-1.5 text-xs text-foreground/80"><span className="font-semibold text-primary">Draft:</span> {m.reply_draft}</p>}
                  {replyOpen === m.id && (
                    <div className="mt-2">
                      <textarea value={replyText} onChange={(e) => setReplyText(e.target.value)} rows={2} placeholder="Write a reply… (saved as a draft; nothing is sent automatically)" className="w-full rounded-lg border border-border bg-muted/30 px-3 py-2 text-sm outline-none focus:border-primary/50" />
                      <div className="mt-1.5 flex gap-2">
                        <button onClick={() => sendReply(m)} className="rounded-lg bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground">Save draft</button>
                        <button onClick={() => { setReplyOpen(null); setReplyText(""); }} className="rounded-lg border border-border bg-secondary px-3 py-1.5 text-xs font-semibold text-secondary-foreground">Cancel</button>
                      </div>
                    </div>
                  )}
                </div>
                {m.related_item_id && <button onClick={() => navigate(`/items/${m.related_item_id}`)} className="inline-flex shrink-0 items-center gap-1 rounded-lg border border-border px-2.5 py-1.5 text-xs font-semibold text-muted-foreground hover:text-foreground">View <ArrowUpRight size={13} /></button>}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
