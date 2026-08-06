"""Financial reporting: profit/fees/tax/margin from cost, price and workspace settings.

Sold items use their actual sale price (REALIZED figures); everything else is a
POTENTIAL figure based on current listings (or value estimates for unlisted
items) — the API labels this explicitly.
"""
import logging

import config
from deps import db

logger = logging.getLogger(__name__)


def _money(x):
    return round(float(x or 0), 2)


async def compute_financials(wid: str) -> dict:
    ws = await db.workspaces.find_one({"id": wid}, {"_id": 0}) or {}
    currency = ws.get("currency", "USD")
    tax_rate = round(float(ws.get("tax_rate") or 0) / 100.0, 4)
    fee_rate = config.MARKETPLACE_FEE_RATE

    items = await db.items.find({"workspace_id": wid}, {"_id": 0, "image": 0}).to_list(500)
    listings = await db.listings.find({"workspace_id": wid}, {"_id": 0}).to_list(500)
    price_by_item = {}
    for l in listings:
        if l.get("item_id") and l["item_id"] not in price_by_item:
            price_by_item[l["item_id"]] = l.get("suggested_price")

    rows = []
    for it in items:
        cost = it.get("cost")
        sold = bool(it.get("sold"))
        price = it.get("sale_price") if sold else price_by_item.get(it["id"])
        if price is None:
            price = (it.get("value_estimate") or {}).get("mid")
        if cost is None and price is None:
            continue
        cost = _money(cost) if cost is not None else None
        price = _money(price) if price is not None else None
        status = "sold" if sold else ("listed" if it["id"] in price_by_item else "unlisted")
        gross = _money(price - cost) if cost is not None and price is not None else None
        fees = _money(price * fee_rate) if price is not None else None
        tax = _money(gross * tax_rate) if gross is not None else None
        net = _money(gross - fees - tax) if gross is not None and fees is not None and tax is not None else None
        rows.append({
            "item_id": it["id"], "name": it["name"], "category": it.get("category"),
            "cost": cost, "price": price, "listed": it["id"] in price_by_item,
            "status": status, "sale_price": it.get("sale_price"),
            "gross_profit": gross, "estimated_fees": fees, "estimated_tax": tax, "net_profit": net,
            "margin_pct": round(net / price * 100, 1) if net is not None and price else None,
        })

    def total(key, pred):
        return _money(sum(r[key] for r in rows if r[key] is not None and pred(r)))

    sold_rows = [r for r in rows if r["status"] == "sold"]
    open_rows = [r for r in rows if r["status"] != "sold"]
    realized_revenue = _money(sum(r["price"] or 0 for r in sold_rows))
    potential_revenue = _money(sum(r["price"] or 0 for r in open_rows))
    realized_net = _money(sum(r["net_profit"] for r in sold_rows if r["net_profit"] is not None))
    potential_net = _money(sum(r["net_profit"] for r in open_rows if r["net_profit"] is not None))
    combined_revenue = realized_revenue + potential_revenue
    combined_net = realized_net + potential_net

    totals = {
        "items": len(rows),
        "listed": sum(1 for r in rows if r["listed"]),
        "sold": len(sold_rows),
        "invested": total("cost", lambda r: True),
        # Realized (completed sales)
        "realized_revenue": realized_revenue,
        "realized_gross_profit": total("gross_profit", lambda r: r["status"] == "sold"),
        "realized_fees": total("estimated_fees", lambda r: r["status"] == "sold"),
        "realized_tax": total("estimated_tax", lambda r: r["status"] == "sold"),
        "realized_net_profit": realized_net,
        "realized_margin_pct": round(realized_net / realized_revenue * 100, 1) if realized_revenue else None,
        # Potential (not yet sold)
        "potential_revenue": potential_revenue,
        "potential_gross_profit": total("gross_profit", lambda r: r["status"] != "sold"),
        "potential_fees": total("estimated_fees", lambda r: r["status"] != "sold"),
        "potential_tax": total("estimated_tax", lambda r: r["status"] != "sold"),
        "potential_net_profit": potential_net,
        "potential_margin_pct": round(potential_net / potential_revenue * 100, 1) if potential_revenue else None,
        # Combined
        "gross_profit": total("gross_profit", lambda r: True),
        "estimated_fees": total("estimated_fees", lambda r: True),
        "estimated_tax": total("estimated_tax", lambda r: True),
        "net_profit": _money(combined_net),
        "net_margin_pct": round(combined_net / combined_revenue * 100, 1) if combined_revenue else None,
    }

    agg = {}
    for r in rows:
        key = r["category"] or "Uncategorized"
        a = agg.setdefault(key, {"count": 0, "sold": 0, "invested": 0.0, "potential_revenue": 0.0, "gross_profit": 0.0, "net_profit": 0.0})
        a["count"] += 1
        a["sold"] += 1 if r["status"] == "sold" else 0
        a["invested"] += r["cost"] or 0
        a["potential_revenue"] += r["price"] or 0
        a["gross_profit"] += r["gross_profit"] or 0
        a["net_profit"] += r["net_profit"] or 0
    by_category = [
        {**{"category": k}, **{kk: _money(vv) for kk, vv in a.items() if kk != "count"}, "count": a["count"]}
        for k, a in sorted(agg.items(), key=lambda kv: -kv[1]["potential_revenue"])
    ]

    rows.sort(key=lambda r: (r["net_profit"] if r["net_profit"] is not None else -1e18), reverse=True)
    return {
        "currency": currency,
        "marketplace_fee_rate": fee_rate,
        "tax_rate": tax_rate,
        "note": "Sold items use actual sale prices (realized); unsold items are potential figures based on current listings (value estimates for unlisted items).",
        "totals": totals,
        "by_category": by_category,
        "items": rows[:100],
    }
