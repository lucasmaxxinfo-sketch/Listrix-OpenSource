"""Per-workspace AI memory injected into every LLM prompt."""
from deps import db


async def build_ai_memory(wid):
    """Per-workspace AI memory: user preferences + derived behaviour. Belongs only to this workspace."""
    ws = await db.workspaces.find_one({"id": wid}, {"_id": 0}) or {}
    prefs = ws.get("ai_preferences", {})
    items = await db.items.find({"workspace_id": wid}, {"_id": 0, "category": 1}).to_list(500)
    cats = {}
    for it in items:
        c = it.get("category")
        if c:
            cats[c] = cats.get(c, 0) + 1
    frequent = sorted(cats, key=cats.get, reverse=True)[:5]
    applied = await db.suggestions.find({"workspace_id": wid, "status": "applied"}, {"_id": 0, "type": 1}).to_list(100)
    dismissed = await db.suggestions.find({"workspace_id": wid, "status": "dismissed"}, {"_id": 0, "type": 1}).to_list(100)
    return {
        "business_name": ws.get("name"),
        "currency": ws.get("currency", "USD"),
        "writing_style": prefs.get("writing_style"),
        "pricing_behavior": prefs.get("pricing_behavior"),
        "selling_strategy": prefs.get("selling_strategy"),
        "customer_comms_style": prefs.get("customer_comms_style"),
        "frequent_categories": frequent,
        "actions_applied": list({a["type"] for a in applied}),
        "actions_dismissed": list({d["type"] for d in dismissed}),
    }


def memory_block(mem):
    return (
        f"BUSINESS AI MEMORY (personalise to this workspace):\n"
        f"Business: {mem.get('business_name')} | Currency: {mem.get('currency')}\n"
        f"Preferred writing style: {mem.get('writing_style')}\n"
        f"Pricing behaviour: {mem.get('pricing_behavior')} | Selling strategy: {mem.get('selling_strategy')}\n"
        f"Customer comms style: {mem.get('customer_comms_style')}\n"
        f"Frequently sold categories: {mem.get('frequent_categories')}\n"
        f"Actions the business tends to apply: {mem.get('actions_applied')} | tends to reject: {mem.get('actions_dismissed')}\n"
    )
