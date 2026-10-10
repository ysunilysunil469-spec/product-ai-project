from backend.app.rag import retrieve_facts
from backend.app.recommendations import score_product
from backend.app.seed import SAMPLE_PRODUCTS
from backend.app.models import Product

def make_product():
    return Product(**SAMPLE_PRODUCTS[0])

def test_origin_question_retrieves_origin_fact():
    product = make_product()
    facts = retrieve_facts(product, "Where were you manufactured?")
    assert any(title == "Manufacturing origin" for title, _ in facts)

def test_budget_recommendation_score_is_bounded():
    product = make_product()
    score = score_product(product, 700, "college", "cotton", "T-shirts")
    assert 0 <= score <= 100
