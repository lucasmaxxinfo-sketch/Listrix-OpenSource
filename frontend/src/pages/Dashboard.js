import { useEffect } from "react";
import { toast } from "sonner";
import { Package, Sparkles, DollarSign, Gauge, Loader2, Play } from "lucide-react";
import { logClientEvent } from "@/lib/api";
import { useItems, useListings, useEvents, useGenerateListing, useBriefLatest, useGenerateBrief, usePerformanceIntel, useSuggestions, useAnalyzeAll, useAnalytics } from "@/lib/queries";
import { buildListingIndex, listingForItem, formatMoney } from "@/lib/derive";
import StatCard from "@/components/StatCard";
import ItemCard from "@/components/ItemCard";
import EventTimeline from "@/components/EventTimeline";
import DailyBriefing from "@/components/DailyBriefing";
import WidgetCarousel from "@/components/WidgetCarousel";
import PerformanceIntelligence from "@/components/PerformanceIntelligence";
import DashboardChart from "@/components/DashboardChart";
import DashboardTable from "@/components/DashboardTable";

export default function Dashboard() {
  const { data: items = [], isLoading: li } = useItems();
  const { data: listings = [] } = useListings();
  const { data: events = [] } = useEvents();
  const { data: brief, isLoading: lb } = useBriefLatest();
  const { data: intel } = usePerformanceIntel();
  const { data: pending = [] } = useSuggestions("pending");
  const { data: analytics } = useAnalytics();
  const generate = useGenerateListing();
  const genBrief = useGenerateBrief();
  const analyzeAll = useAnalyzeAll();
  const index = buildListingIndex(listings);

  useEffect(() => { logClientEvent({ type: "COMMAND_CENTER_OPENED", message: "Command Center opened" }); }, []);

  const handleGenerate = async (item) => {
    try { await generate.mutateAsync({ name: item.name, description: item.description, condition: item.condition, cost: item.cost ?? null, item_id: item.id }); toast.success(`Listing generated for ${item.name}`); }
    catch { toast.error("AI generation failed."); }
  };
  const refreshBrief = async () => { try { await genBrief.mutateAsync(); toast.success("Daily briefing updated"); } catch { toast.error("Brief generation failed"); } };
  const runAnalysis = async () => { try { const r = await analyzeAll.mutateAsync(); toast.success(`Analyzed ${r.analyzed} item(s)`); } catch { toast.error("Analysis failed"); } };

  if (li) return <div className="flex h-64 items-center justify-center text-muted-foreground"><Loader2 className="animate-spin" size={26} /></div>;

  return (
    <div data-testid="dashboard-page" className="space-y-6">
      <DailyBriefing brief={brief} loading={lb} onRefresh={refreshBrief} refreshing={genBrief.isPending} />

      <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
        <div data-testid="dashboard-stats" className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <StatCard label="Total Items" value={items.length} icon={Package} accent />
          <StatCard label="Listings" value={listings.length} icon={Sparkles} accent />
          <StatCard label="Pending Actions" value={pending.length} icon={Gauge} />
          <StatCard label="Revenue Opp." value={formatMoney(intel?.predicted_revenue_opportunity)} icon={DollarSign} />
        </div>
        <WidgetCarousel items={items} suggestions={pending} perfIntel={intel} />
      </div>

      <DashboardChart analytics={analytics} events={events} />

      <DashboardTable items={items} listingIndex={index} />

      <div className="flex justify-end">
        <button data-testid="dashboard-run-analysis" onClick={runAnalysis} disabled={analyzeAll.isPending} className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-orangeGlow hover:shadow-orangeGlowStrong disabled:opacity-60">
          {analyzeAll.isPending ? <Loader2 size={15} className="animate-spin" /> : <Play size={15} />} Run Marketing Analysis
        </button>
      </div>

      <PerformanceIntelligence intel={intel} />

      {analytics && (
        <section data-testid="dashboard-analytics" className="rounded-xl border border-border bg-card/40">
          <div className="border-b border-border px-5 py-3"><h2 className="text-sm font-semibold tracking-wide">Activity Analytics</h2><p className="text-xs text-muted-foreground">Last {analytics.days} days · {analytics.events_total} events</p></div>
          <div className="grid gap-4 p-4 sm:grid-cols-[auto_1fr]">
            <div className="grid grid-cols-2 gap-2 text-sm">
              {[["Items", analytics.totals.items], ["Sold", analytics.totals.sold], ["Listings", analytics.totals.listings], ["Pending Actions", analytics.totals.pending_actions]].map(([k, v]) => (
                <div key={k} className="rounded-lg border border-border bg-card/60 px-3 py-2"><p className="text-[10px] uppercase tracking-wide text-muted-foreground">{k}</p><p className="text-lg font-bold tabular-nums">{v}</p></div>
              ))}
            </div>
            <div className="space-y-1.5">
              {analytics.top_event_types.slice(0, 5).map((t) => (
                <div key={t.type} className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">{t.type}</span>
                  <span className="tabular-nums">{t.count}</span>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <section data-testid="dashboard-recent-items" className="lg:col-span-2 rounded-xl border border-border bg-card/40">
          <div className="border-b border-border px-5 py-3"><h2 className="text-sm font-semibold tracking-wide">Recent Items</h2></div>
          <div className="p-4">
            {items.length === 0 ? <p className="py-8 text-center text-sm text-muted-foreground">No items yet.</p> : (
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                {items.slice(0, 6).map((it) => <ItemCard key={it.id} item={it} listing={listingForItem(it, index)} onGenerate={handleGenerate} generating={generate.isPending} />)}
              </div>
            )}
          </div>
        </section>
        <section data-testid="dashboard-event-stream" className="rounded-xl border border-border bg-card/40">
          <div className="border-b border-border px-5 py-3"><h2 className="text-sm font-semibold tracking-wide">Event Stream</h2></div>
          <div className="max-h-[520px] overflow-y-auto lx-scroll"><EventTimeline events={events.slice(0, 20)} /></div>
        </section>
      </div>
    </div>
  );
}
