# ProductTalk AI

A portfolio-ready AI shopping demo where **products are animated characters**. Select a product, press **Talk to this product**, and the product character speaks about its own verified product facts. It is intentionally more than a generic chatbot: the character animates, speaks using browser text-to-speech, can listen to voice input where supported, and answers from retrieved product data.

## Included
- FastAPI REST backend
- SQLite database via SQLAlchemy (auto-created and seeded on first run)
- Product discovery, search, product details, and transparent match scores
- Lightweight retrieval-augmented generation (RAG): relevant product facts are retrieved before answering
- Optional OpenAI-compatible LLM integration; works without an API key in deterministic demo mode
- Animated product character using CSS and SVG-like CSS shapes; browser speech synthesis
- Product comparison and product recommendation endpoints
- Basic API health endpoint and API docs

## Run locally (Windows)
1. Install Python 3.10+.
2. Open Command Prompt inside this folder.
3. Create and activate a virtual environment:
   ```bat
   py -m venv .venv
   .venv\Scripts\activate
   ```
4. Install dependencies:
   ```bat
   pip install -r requirements.txt
   ```
5. Optional: copy `.env.example` to `.env` and set `LLM_API_KEY`. Without it, demo mode still works.
6. Start the app:
   ```bat
   uvicorn backend.app.main:app --reload
   ```
7. Open http://127.0.0.1:8000
8. API documentation: http://127.0.0.1:8000/docs

## Environment variables
- `DATABASE_URL` (default: `sqlite:///./producttalk.db`)
- `LLM_API_KEY` (optional)
- `LLM_BASE_URL` (default: `https://api.openai.com/v1`)
- `LLM_MODEL` (default: `gpt-4o-mini`)
- `CORS_ORIGINS` (default: `*`; restrict this for production)

The LLM integration uses the OpenAI-compatible `POST /chat/completions` API. Configure a provider that supports that API shape. Keep your API key on the server; never put it in frontend JavaScript.

## API overview
- `GET /api/health`
- `GET /api/products?q=&category=`
- `GET /api/products/{product_id}`
- `POST /api/talk/{product_id}` with `{ "message": "Is this good for summer?" }`
- `POST /api/recommendations` with `{ "budget": 1000, "occasion": "college", "material": "cotton" }`
- `GET /api/compare?ids=1,2`

## RAG design
The RAG module ranks product fact snippets using token overlap, then supplies the best matching facts to the LLM. This is a deliberately simple, dependency-light retrieval baseline for learning and interviews—not a production vector search system. A natural next step is adding embeddings and a vector database, then evaluating retrieval precision and answer faithfulness.

## Important accuracy note
Demo catalog details are illustrative. The assistant is instructed to say when information is unavailable and not to invent manufacturing origin, certifications, or other facts. Replace sample records with verified product data before using this for real commerce.

## Deployment
This is a single FastAPI service serving both API and frontend static files, so it can be deployed as one Python web service on platforms that support Python apps (for example, Render or Railway). Use:
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`

Set environment variables in your hosting dashboard. For persistent production data, use PostgreSQL and set `DATABASE_URL` to your provider's SQLAlchemy connection URL. A local SQLite file may not persist across some hosting redeploys.
