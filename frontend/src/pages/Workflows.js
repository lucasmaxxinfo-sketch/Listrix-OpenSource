import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { ImagePlus, X, Loader2, Sparkles, Check, ArrowRight, ArrowLeft, Tag, DollarSign, Wand2, Eye, LayoutGrid, History, Workflow as WorkflowIcon, Package } from "lucide-react";
import { useCreateItem, useGenerateListing, useItems, useListings, useEvents, useSetItemStage, useUploadItemImage } from "@/lib/queries";
import { visionAnalyze, imageSrc } from "@/lib/api";
import { formatMoney, buildListingIndex, listingForItem, estimatedValue } from "@/lib/derive";
import { compressImage } from "@/lib/utils";

const STEPS = ["Item Details", "Photo & AI Vision", "Generate", "Review"];
const CONDITIONS = ["New", "Like New", "Good", "Fair", "Used", "For Parts"];
const MAX = 5 * 1024 * 1024;
const inputCls = "w-full rounded-lg border border-border bg-muted/30 px-3 py-2.5 text-sm text-foreground outline-none transition-colors focus:border-primary/50 focus:ring-2 focus:ring-ring/40 placeholder:text-muted-foreground/60";

export default function Workflows() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState({ name: "", description: "", condition: "", category: "", cost: "" });
  const [image, setImage] = useState(null);
  const [vision, setVision] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [listing, setListing] = useState(null);
  const [tab, setTab] = useState("flow");
  const createItem = useCreateItem();
  const generate = useGenerateListing();
  const uploadImage = useUploadItemImage();
  const busy = createItem.isPending || generate.isPending;
  const update = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const progress = (step / (STEPS.length - 1)) * 100;

  const handleImage = async (e) => {
    const file = e.target.files?.[0]; if (!file) return;
    if (!file.type.startsWith("image/")) return toast.error("Please select an image file.");
    if (file.size > MAX) return toast.error("Image must be under 5MB.");
    try {
      const dataUrl = await compressImage(file);
      setImage(dataUrl); setVision(null);
    } catch (err) {
      toast.error(err?.message || "Could not process the image.");
    }
    e.target.value = "";
  };

  const analyzeImage = async () => {
    if (!image) return;
    setAnalyzing(true);
    try {
      const v = await visionAnalyze({ image });
      setVision(v);
      // Auto-fill (user can still edit)
      setForm((f) => ({
        ...f,
        name: f.name || v.suggested_title || v.item_type || "",
        description: f.description || v.suggested_description || "",
        condition: f.condition || v.condition_guess || "",
        category: f.category || v.category || "",
        cost: f.cost,
      }));
      toast.success("Image analysed — fields auto-filled");
    } catch { toast.error("Image analysis failed"); } finally { setAnalyzing(false); }
  };

  const validate0 = () => {
    if (!form.name.trim() || !form.description.trim() || !form.condition.trim()) { toast.error("Name, description and condition are required."); return false; }
    return true;
  };
  const next = () => {
    if (step === 0 && !validate0()) return;
    if (step === 1 && form.cost !== "" && (isNaN(Number(form.cost)) || Number(form.cost) < 0)) return toast.error("Cost must be a valid number.");
    setStep((s) => Math.min(s + 1, STEPS.length - 1));
  };
  const back = () => setStep((s) => Math.max(s - 1, 0));

  const saveAndGenerate = async () => {
    const cost = form.cost === "" ? null : Number(form.cost);
    try {
      const item = await createItem.mutateAsync({
        name: form.name.trim(), description: form.description.trim(), condition: form.condition.trim(),
        image: image || null, cost, category: form.category || (vision?.category ?? null),
        vision: vision ? { item_type: vision.item_type, category: vision.category, brand: vision.brand, condition_guess: vision.condition_guess, features: vision.features } : null,
        value_estimate: vision?.value_estimate || null,
      });
      const result = await generate.mutateAsync({ name: item.name, description: item.description, condition: item.condition, cost, item_id: item.id });
      if (image) { try { await uploadImage.mutateAsync({ id: item.id, data: image }); } catch { toast.warning("Item saved, but image upload to object storage failed."); } }
      setListing(result); toast.success("Item created & listing generated!"); setStep(3);
    } catch { toast.error("Something went wrong. Please try again."); }
  };
  const reset = () => { setForm({ name: "", description: "", condition: "", category: "", cost: "" }); setImage(null); setVision(null); setListing(null); setStep(0); };

  const TABS = [
    { id: "flow", label: "Create Flow", icon: WorkflowIcon },
    { id: "kanban", label: "Kanban", icon: LayoutGrid },
    { id: "timeline", label: "Timeline", icon: History },
  ];

  return (
    <div data-testid="workflow-stepper">
      <div className="mb-5 flex items-center gap-1 rounded-xl border border-border bg-card/40 p-1">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button key={id} data-testid={`workflow-tab-${id}`} onClick={() => setTab(id)} className={`inline-flex flex-1 items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold transition-colors ${tab === id ? "bg-primary text-primary-foreground shadow-orangeGlow" : "text-muted-foreground hover:text-foreground"}`}><Icon size={15} /> {label}</button>
        ))}
      </div>

      {tab === "kanban" && <KanbanBoard />}
      {tab === "timeline" && <TimelineView />}
      {tab === "flow" && (<div className="mx-auto max-w-3xl">
      <div className="mb-6 rounded-xl border border-border bg-card/50 p-5">
        <div className="mb-3 flex items-center justify-between">
          {STEPS.map((label, i) => (
            <div key={label} className="flex items-center gap-2">
              <span className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold ${i < step ? "bg-[hsl(var(--lx-green))] text-black" : i === step ? "bg-primary text-primary-foreground shadow-orangeGlow" : "bg-muted/50 text-muted-foreground"}`}>{i < step ? <Check size={14} /> : i + 1}</span>
              <span className={`hidden text-xs font-medium sm:inline ${i === step ? "text-foreground" : "text-muted-foreground"}`}>{label}</span>
            </div>
          ))}
        </div>
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted/40"><div className="h-full rounded-full bg-primary transition-[width] duration-300" style={{ width: `${progress}%` }} /></div>
      </div>

      <div className="rounded-xl border border-border bg-card/50 p-6 shadow-panelSoft">
        {step === 0 && (
          <div className="space-y-4">
            <div><h2 className="text-lg font-semibold">Item Details</h2><p className="text-sm text-muted-foreground">Tell us what you’re selling (or upload a photo next and let AI fill this in).</p></div>
            <div><label className="mb-1.5 block text-xs font-medium text-muted-foreground">Name</label><input data-testid="input-name" className={inputCls} value={form.name} onChange={update("name")} placeholder="e.g. Sony WH-1000XM4 Headphones" /></div>
            <div><label className="mb-1.5 block text-xs font-medium text-muted-foreground">Description</label><textarea data-testid="input-description" rows={4} className={inputCls} value={form.description} onChange={update("description")} placeholder="Condition, what's included, any flaws..." /></div>
            <div className="grid grid-cols-2 gap-4">
              <div><label className="mb-1.5 block text-xs font-medium text-muted-foreground">Condition</label><select data-testid="input-condition" className={inputCls} value={form.condition} onChange={update("condition")}><option value="">Select</option>{CONDITIONS.map((c) => <option key={c} value={c}>{c}</option>)}</select></div>
              <div><label className="mb-1.5 block text-xs font-medium text-muted-foreground">Category</label><input data-testid="input-category" className={inputCls} value={form.category} onChange={update("category")} placeholder="e.g. Electronics" /></div>
            </div>
          </div>
        )}

        {step === 1 && (
          <div className="space-y-4">
            <div><h2 className="text-lg font-semibold">Photo & AI Vision</h2><p className="text-sm text-muted-foreground">Upload a photo and let the visual AI identify it, estimate value and auto-fill your details.</p></div>
            {!image ? (
              <label data-testid="create-item-image-upload" className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-border bg-card/40 py-10 text-muted-foreground transition-colors hover:border-primary/40">
                <ImagePlus size={26} /><span className="text-sm">Click to upload (max 5MB)</span>
                <input data-testid="input-image" type="file" accept="image/*" className="hidden" onChange={handleImage} />
              </label>
            ) : (
              <div className="space-y-3">
                <div className="relative inline-block"><img src={image} alt="preview" className="h-44 w-full rounded-xl border border-border object-cover" /><button onClick={() => { setImage(null); setVision(null); }} className="absolute right-2 top-2 rounded-full bg-black/70 p-1.5 text-white hover:bg-black"><X size={14} /></button></div>
                <button data-testid="analyze-image-button" onClick={analyzeImage} disabled={analyzing} className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-orangeGlow hover:shadow-orangeGlowStrong disabled:opacity-60">{analyzing ? <Loader2 size={15} className="animate-spin" /> : <Wand2 size={15} />} Analyze Image & Auto-Fill</button>
                {vision && (
                  <div data-testid="vision-result" className="rounded-lg border border-primary/20 bg-card/60 p-4">
                    <div className="flex items-center gap-2 text-primary"><Eye size={15} /><span className="text-sm font-semibold">AI Visual Analysis</span></div>
                    <p className="mt-2 text-sm"><b>{vision.item_type}</b>{vision.brand ? ` · ${vision.brand}` : ""} · {vision.category}</p>
                    <p className="mt-1 text-sm text-[hsl(var(--lx-green))]">Value: {formatMoney(vision.value_estimate?.low)} – {formatMoney(vision.value_estimate?.high)} (mid {formatMoney(vision.value_estimate?.mid)}, {Math.round(vision.value_estimate?.confidence || 0)}% conf.)</p>
                    {vision.features?.length > 0 && <div className="mt-2 flex flex-wrap gap-1.5">{vision.features.slice(0, 6).map((f, i) => <span key={i} className="rounded-full bg-muted/50 px-2 py-0.5 text-[11px] text-muted-foreground">{f}</span>)}</div>}
                  </div>
                )}
              </div>
            )}
            <div><label className="mb-1.5 block text-xs font-medium text-muted-foreground">Your Cost ($) <span className="text-muted-foreground/60">optional</span></label><div className="relative"><DollarSign size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" /><input data-testid="input-cost" type="number" min="0" className={inputCls + " pl-8"} value={form.cost} onChange={update("cost")} placeholder="e.g. 180" /></div></div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4">
            <div><h2 className="text-lg font-semibold">Generate Listing</h2><p className="text-sm text-muted-foreground">Review, then let the AI write your listing.</p></div>
            <div className="rounded-lg border border-border bg-muted/20 p-4 text-sm">
              <Row k="Name" v={form.name} /><Row k="Condition" v={form.condition} /><Row k="Category" v={form.category || "—"} /><Row k="Cost" v={form.cost === "" ? "—" : `$${form.cost}`} /><Row k="Image" v={image ? "Attached" : "None"} /><Row k="AI value" v={vision?.value_estimate ? formatMoney(vision.value_estimate.mid) : "—"} />
            </div>
            <button data-testid="workflow-submit-button" onClick={saveAndGenerate} disabled={busy} className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground shadow-orangeGlowStrong hover:shadow-orangeGlow disabled:opacity-60">{busy ? <><Loader2 size={16} className="animate-spin" /> Working...</> : <><Sparkles size={16} /> Save & Generate Listing</>}</button>
          </div>
        )}

        {step === 3 && listing && (
          <div data-testid="listing-result" className="space-y-4">
            <div className="flex items-center gap-2 text-[hsl(var(--lx-green))]"><Check size={18} /><span className="text-sm font-semibold">Listing generated successfully</span></div>
            <div className="rounded-xl border border-primary/20 bg-card/60 p-5 shadow-orangeGlow">
              <span className="inline-flex items-center gap-1.5 rounded-md border border-primary/30 bg-[rgba(255,122,26,0.12)] px-2 py-0.5 text-xs font-semibold text-primary"><Sparkles size={13} /> AI Listing</span>
              <h3 data-testid="result-title" className="mt-3 text-lg font-bold">{listing.listing_title}</h3>
              <p data-testid="result-description" className="mt-2 whitespace-pre-line text-sm text-foreground/85">{listing.listing_description}</p>
              <p data-testid="result-price" className="mt-3 text-2xl font-bold tabular-nums text-[hsl(var(--lx-green))]">${listing.suggested_price}</p>
              {listing.hashtags?.length > 0 && <div data-testid="result-hashtags" className="mt-3 flex flex-wrap gap-2">{listing.hashtags.map((h, i) => <span key={i} className="inline-flex items-center gap-1 rounded-full bg-muted/50 px-2.5 py-1 text-xs text-muted-foreground"><Tag size={11} /> {h}</span>)}</div>}
            </div>
            <div className="flex gap-3"><button onClick={() => navigate("/ai-manager")} className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground">Get AI Actions <ArrowRight size={15} /></button><button onClick={reset} className="inline-flex items-center gap-2 rounded-lg border border-border bg-secondary px-4 py-2 text-sm font-semibold text-secondary-foreground hover:bg-muted/50">Create another</button></div>
          </div>
        )}

        {step < 2 && (
          <div className="mt-6 flex items-center justify-between">
            <button data-testid="workflow-back-button" onClick={back} disabled={step === 0} className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-secondary px-4 py-2 text-sm font-semibold text-secondary-foreground hover:bg-muted/50 disabled:opacity-40"><ArrowLeft size={15} /> Back</button>
            <button data-testid="workflow-next-button" onClick={next} className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-5 py-2 text-sm font-semibold text-primary-foreground shadow-orangeGlow hover:shadow-orangeGlowStrong">Next <ArrowRight size={15} /></button>
          </div>
        )}
        {step === 2 && <div className="mt-6"><button data-testid="workflow-back-button" onClick={back} className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-secondary px-4 py-2 text-sm font-semibold text-secondary-foreground hover:bg-muted/50"><ArrowLeft size={15} /> Back</button></div>}
      </div>
    </div>)}
    </div>
  );
}

const STAGE_META = {
  inventory: { label: "Inventory", tone: "text-muted-foreground border-border" },
  listed: { label: "Listed", tone: "text-primary border-primary/30" },
  sold: { label: "Sold", tone: "text-[hsl(var(--lx-green))] border-[rgba(34,197,94,0.3)]" },
  archived: { label: "Archived", tone: "text-muted-foreground border-border" },
};
const STAGE_ORDER = ["inventory", "listed", "sold", "archived"];

function KanbanBoard() {
  const navigate = useNavigate();
  const { data: items = [], isLoading } = useItems();
  const { data: listings = [] } = useListings();
  const setStage = useSetItemStage();
  const index = buildListingIndex(listings);
  if (isLoading) return <div className="flex h-64 items-center justify-center text-muted-foreground"><Loader2 className="animate-spin" size={26} /></div>;

  return (
    <div data-testid="kanban-board" className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {STAGE_ORDER.map((stage) => {
        const meta = STAGE_META[stage];
        const col = items.filter((it) => (it.stage || "inventory") === stage);
        return (
          <div key={stage} className="rounded-xl border border-border bg-card/40 p-3">
            <div className="mb-3 flex items-center justify-between px-1">
              <span className={`rounded-md border px-2 py-0.5 text-[11px] font-bold uppercase ${meta.tone}`}>{meta.label}</span>
              <span className="text-xs text-muted-foreground">{col.length}</span>
            </div>
            <div className="space-y-2">
              {col.map((it) => {
                const listing = listingForItem(it, index);
                const value = estimatedValue(it, listing);
                return (
                  <div key={it.id} data-testid={`kanban-card-${it.stage || "inventory"}`} className="rounded-lg border border-border bg-card/70 p-3 shadow-panelSoft">
                    {it.image_id || it.image ? <img src={imageSrc(it, true)} alt={it.name} className="mb-2 h-16 w-full rounded-md border border-border object-cover" /> : <div className="mb-2 flex h-16 w-full items-center justify-center rounded-md bg-muted/30 text-muted-foreground"><Package size={18} /></div>}
                    <button onClick={() => navigate(`/items/${it.id}`)} className="block w-full truncate text-left text-sm font-semibold hover:text-primary">{it.name}</button>
                    <p className="mt-0.5 text-xs text-muted-foreground">{it.sold ? `Sold \u00B7 \${formatMoney(it.sale_price)}` : `Est. \${formatMoney(value)}`}</p>
                    <select value={it.stage || "inventory"} onChange={(e) => setStage.mutate({ id: it.id, stage: e.target.value })} className="mt-2 w-full rounded-md border border-border bg-muted/30 px-2 py-1 text-xs outline-none">
                      {STAGE_ORDER.map((st) => <option key={st} value={st} disabled={st === (it.stage || "inventory")}>{STAGE_META[st].label}</option>)}
                    </select>
                  </div>
                );
              })}
              {col.length === 0 && <div className="rounded-lg border border-dashed border-border p-6 text-center text-xs text-muted-foreground">Empty</div>}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function TimelineView() {
  const { data: events = [] } = useEvents();
  const { data: items = [] } = useItems();
  const eventsWithKey = events.map((e) => ({ ...e, dateKey: (e.created_at || "").slice(0, 10) }));
  const sold = items.filter((it) => it.sold && it.sold_at).map((it) => ({ id: it.id, dateKey: (it.sold_at || "").slice(0, 10), title: `Sold: \${it.name}`, type: "ITEM_SOLD" }));
  const days = {};
  for (const e of [...eventsWithKey, ...sold]) { (days[e.dateKey] ||= []).push(e); }
  const sorted = Object.entries(days).sort((a, b) => (a[0] < b[0] ? 1 : -1));
  return (
    <div data-testid="workflow-timeline" className="mx-auto max-w-2xl space-y-6">
      {sorted.length === 0 && <div className="rounded-xl border border-dashed border-border bg-card/30 p-10 text-center text-sm text-muted-foreground">No activity yet — create items and run analysis to populate the timeline.</div>}
      {sorted.map(([day, evs]) => (
        <div key={day}>
          <div className="mb-2 flex items-center gap-2"><span className="rounded-md border border-border bg-card/60 px-2 py-0.5 text-[11px] font-bold uppercase tracking-wide text-muted-foreground">{day}</span><span className="h-px flex-1 bg-border" /></div>
          <div className="space-y-2">
            {evs.sort((a, b) => ((a.created_at || "") < (b.created_at || "") ? 1 : -1)).map((e, i) => (
              <div key={`${e.id || e.dateKey}-${i}`} className="flex items-start gap-3 rounded-lg border border-border bg-card/50 p-3">
                <span className="mt-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/15 text-primary"><History size={12} /></span>
                <div className="min-w-0"><p className="truncate text-sm font-medium">{e.title || e.message}</p><p className="text-[11px] text-muted-foreground">{e.type || "ITEM_SOLD"} · {new Date(e.created_at || Date.now()).toLocaleTimeString()}</p></div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function Row({ k, v }) { return <div className="flex justify-between py-1"><span className="text-muted-foreground">{k}</span><span className="font-medium">{v}</span></div>; }
