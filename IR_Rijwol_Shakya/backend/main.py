import logging
import os
import re
import time

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from search import SearchEngine, load_publications, load_inverted_index
from classification_ml import classify_document, get_model_info, train_models
from clustering_ml import cluster_document, get_cluster_model_info, train_cluster_model
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
index_data = load_inverted_index(os.path.join(DATA_DIR, "inverted_index.json"))
search_engine = SearchEngine(publications_data, index_data=index_data)

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


class ClusteringRequest(BaseModel):
    text: str


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

def _extract_year(date_str: str) -> int:
    if not date_str:
        return 0
    match = re.search(r"(19|20)\d{2}", str(date_str))
    return int(match.group()) if match else 0


def _matches_author(item, author_query: str) -> bool:
    if not author_query:
        return True
    aq = author_query.strip().lower()
    authors = item.get("authors", [])
    if isinstance(authors, list):
        for a in authors:
            name = ""
            if isinstance(a, dict):
                name = a.get("name", "")
            else:
                name = str(a)
            if aq in name.lower():
                return True
    return False


def _matches_year(item, year_from: int, year_to: int) -> bool:
    if not year_from and not year_to:
        return True
    year = _extract_year(item.get("published_date", ""))
    if year_from and year < year_from:
        return False
    if year_to and year > year_to:
        return False
    return year != 0


@app.get("/search")
def search_publications(
    query: str = "",
    page: int = 1,
    size: int = 10,
    author: str = "",
    year_from: int = 0,
    year_to: int = 0,
    sort: str = "score",
):
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
            key = "|".join(
                [
                    query.strip().lower(),
                    author.strip().lower(),
                    str(year_from or ""),
                    str(year_to or ""),
                    sort.strip().lower(),
                ]
            )
            cached = _cache_get(key)
            if cached is None:
                results = search_engine.search(query)
                _cache_set(key, results)
            else:
                results = cached

        if author.strip():
            results = [r for r in results if _matches_author(r, author)]
        if year_from or year_to:
            results = [r for r in results if _matches_year(r, year_from, year_to)]

        if sort == "date":
            results.sort(key=lambda r: _extract_year(r.get("published_date", "")), reverse=True)
        elif sort == "title":
            results.sort(key=lambda r: (r.get("title") or "").lower())
        else:
            results.sort(key=lambda r: r.get("score", 0.0), reverse=True)

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


@app.post("/cluster")
def cluster_text(request: ClusteringRequest):
    if not request.text.strip():
        return {"error": "Text is required for clustering"}
    try:
        return cluster_document(request.text)
    except Exception as e:
        return {"error": str(e)}


@app.get("/cluster-model-info")
def cluster_model_info():
    try:
        return get_cluster_model_info()
    except Exception as e:
        return {"error": str(e)}


@app.post("/train-cluster-model")
def train_clustering_model():
    try:
        results = train_cluster_model()
        return {"message": "Cluster model trained successfully", "results": results}
    except Exception as e:
        return {"error": str(e)}
