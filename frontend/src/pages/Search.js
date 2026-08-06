import { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Loader2, Search as SearchIcon, Package, Sparkles, Bell, MessageSquare, ArrowUpRight } from "lucide-react";
import { searchAll } from "@/lib/api";

const TYPE_META = {
  item: { icon: Package, tone: "text-primary", label: "Item" },
  listing: { icon: Sparkles, tone: "text-[hsl(var(--lx-green))]", label: "Listing" },
  event: { icon: Bell, tone: "text-muted-foreground", label: "Event" },
  inbox: { icon: MessageSquare, tone: "text-[hsl(var(--lx-blue))]", label: "Inbox" },
};

export default function Search() {
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const q = params.get("q") || "";
  const [input, setInput] = useState(q);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (q.length < 2) { setData(null); return; }
    let live = true;
    setLoading(true);
    searchAll(q)
      .then((r) => { if (live) setData(r); })
      .catch(() => toast.error("Search failed"))
      .finally(() => { if (live) setLoading(false); });
    return () => { live = false; };
  }, [q]);

  const submit = (e) => {
    e.preventDefault();
    const term = input.trim();
    if (term.length < 2) return toast.error("Type at least 2 characters to search");
    setParams({ q: term });
  };

  return (
    <div data-testid="search-page" className="space-y-5">
      <form onSubmit={submit} className="flex items-center gap-2">
        <div className="relative flex-1">
          <SearchIcon size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input autoFocus value={input} onChange={(e) => setInput(e.target.value)} placeholder="Search items, listings, events, inbox…" className="w-full rounded-lg border border-border bg-muted/30 py-2.5 pl-9 pr-3 text-sm outline-none transition-colors focus:border-primary/50 focus:ring-2 focus:ring-ring/40" />
        </div>
        <button className="rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground shadow-orangeGlow hover:shadow-orangeGlowStrong">Search</button>
      </form>

      {loading && <div className="flex h-40 items-center justify-center text-muted-foreground"><Loader2 className="animate-spin" size={22} /></div>}
      {!loading && data && (
        <div>
          <p className="text-sm text-muted-foreground">{data.count} result{data.count !== 1 ? "s" : ""} for “{q}”</p>
          {data.results.length === 0 ? (
            <div className="mt-4 rounded-xl border border-dashed border-border bg-card/30 p-10 text-center text-sm text-muted-foreground">No matches in this workspace.</div>
          ) : (
            <div className="mt-3 space-y-2">
              {data.results.map((r, i) => {
                const meta = TYPE_META[r.type] || TYPE_META.event; const Icon = meta.icon;
                return (
                  <button key={`${r.type}-${r.id}-${i}`} onClick={() => r.link && navigate(r.link)} className="flex w-full items-start gap-3 rounded-xl border border-border bg-card/60 p-3.5 text-left shadow-panelSoft transition-colors hover:border-primary/30">
                    <span className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted/40 ${meta.tone}`}><Icon size={15} /></span>
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-sm font-semibold">{r.title}</span>
                      {r.subtitle && <span className="mt-0.5 block truncate text-xs text-muted-foreground">{r.subtitle}</span>}
                    </span>
                    <span className="flex items-center gap-1 text-[10px] uppercase tracking-wide text-muted-foreground">{meta.label}{r.link && <ArrowUpRight size={12} />}</span>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
