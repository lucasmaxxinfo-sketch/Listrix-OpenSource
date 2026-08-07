import { Link } from "react-router-dom";
import { Cpu, Wifi, WifiOff, ArrowRight } from "lucide-react";
import { useAIStatus } from "@/lib/queries";

export default function AIStatusBanner() {
  const { data, isError } = useAIStatus();

  // Backend itself is unreachable (e.g. the free GitHub Pages demo shell).
  if (isError) {
    return (
      <div data-testid="ai-status-banner" className="flex items-center justify-between gap-3 border-b border-border bg-[rgba(239,68,68,0.08)] px-4 py-2 md:px-6">
        <p className="flex items-center gap-2 text-xs text-red-300">
          <WifiOff size={13} /> <span><span className="font-semibold">Listrix backend is not connected.</span> This demo shows the app's look — run it on your computer (double-click the Listrix launcher) for live data, AI and sync.</span>
        </p>
      </div>
    );
  }

  if (!data || data.reachable) return null;

  return (
    <div data-testid="ai-status-banner" className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-[rgba(255,122,26,0.08)] px-4 py-2 md:px-6">
      <p className="flex items-center gap-2 text-xs text-amber-200">
        <Cpu size={13} /> <span><span className="font-semibold">The AI brain isn't running yet.</span> Start the free Ollama app on this computer ({data.model}) to enable AI listings, vision and the marketing agent.</span>
      </p>
      <Link to="/ai-control" className="inline-flex items-center gap-1 rounded-md border border-primary/30 bg-primary/10 px-2 py-1 text-[11px] font-semibold text-primary transition-colors hover:bg-primary/20">
        See AI status <ArrowRight size={11} />
      </Link>
    </div>
  );
}
