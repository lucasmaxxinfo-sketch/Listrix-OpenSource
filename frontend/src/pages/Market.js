import { useState } from "react";
import { toast } from "sonner";
import { Loader2, Store, Copy, Tag, ArrowUpRight } from "lucide-react";
import { useListings } from "@/lib/queries";
import { formatTime } from "@/lib/derive";

export default function Market() {
  const { data: listings = [], isLoading } = useListings();
  const [copied, setCopied] = useState(null);

  const copyListing = (ls) => {
    const text = `${ls.listing_title}\n\n${ls.listing_description}\n\nSuggested price: $${ls.suggested_price}\n\n${(ls.hashtags || []).map((h) => "#" + h).join(" ")}`;
    navigator.clipboard.writeText(text);
    setCopied(ls.id);
    toast.success("Listing copied to clipboard.");
    setTimeout(() => setCopied(null), 1500);
  };

  if (isLoading) {
    return <div className="flex h-64 items-center justify-center text-muted-foreground"><Loader2 className="animate-spin" size={26} /></div>;
  }

  return (
    <div data-testid="market-page">
      <p className="mb-5 text-sm text-muted-foreground">{listings.length} AI-generated listing{listings.length !== 1 ? "s" : ""}</p>

      {listings.length === 0 ? (
        <div className="flex h-64 flex-col items-center justify-center rounded-xl border border-dashed border-border bg-card/30 text-muted-foreground">
          <Store size={28} className="mb-3" />
          <p className="text-sm">No listings yet. Generate one from your items or a workflow.</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {listings.map((ls) => (
            <div key={ls.id} data-testid="market-listing-card" className="flex flex-col rounded-xl border border-border bg-card/55 p-5 shadow-panelSoft transition-colors hover:border-primary/25">
              <div className="flex items-start justify-between gap-3">
                <h3 data-testid="market-listing-title" className="text-sm font-semibold leading-snug line-clamp-2">{ls.listing_title}</h3>
                <span data-testid="market-listing-price" className="shrink-0 rounded-md bg-[rgba(34,197,94,0.12)] px-2 py-0.5 text-sm font-bold tabular-nums text-[hsl(var(--lx-green))]">${ls.suggested_price}</span>
              </div>
              <p className="mt-2 flex-1 text-xs text-foreground/70 line-clamp-4">{ls.listing_description}</p>
              {ls.hashtags?.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {ls.hashtags.slice(0, 6).map((h, i) => (
                    <span key={i} className="inline-flex items-center gap-1 rounded-full bg-muted/50 px-2 py-0.5 text-[11px] text-muted-foreground"><Tag size={10} /> {h}</span>
                  ))}
                </div>
              )}
              <div className="mt-4 flex items-center justify-between border-t border-border pt-3">
                <span className="truncate text-[11px] text-muted-foreground">{ls.source_name} \u00b7 {formatTime(ls.created_at)}</span>
                <button data-testid="market-listing-copy-button" onClick={() => copyListing(ls)} className="inline-flex items-center gap-1.5 rounded-lg border border-border px-2.5 py-1.5 text-xs font-semibold text-muted-foreground transition-colors hover:bg-muted/50 hover:text-foreground">
                  <Copy size={13} /> {copied === ls.id ? "Copied" : "Copy"}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
