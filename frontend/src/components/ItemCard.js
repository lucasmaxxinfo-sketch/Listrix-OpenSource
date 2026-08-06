import { Sparkles, ImageIcon, ShieldCheck, Loader2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { conditionScore, confidenceFor, estimatedValue, formatMoney } from "@/lib/derive";
import { imageSrc } from "@/lib/api";

const CONF = {
  low: "bg-muted/50 text-muted-foreground border border-border",
  medium: "bg-[rgba(255,122,26,0.12)] text-primary border border-primary/30",
  high: "bg-[rgba(34,197,94,0.12)] text-[hsl(var(--lx-green))] border border-[rgba(34,197,94,0.3)]",
};

export const ItemCard = ({ item, listing, onGenerate, generating }) => {
  const navigate = useNavigate();
  const score = conditionScore(item.condition);
  const { level } = confidenceFor(item, listing);
  const value = estimatedValue(item, listing);
  const open = () => navigate(`/items/${item.id}`);

  return (
    <div data-testid="item-card" className="group flex flex-col rounded-xl border border-border bg-card/60 p-3 shadow-panelSoft transition-colors hover:border-primary/30">
      <button onClick={open} data-testid="item-card-thumbnail" className="relative mb-3 overflow-hidden rounded-lg bg-muted/30 text-left">
        <div className="aspect-[4/3] w-full">
          {imageSrc(item, true) ? <img src={imageSrc(item, true)} alt={item.name} className="h-full w-full object-cover transition-opacity group-hover:opacity-95" /> : <div className="flex h-full w-full items-center justify-center text-muted-foreground"><ImageIcon size={28} /></div>}
        </div>
        <span data-testid="item-card-ai-confidence" className={`absolute left-2 top-2 inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold ${CONF[level]}`}><ShieldCheck size={12} /> {level} confidence</span>
      </button>
      <button onClick={open} data-testid="item-card-name" className="text-left text-sm font-semibold leading-snug line-clamp-2 hover:text-primary">{item.name}</button>
      <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground"><span>{item.condition}</span><span className="h-1 w-1 rounded-full bg-muted-foreground/50" /><span>Condition {score}</span></div>
      <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-muted/40"><div className="h-full rounded-full bg-primary/80" style={{ width: `${score}%` }} /></div>
      <div className="mt-3 flex items-end justify-between">
        <div><p className="text-[11px] uppercase tracking-wide text-muted-foreground">Est. value</p><p data-testid="item-card-estimated-value" className="text-2xl font-semibold tabular-nums">{formatMoney(value)}</p></div>
        {item.sold ? <span data-testid="item-card-sold" className="mb-1 rounded bg-[rgba(34,197,94,0.16)] px-2 py-0.5 text-[11px] font-semibold text-[hsl(var(--lx-green))]">Sold · {formatMoney(item.sale_price)}</span> : listing && <span className="mb-1 rounded bg-[rgba(34,197,94,0.12)] px-2 py-0.5 text-[11px] font-semibold text-[hsl(var(--lx-green))]">Listed</span>}
      </div>
      <button data-testid="item-card-generate-listing-button" onClick={() => onGenerate?.(item)} disabled={generating} className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground shadow-orangeGlow transition-shadow hover:shadow-orangeGlowStrong active:scale-[0.98] disabled:opacity-60">
        {generating ? <Loader2 size={15} className="animate-spin" /> : <Sparkles size={15} />}{listing ? "Regenerate" : "Generate Listing"}
      </button>
    </div>
  );
};

export default ItemCard;
