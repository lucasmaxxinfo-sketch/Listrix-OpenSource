import { useState } from "react";
import { toast } from "sonner";
import { Play, Loader2, ListChecks, CheckCircle2, XCircle, Info } from "lucide-react";
import { useSuggestions, usePerformance, useAnalyzeAll, useApplySuggestion, useDismissSuggestion } from "@/lib/queries";
import ActionCard from "@/components/ActionCard";
import ControlActionDialog from "@/components/ControlActionDialog";

export default function AIManager() {
  const { data: pending = [], isLoading } = useSuggestions("pending");
  const { data: applied = [] } = useSuggestions("applied");
  const { data: dismissed = [] } = useSuggestions("dismissed");
  const { data: performance = [] } = usePerformance();
  const analyzeAll = useAnalyzeAll();
  const apply = useApplySuggestion();
  const dismiss = useDismissSuggestion();
  const [dialog, setDialog] = useState(null);

  const runAnalysis = async () => {
    try { const r = await analyzeAll.mutateAsync(); toast.success(`Analyzed ${r.analyzed} item(s)`); }
    catch { toast.error("Analysis failed"); }
  };
  const confirmApply = async () => {
    try { const res = await apply.mutateAsync(dialog.id); toast.success(res.change || "Action applied"); setDialog(null); }
    catch { toast.error("Apply failed"); }
  };
  const reject = async (s) => { try { await dismiss.mutateAsync(s.id); toast.success("Action rejected"); } catch { toast.error("Reject failed"); } };

  return (
    <div data-testid="ai-manager-page" className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm text-muted-foreground">Your AI marketplace operations analyst. Every action needs your approval.</p>
        </div>
        <button data-testid="run-analysis-button" onClick={runAnalysis} disabled={analyzeAll.isPending} className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-orangeGlow hover:shadow-orangeGlowStrong disabled:opacity-60">
          {analyzeAll.isPending ? <Loader2 size={15} className="animate-spin" /> : <Play size={15} />} Run Marketing Analysis
        </button>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <Stat label="Queued Actions" value={pending.length} tone="text-primary" />
        <Stat label="Approved" value={applied.length} tone="text-[hsl(var(--lx-green))]" />
        <Stat label="Rejected" value={dismissed.length} tone="text-[hsl(var(--destructive))]" />
      </div>

      <section className="rounded-xl border border-border bg-card/40">
        <div className="flex items-center gap-2 border-b border-border px-5 py-3"><ListChecks size={15} className="text-primary" /><h2 className="text-sm font-semibold tracking-wide">Action Queue</h2></div>
        <div className="p-4">
          {isLoading ? <div className="flex h-32 items-center justify-center text-muted-foreground"><Loader2 className="animate-spin" size={22} /></div>
          : pending.length === 0 ? (
            <div className="flex h-32 flex-col items-center justify-center text-center text-muted-foreground">
              <Info size={22} className="mb-2" /><p className="text-sm">No actions queued. Run a marketing analysis to generate recommendations.</p>
            </div>
          ) : (
            <div data-testid="action-queue" className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {pending.map((s) => <ActionCard key={s.id} suggestion={s} onApprove={setDialog} onReject={reject} busy={apply.isPending || dismiss.isPending} />)}
            </div>
          )}
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <HistoryPanel title="Approved Actions" icon={CheckCircle2} tone="text-[hsl(var(--lx-green))]" rows={applied} />
        <HistoryPanel title="Rejected Actions" icon={XCircle} tone="text-[hsl(var(--destructive))]" rows={dismissed} />
      </div>

      <ControlActionDialog suggestion={dialog} onConfirm={confirmApply} onClose={() => setDialog(null)} busy={apply.isPending} />
    </div>
  );
}

function Stat({ label, value, tone }) {
  return <div className="rounded-xl border border-border bg-card/60 p-4"><p className="text-xs text-muted-foreground">{label}</p><p className={`mt-1 text-2xl font-semibold ${tone}`}>{value}</p></div>;
}
function HistoryPanel({ title, icon: Icon, tone, rows }) {
  return (
    <section className="rounded-xl border border-border bg-card/40">
      <div className={`flex items-center gap-2 border-b border-border px-5 py-3`}><Icon size={15} className={tone} /><h3 className="text-sm font-semibold tracking-wide">{title}</h3></div>
      <div className="p-4">
        {rows.length === 0 ? <p className="text-sm text-muted-foreground">None yet.</p> : (
          <ul className="space-y-2">{rows.slice(0, 8).map((s) => (
            <li key={s.id} className="flex items-center justify-between gap-3 rounded-lg border border-border bg-card/60 px-3 py-2">
              <div className="min-w-0"><p className="truncate text-sm font-medium">{s.title}</p><p className="truncate text-xs text-muted-foreground">{s.item_name}</p></div>
            </li>))}</ul>
        )}
      </div>
    </section>
  );
}
