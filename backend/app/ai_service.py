import httpx
from .config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from .models import Product
from .rag import build_context

SYSTEM_PROMPT = """You are the animated product character on ProductTalk AI, not a generic customer-support chatbot. Speak in first person as the selected product, warmly and concisely (2-5 sentences). Use ONLY the supplied retrieved product facts for factual claims. Never invent manufacturing origin, certifications, fabric percentages, durability, stock, delivery dates, or return policies. Clearly say when a detail is not available or not independently verified. You may give general styling advice, but label it as advice rather than a product fact. If asked whether to buy me, be balanced and mention a limitation when supported by the facts. Do not pretend demo review summaries are verified real customer reviews."""

def demo_answer(product: Product, question: str, context: str) -> str:
    q = question.lower()
    facts = context.lower()
    if any(k in q for k in ["where", "manufactur", "made", "origin", "country"]):
        if product.manufactured_in and product.origin_verified:
            return f"I'm the {product.name}, and my listing says I'm manufactured in {product.manufactured_in}. That origin field is marked as verified in this demo dataset. For a real store, the evidence behind that verification should also be retained."
        if product.manufactured_in:
            return f"I'm the {product.name}. My listing says {product.manufactured_in}, but that information is not independently verified in this demo. I'd recommend confirming it with the seller before relying on it."
        return f"I'm the {product.name}. My current product data doesn't specify my manufacturing country, so I don't want to guess. Ask the seller for a verified origin if that detail matters to you."
    if any(k in q for k in ["material", "fabric", "cotton", "linen", "summer", "hot", "breathable", "soft"]):
        return f"I'm the {product.name}. My listed material is {product.material}. That information alone can't guarantee how cool or soft I'll feel; fabric weight, construction, and personal preference matter too. The listing doesn't provide lab-tested performance details."
    if any(k in q for k in ["price", "cost", "worth", "expensive", "budget"]):
        return f"My listed price is ₹{product.price:.0f}. Whether I'm worth it depends on your budget and what matters to you. I'm described as {product.style.lower()}, and you can compare my material, fit, care needs, and available reviews before deciding."
    if any(k in q for k in ["occasion", "college", "office", "wear", "event", "style", "pair"]):
        return f"I'm styled as {product.style.lower()} and my listing suggests me for: {product.occasions}. For a simple outfit, you could pair me with jeans or chinos. That's styling advice, not a guarantee that I'll suit every dress code."
    if any(k in q for k in ["why not", "disadvantage", "negative", "downside", "bad", "regret"]):
        limitation = product.review_summary
        return f"A reason to pause before buying me: {product.material}. My listing doesn't provide every material detail, so check the label if fibre composition matters to you. The available demo note says: {limitation}"
    if any(k in q for k in ["review", "rating", "customer"]):
        return f"My demo listing shows a rating of {product.rating:.1f}/5 and this summary: {product.review_summary} Please note: these are sample portfolio data, not verified live customer reviews."
    if any(k in q for k in ["care", "wash", "clean", "iron"]):
        return f"My listed care guidance is: {product.care} Always follow the care label on the actual garment, because that is the most relevant instruction for the item you receive."
    return f"Hi, I'm {product.name}! I'm listed at ₹{product.price:.0f}, in {product.color.lower()}, with a {product.fit.lower()} and {product.style.lower()} style. My listed material is {product.material}. Ask me about my price, fabric, fit, care, origin, or occasions—and I'll tell you when a detail isn't available."

async def answer_product_question(product: Product, question: str):
    context, sources = build_context(product, question)
    if not LLM_API_KEY:
        return demo_answer(product, question, context), sources, "demo"
    payload = {
        "model": LLM_MODEL,
        "temperature": 0.3,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"PRODUCT: {product.name}\nRETRIEVED FACTS:\n{context}\n\nCUSTOMER QUESTION: {question}\nAnswer as the product character, grounded in the facts above."},
        ],
    }
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            response = await client.post(
                f"{LLM_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            answer = data["choices"][0]["message"]["content"].strip()
            if not answer:
                raise ValueError("The language model returned an empty answer")
            return answer, sources, "llm+r ag".replace(" ", "")
    except Exception:
        # The product remains usable if the optional provider is unavailable.
        return demo_answer(product, question, context), sources, "demo_fallback"
