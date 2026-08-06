import { Cpu, Activity, Sparkles, Package, Zap, CheckCircle2 } from "lucide-react";
import { useItems, useListings, useEvents } from "@/lib/queries";
import EventTimeline from "@/components/EventTimeline";
import StatCard from "@/components/StatCard";

export default function AIControl() {
  const { data: items = [] } = useItems();
  const { data: listings = [] } = useListings();
  const { data: events = [] } = useEvents();

  const errors = events.filter((e) => e.type === "AI_ERROR").length;
  const genEvents = events.filter((e) => e.type === "LISTING_GENERATED").length;
  const successRate = genEvents + errors > 0 ? Math.round((genEvents / (genEvents + errors)) * 100) : 100;

  return (
    <div data-testid="ai-control-page" className="space-y-6">
      {/* Model status */}
      <div className="rounded-xl border border-border bg-card/50 p-6 shadow-panelSoft">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-[rgba(255,122,26,0.12)] text-primary shadow-orangeGlow"><Cpu size={24} /></span>
            <div>
              <h2 className="text-lg font-semibold">Listing Intelligence Engine</h2>
              <p className="font-mono text-xs text-muted-foreground">provider: local ollama \u00b7 model: llama3.2-vision (open-source)</p>
            </div>
          </div>
          <span className="inline-flex items-center gap-2 rounded-full border border-[rgba(34,197,94,0.3)] bg-[rgba(34,197,94,0.12)] px-3 py-1.5 text-sm font-semibold text-[hsl(var(--lx-green))]">
            <span className="h-2 w-2 rounded-full bg-[hsl(var(--lx-green))] shadow-[0_0_8px_hsl(var(--lx-green))]" /> Online
          </span>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Items Analyzed" value={items.length} icon={Package} />
        <StatCard label="Listings Generated" value={listings.length} icon={Sparkles} accent />
        <StatCard label="Success Rate" value={`${successRate}%`} icon={CheckCircle2} />
        <StatCard label="Errors" value={errors} icon={Zap} />
      </div>

      {/* Capabilities + activity */}
      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-xl border border-border bg-card/40">
          <div className="border-b border-border px-5 py-3"><h3 className="text-sm font-semibold tracking-wide">Capabilities</h3></div>
          <div className="space-y-3 p-5">
            {[
              { t: "Marketplace Copywriting", d: "Generates catchy titles & persuasive descriptions." },
              { t: "Smart Pricing", d: "Suggests a fair market price from item details & cost." },
              { t: "Keyword Optimization", d: "Produces relevant hashtags for discoverability." },
            ].map((c) => (
              <div key={c.t} className="flex items-start gap-3 rounded-lg border border-border bg-card/60 p-3">
                <span className="mt-0.5 flex h-8 w-8 items-center justify-center rounded-lg bg-[rgba(255,122,26,0.12)] text-primary"><Sparkles size={15} /></span>
                <div><p className="text-sm font-medium">{c.t}</p><p className="text-xs text-muted-foreground">{c.d}</p></div>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-xl border border-border bg-card/40">
          <div className="flex items-center gap-2 border-b border-border px-5 py-3"><Activity size={15} className="text-muted-foreground" /><h3 className="text-sm font-semibold tracking-wide">Engine Activity</h3></div>
          <EventTimeline events={events.slice(0, 10)} emptyText="No engine activity yet." />
        </section>
      </div>
    </div>
  );
}
