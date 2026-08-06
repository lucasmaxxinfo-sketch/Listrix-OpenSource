"""Visual intelligence: prompt construction + structured parsing of vision results."""
VISION_SYSTEM = "You are a visual resale expert, pricing analyst and marketing strategist. You ALWAYS respond with a single valid JSON object and nothing else."


def build_vision_prompt(hint):
    hl = f"Seller hint: {hint}\n" if hint else ""
    return ("Analyse this product image for resale.\n" + hl +
            "Respond with ONLY JSON with keys: item_type(string), category(string), brand(string|null), "
            'condition_guess(one of "New","Like New","Good","Fair","Used","For Parts"), features([strings]), '
            "suggested_title(string), suggested_description(string), suggested_price(number), "
            "value_estimate({low,mid,high,confidence(0-100),reasoning}), market_positioning(one of budget,competitive,premium)")


def parse_vision_result(data):
    ve = data.get("value_estimate") or {}
    return {"item_type": str(data.get("item_type", "")).strip(), "category": str(data.get("category", "")).strip(),
            "brand": data.get("brand"), "condition_guess": str(data.get("condition_guess", "Good")).strip(),
            "features": [str(f) for f in (data.get("features") or [])][:10],
            "suggested_title": str(data.get("suggested_title", "")).strip(),
            "suggested_description": str(data.get("suggested_description", "")).strip(),
            "suggested_price": float(data.get("suggested_price", ve.get("mid", 0) or 0)),
            "value_estimate": {"low": float(ve.get("low", 0) or 0), "mid": float(ve.get("mid", 0) or 0),
                               "high": float(ve.get("high", 0) or 0), "confidence": float(ve.get("confidence", 50) or 50),
                               "reasoning": str(ve.get("reasoning", "")).strip()},
            "market_positioning": str(data.get("market_positioning", "competitive")).strip()}
