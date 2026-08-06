import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Plus, Loader2, Package } from "lucide-react";
import { useItems, useListings, useGenerateListing } from "@/lib/queries";
import { buildListingIndex, listingForItem } from "@/lib/derive";
import ItemCard from "@/components/ItemCard";

export default function Items() {
  const navigate = useNavigate();
  const { data: items = [], isLoading } = useItems();
  const { data: listings = [] } = useListings();
  const generate = useGenerateListing();
  const index = buildListingIndex(listings);

  const handleGenerate = async (item) => {
    try {
      await generate.mutateAsync({
        name: item.name, description: item.description, condition: item.condition,
        cost: item.cost ?? null, item_id: item.id,
      });
      toast.success(`Listing generated for ${item.name}`);
    } catch {
      toast.error("AI generation failed.");
    }
  };

  return (
    <div data-testid="items-page">
      <div className="mb-5 flex items-center justify-between">
        <p className="text-sm text-muted-foreground">{items.length} item{items.length !== 1 ? "s" : ""} in inventory</p>
        <button data-testid="items-create-button" onClick={() => navigate("/workflows")} className="inline-flex items-center gap-2 rounded-lg bg-primary px-3.5 py-2 text-sm font-semibold text-primary-foreground shadow-orangeGlowStrong transition-shadow hover:shadow-orangeGlow active:scale-[0.98]">
          <Plus size={16} /> Create Item
        </button>
      </div>

      {isLoading ? (
        <div className="flex h-64 items-center justify-center text-muted-foreground"><Loader2 className="animate-spin" size={26} /></div>
      ) : items.length === 0 ? (
        <div className="flex h-64 flex-col items-center justify-center rounded-xl border border-dashed border-border bg-card/30 text-muted-foreground">
          <Package size={28} className="mb-3" />
          <p className="text-sm">No items yet. Start by creating one.</p>
          <button onClick={() => navigate("/workflows")} className="mt-4 inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground"><Plus size={15} /> Create Item</button>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {items.map((it) => (
            <ItemCard key={it.id} item={it} listing={listingForItem(it, index)} onGenerate={handleGenerate} generating={generate.isPending} />
          ))}
        </div>
      )}
    </div>
  );
}
