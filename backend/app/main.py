from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from .models import Product
from .schemas import TalkRequest, TalkResponse, RecommendationRequest
from .seed import seed_products
from .ai_service import answer_product_question
from .recommendations import recommend
from .config import CORS_ORIGINS

BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(title="ProductTalk AI", description="Animated talking products with RAG-grounded answers and product recommendations.", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
Base.metadata.create_all(bind=engine)
with next(get_db()) as db:
    seed_products(db)

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "ProductTalk AI", "llm_enabled": bool(__import__('backend.app.config', fromlist=['LLM_API_KEY']).LLM_API_KEY)}

def serialize_product(p: Product, match_score=None):
    return {
        "id": p.id, "name": p.name, "category": p.category, "price": p.price,
        "original_price": p.original_price, "material": p.material, "color": p.color,
        "fit": p.fit, "style": p.style, "occasions": p.occasions, "description": p.description,
        "care": p.care, "manufactured_in": p.manufactured_in, "origin_verified": bool(p.origin_verified),
        "rating": p.rating, "review_summary": p.review_summary, "image_emoji": p.image_emoji,
        "accent": p.accent, "match_score": match_score,
    }

@app.get("/api/products")
def list_products(q: Optional[str] = None, category: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Product)
    if category and category.lower() != "all":
        query = query.filter(Product.category.ilike(f"%{category}%"))
    products = query.order_by(Product.id).all()
    if q:
        words = q.lower().split()
        products = [p for p in products if any(w in f"{p.name} {p.category} {p.material} {p.color} {p.style} {p.occasions}".lower() for w in words)]
    return [serialize_product(p) for p in products]

@app.get("/api/products/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return serialize_product(product)

@app.post("/api/talk/{product_id}", response_model=TalkResponse)
async def talk_to_product(product_id: int, payload: TalkRequest, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    answer, sources, mode = await answer_product_question(product, payload.message.strip())
    return TalkResponse(product_id=product.id, product_name=product.name, answer=answer, sources=sources, mode=mode)

@app.post("/api/recommendations")
def get_recommendations(payload: RecommendationRequest, db: Session = Depends(get_db)):
    products = db.query(Product).all()
    ranked = recommend(products, payload.budget, payload.occasion, payload.material, payload.category)
    return [serialize_product(p, score) for score, p in ranked[:6]]

@app.get("/api/compare")
def compare_products(ids: str = Query(..., description="Comma-separated product IDs"), db: Session = Depends(get_db)):
    try:
        product_ids = list(dict.fromkeys(int(value.strip()) for value in ids.split(",") if value.strip()))
    except ValueError:
        raise HTTPException(status_code=400, detail="ids must be comma-separated integers")
    if len(product_ids) < 2 or len(product_ids) > 4:
        raise HTTPException(status_code=400, detail="Choose between 2 and 4 products to compare")
    products = db.query(Product).filter(Product.id.in_(product_ids)).all()
    by_id = {p.id: p for p in products}
    if len(by_id) != len(product_ids):
        raise HTTPException(status_code=404, detail="One or more products were not found")
    return [serialize_product(by_id[pid]) for pid in product_ids]

@app.get("/", include_in_schema=False)
def home():
    return FileResponse(FRONTEND_DIR / "index.html")

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
