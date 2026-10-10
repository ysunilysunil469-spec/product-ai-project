import re
from typing import List, Tuple
from .models import Product

STOP_WORDS = {"the", "a", "an", "is", "are", "am", "i", "you", "your", "me", "it", "to", "for", "of", "and", "in", "on", "do", "does", "this", "that", "with", "my", "we", "be", "can", "what", "where", "how", "should", "would", "tell", "about", "buy", "wear", "product"}

def tokens(text: str):
    return {w for w in re.findall(r"[a-z0-9]+", (text or "").lower()) if len(w) > 1 and w not in STOP_WORDS}

def product_facts(product: Product) -> List[Tuple[str, str]]:
    facts = [
        ("Price", f"Listed price: ₹{product.price:.0f}."),
        ("Material", f"Material: {product.material}."),
        ("Colour", f"Colour: {product.color}."),
        ("Fit", f"Fit: {product.fit}."),
        ("Style", f"Style: {product.style}."),
        ("Occasions", f"Listed occasions: {product.occasions}."),
        ("Description", f"Description: {product.description}"),
        ("Care", f"Care: {product.care}"),
        ("Manufacturing origin", f"Manufacturing origin: {product.manufactured_in if product.manufactured_in else 'Not provided in the product data'}."),
        ("Rating and review summary", f"Demo rating: {product.rating:.1f}/5. Review summary: {product.review_summary}"),
    ]
    return facts

def retrieve_facts(product: Product, question: str, limit: int = 5):
    q = tokens(question)
    ranked = []
    for title, fact in product_facts(product):
        ft = tokens(title + " " + fact)
        overlap = len(q & ft)
        # Small boosts for clear intent so exact fields are retrieved reliably.
        lower = question.lower()
        if any(x in lower for x in ["price", "cost", "expensive", "budget"]):
            overlap += 2 if title == "Price" else 0
        if any(x in lower for x in ["material", "fabric", "cotton", "linen", "summer", "hot", "breathable"]):
            overlap += 2 if title == "Material" else 0
        if any(x in lower for x in ["manufactur", "made", "origin", "country", "where from"]):
            overlap += 2 if title == "Manufacturing origin" else 0
        if any(x in lower for x in ["occasion", "college", "office", "wear", "event"]):
            overlap += 2 if title == "Occasions" else 0
        ranked.append((overlap, title, fact))
    ranked.sort(key=lambda row: row[0], reverse=True)
    selected = [(title, fact) for score, title, fact in ranked[:limit] if score > 0]
    if not selected:
        selected = [(title, fact) for title, fact in product_facts(product)[:4]]
    return selected

def build_context(product: Product, question: str):
    selected = retrieve_facts(product, question)
    return "\n".join(f"- {title}: {fact}" for title, fact in selected), [title for title, _ in selected]
