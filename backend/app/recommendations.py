from typing import Optional
from .models import Product

def score_product(product: Product, budget: Optional[float], occasion: Optional[str], material: Optional[str], category: Optional[str]) -> int:
    score = 50
    if budget is not None:
        if product.price <= budget:
            score += 25
        else:
            score -= min(25, int((product.price - budget) / max(budget, 1) * 20))
    if occasion and occasion.lower() in product.occasions.lower():
        score += 15
    if material and material.lower() in product.material.lower():
        score += 10
    if category and category.lower() in product.category.lower():
        score += 10
    return max(0, min(100, score))

def recommend(products, budget=None, occasion=None, material=None, category=None):
    rows = []
    for product in products:
        score = score_product(product, budget, occasion, material, category)
        rows.append((score, product))
    rows.sort(key=lambda row: (row[0], row[1].rating, -row[1].price), reverse=True)
    return rows
