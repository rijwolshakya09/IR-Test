from fastapi import FastAPI
from pydantic import BaseModel
from search import SearchEngine, load_publications
from classification_ml import classify_document, get_model_info, train_models
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3000/",
    "http://127.0.0.1:3000/",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load publications data once when the app starts
publications_data = load_publications()
search_engine = SearchEngine(publications_data)


# Pydantic models for request bodies
class ClassificationRequest(BaseModel):
    text: str
    model_type: str = "naive_bayes"  # 'naive_bayes' or 'logistic_regression'


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/search")
def search_publications(query: str = "", page: int = 1, size: int = 30):
    try:
        # If no query provided, return all publications
        if not query.strip():
            results = []
            for pub in publications_data:
                item = dict(pub)  # copy
                item["score"] = 0.0  # no search score for all results

                # Ensure authors is a list
                if not isinstance(item.get("authors", []), list):
                    item["authors"] = (
                        item.get("authors", "").split(", ")
                        if item.get("authors")
                        else []
                    )

                # Return standard fields
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
            # Perform search using the initialized search engine
            results = search_engine.search(query)

        # Apply pagination
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
        return {"error": str(e)}


@app.post("/classify")
def classify_text(request: ClassificationRequest):
    """
    Classify text into business, health, or politics categories using ML models
    """
    try:
        if not request.text.strip():
            return {"error": "Text is required for classification"}

        result = classify_document(request.text, request.model_type)
        return result
    except Exception as e:
        return {"error": str(e)}


@app.get("/model-info")
def model_info(model_type: str = "naive_bayes"):
    """
    Get information about the classification model
    """
    try:
        info = get_model_info(model_type)
        return info
    except Exception as e:
        return {"error": str(e)}


@app.post("/train-models")
def train_classification_models():
    """
    Retrain the classification models (for demonstration purposes)
    """
    try:
        results = train_models()
        return {"message": "Models trained successfully", "results": results}
    except Exception as e:
        return {"error": str(e)}
