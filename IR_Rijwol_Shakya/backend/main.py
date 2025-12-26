import logging
import os
import time

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from search import SearchEngine, load_publications
from classification_ml import classify_document, get_model_info, train_models
from dotenv import load_dotenv

app = FastAPI()

# Load env config
load_dotenv()
DATA_DIR = os.getenv("DATA_DIR", "../data")
SEARCH_CACHE_TTL = int(os.getenv("SEARCH_CACHE_TTL", "60"))
SEARCH_CACHE_MAX = int(os.getenv("SEARCH_CACHE_MAX", "128"))

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("ir_backend")

# Allow all for local mobile dev; tighten in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load publications at startup
publications_data = load_publications(
    filepath_primary=os.path.join(DATA_DIR, "publications.json"),
    filepath_fallback=os.path.join(DATA_DIR, "publications_links.json"),
)
search_engine = SearchEngine(publications_data)

_search_cache = {}


def _cache_get(key: str):
    entry = _search_cache.get(key)
    if not entry:
        return None
    if time.time() - entry["ts"] > SEARCH_CACHE_TTL:
        _search_cache.pop(key, None)
        return None
    return entry["value"]


def _cache_set(key: str, value):
    if len(_search_cache) >= SEARCH_CACHE_MAX:
        oldest = min(_search_cache.items(), key=lambda item: item[1]["ts"])
        _search_cache.pop(oldest[0], None)
    _search_cache[key] = {"ts": time.time(), "value": value}


class ClassificationRequest(BaseModel):
    text: str
    model_type: str = "naive_bayes"


@app.get("/")
def read_root():
    return {"status": "ok"}

@app.get("/health")
def health():
    return {
        "status": "ok",
        "publications": len(publications_data),
        "cache_entries": len(_search_cache),
        "data_dir": DATA_DIR,
    }


@app.get("/search")
def search_publications(query: str = "", page: int = 1, size: int = 10):
    try:
        if not query.strip():
            results = []
            for pub in publications_data:
                item = dict(pub)
                item["score"] = 0.0
                if not isinstance(item.get("authors", []), list):
                    item["authors"] = (
                        item.get("authors", "").split(", ") if item.get("authors") else []
                    )
                return_fields = [
                    "title",
                    "link",
                    "authors",
                    "published_date",
                    "abstract",
                    "score",
                ]
                formatted_item = {k: item.get(k, "") for k in return_fields}
                results.append(formatted_item)
        else:
            key = query.strip().lower()
            cached = _cache_get(key)
            if cached is None:
                results = search_engine.search(query)
                _cache_set(key, results)
            else:
                results = cached

        start_idx = (page - 1) * size
        end_idx = start_idx + size
        paginated_results = results[start_idx:end_idx]

        return {
            "results": paginated_results,
            "total": len(results),
            "page": page,
            "size": size,
            "total_pages": (len(results) + size - 1) // size,
        }
    except Exception as e:
        logger.exception("Search failed")
        return {"error": str(e)}


@app.post("/classify")
def classify_text(request: ClassificationRequest):
    if not request.text.strip():
        return {"error": "Text is required for classification"}
    try:
        return classify_document(request.text, request.model_type)
    except Exception as e:
        return {"error": str(e)}


@app.get("/model-info")
def model_info(model_type: str = "naive_bayes"):
    try:
        return get_model_info(model_type)
    except Exception as e:
        return {"error": str(e)}


@app.post("/train-models")
def train_classification_models():
    try:
        results = train_models()
        return {"message": "Models trained successfully", "results": results}
    except Exception as e:
        return {"error": str(e)}
