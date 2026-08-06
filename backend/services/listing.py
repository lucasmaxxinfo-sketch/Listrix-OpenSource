"""AI marketplace-listing generation."""
from services import llm
from services.memory import build_ai_memory, memory_block

LISTING_SYSTEM = "You are an expert e-commerce copywriter. You ALWAYS respond with a single valid JSON object and nothing else."


async def generate_listing_ai(wid, req):
    mem = await build_ai_memory(wid)
    cost_line = f"Seller cost / anchor price: {req.cost}\n" if req.cost is not None else ""
    prompt = (
        f"{memory_block(mem)}\nCreate a polished marketplace listing matching the business's preferred style.\n\n"
        f"Name: {req.name}\nDescription: {req.description}\nCondition: {req.condition}\n{cost_line}\n"
        'Respond with ONLY a JSON object: { "listing_title": string (<=80 chars), "listing_description": string, '
        '"suggested_price": number, "hashtags": array of 5-8 keyword strings without # }'
    )
    data = await llm.call_llm(LISTING_SYSTEM, prompt)
    tags = data.get("hashtags") or []
    if not isinstance(tags, list):
        tags = [str(tags)]
    tags = [str(t).lstrip("#").strip() for t in tags if str(t).strip()]
    dp = req.cost if req.cost is not None else 0
    return {"listing_title": str(data.get("listing_title", "")).strip(),
            "listing_description": str(data.get("listing_description", "")).strip(),
            "suggested_price": float(data.get("suggested_price", dp)), "hashtags": tags}
