// Derived, presentational metrics computed from REAL backend data.

export const CONDITION_SCORES = {
  New: 100,
  "Like New": 90,
  Good: 75,
  Fair: 55,
  Used: 45,
  "For Parts": 20,
};

export function conditionScore(condition) {
  return CONDITION_SCORES[condition] ?? 60;
}

// Build lookup maps from listings so items can find their generated listing.
export function buildListingIndex(listings = []) {
  const byItemId = new Map();
  const byName = new Map();
  for (const ls of listings) {
    if (ls.item_id && !byItemId.has(ls.item_id)) byItemId.set(ls.item_id, ls);
    if (ls.source_name && !byName.has(ls.source_name)) byName.set(ls.source_name, ls);
  }
  return { byItemId, byName };
}

export function listingForItem(item, index) {
  if (!index) return null;
  return index.byItemId.get(item.id) || index.byName.get(item.name) || null;
}

// AI confidence derived from data completeness + whether a listing exists.
export function confidenceFor(item, listing) {
  let score = 0;
  if (item.image) score += 1;
  if ((item.description || "").length > 60) score += 1;
  if (item.cost != null) score += 1;
  if (listing) score += 2;
  let level = "low";
  if (score >= 4) level = "high";
  else if (score >= 2) level = "medium";
  const pct = Math.min(100, 30 + score * 15);
  return { level, pct };
}

export function estimatedValue(item, listing) {
  if (listing && listing.suggested_price != null) return listing.suggested_price;
  if (item.cost != null) return item.cost;
  return null;
}

export function formatMoney(v) {
  if (v == null) return "\u2014";
  return "$" + Number(v).toLocaleString(undefined, { maximumFractionDigits: 0 });
}

export function formatTime(ts) {
  try {
    return new Date(ts).toLocaleString();
  } catch {
    return ts;
  }
}

// Generate AI insight cards from real items + listings data.
export function buildInsights(items = [], listings = []) {
  const index = buildListingIndex(listings);
  const insights = [];

  // Pricing opportunities: suggested price higher than seller cost.
  for (const item of items) {
    const ls = listingForItem(item, index);
    if (ls && item.cost != null && ls.suggested_price > item.cost) {
      const margin = ls.suggested_price - item.cost;
      const pct = Math.round((margin / item.cost) * 100);
      insights.push({
        id: "price-" + item.id,
        label: "Pricing Opportunity",
        tone: "green",
        title: item.name,
        summary: `Suggested price ${formatMoney(ls.suggested_price)} is ${pct}% above your cost (${formatMoney(item.cost)}). Potential margin of ${formatMoney(margin)}.`,
        confidence: Math.min(95, 60 + pct),
        action: "View in Market",
        to: "/market",
      });
    }
  }

  // Listing quality: items without a generated listing.
  const missing = items.filter((it) => !listingForItem(it, index));
  if (missing.length > 0) {
    insights.push({
      id: "quality-missing",
      label: "Listing Quality",
      tone: "orange",
      title: `${missing.length} item${missing.length > 1 ? "s" : ""} need a listing`,
      summary: `${missing.length} of your ${items.length} items don\u2019t have an AI-generated listing yet. Generating listings improves visibility and pricing.`,
      confidence: 80,
      action: "Open Workflow",
      to: "/workflows",
    });
  }

  // Data quality: items without images.
  const noImage = items.filter((it) => !it.image);
  if (noImage.length > 0) {
    insights.push({
      id: "quality-image",
      label: "Risk Flag",
      tone: "blue",
      title: `${noImage.length} item${noImage.length > 1 ? "s" : ""} missing photos`,
      summary: `Items with photos convert better. Add images to ${noImage.length} item${noImage.length > 1 ? "s" : ""} to boost buyer trust.`,
      confidence: 65,
      action: "Manage Items",
      to: "/items",
    });
  }

  return insights;
}

// High priority actions derived from real data.
export function buildPriorityActions(items = [], listings = []) {
  const index = buildListingIndex(listings);
  const actions = [];
  for (const item of items) {
    const ls = listingForItem(item, index);
    if (!ls) {
      actions.push({ id: "gen-" + item.id, severity: "high", label: "Generate listing", target: item.name, to: "/workflows" });
    } else if (!item.image) {
      actions.push({ id: "img-" + item.id, severity: "medium", label: "Add a photo", target: item.name, to: "/items" });
    }
  }
  return actions.slice(0, 6);
}
