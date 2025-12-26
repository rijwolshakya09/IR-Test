# search_engine.py  — upgraded for crawler with abstract + published_date
import json, re, nltk
from typing import List, Dict
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ---------- IO ----------
def load_publications(
    filepath_primary="../data/publications.json",
    filepath_fallback="../data/publications_detailed.json",
) -> List[Dict]:
    """
    Loads crawler output. Prefers publications.json (new crawler), falls back to publications_detailed.json.
    """
    try:
        with open(filepath_primary, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        with open(filepath_fallback, "r", encoding="utf-8") as f:
            data = json.load(f)
    return data


# ---------- NLTK helpers ----------
def _ensure_nltk():
    try:
        _ = stopwords.words("english")
        nltk.word_tokenize("ok")
    except LookupError:
        nltk.download("stopwords")
        nltk.download("punkt")
        # Some environments need this extra package; ignore if unavailable
        try:
            nltk.download("punkt_tab")
        except Exception:
            pass


_ensure_nltk()
STEM = PorterStemmer()
STOP = set(stopwords.words("english"))


def preprocess_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = nltk.word_tokenize(text)
    return " ".join(STEM.stem(t) for t in tokens if t not in STOP and len(t) > 1)


# ---------- normalization ----------
def _ensure_list_of_authors(v):
    """Ensure authors is a list of author objects with name and profile."""
    if not v:
        return []
    if isinstance(v, list):
        # if already a list of author objects, return as is
        if len(v) and isinstance(v[0], dict) and "name" in v[0]:
            return v
        # if list of strings, convert to author objects
        return [{"name": str(x).strip(), "profile": None} for x in v if str(x).strip()]
    # if a single string slipped in, convert to author object
    return [{"name": str(v).strip(), "profile": None}]


def _ensure_list_of_str(v):
    """Convert authors to list of strings for search indexing."""
    if not v:
        return []
    if isinstance(v, list):
        # if list of author objects, extract names
        if len(v) and isinstance(v[0], dict) and "name" in v[0]:
            return [str(d.get("name", "")).strip() for d in v if isinstance(d, dict)]
        # if list of strings, return as is
        return [str(x).strip() for x in v]
    # if a single string slipped in, keep it as a single element
    return [str(v).strip()]


def _normalize_record(r: Dict) -> Dict:
    # unify date
    date_val = r.get("date") or r.get("published_date") or ""
    authors = _ensure_list_of_authors(r.get("authors", []))
    abstract = r.get("abstract", "") or ""
    out = dict(r)
    out["published_date"] = date_val
    out["authors"] = authors
    out["abstract"] = abstract
    return out


# ---------- Engine ----------
class SearchEngine:
    def __init__(self, publications: List[Dict]):
        # normalize all records so frontend fields always exist
        self.publications = [_normalize_record(p) for p in publications]

        # Build searchable strings (title + authors + abstract)
        self.searchable_content = []
        for pub in self.publications:
            title = pub.get("title", "")
            # Extract author names for search indexing
            authors_objects = pub.get("authors", [])
            authors_text = " ".join(
                [
                    author.get("name", "") if isinstance(author, dict) else str(author)
                    for author in authors_objects
                ]
            )
            abstract = pub.get("abstract", "")
            blob = f"{preprocess_text(title)} {preprocess_text(authors_text)} {preprocess_text(abstract)}"
            self.searchable_content.append(blob)

        # TF-IDF over combined text
        self.vectorizer = TfidfVectorizer()
        self.tfidf_matrix = self.vectorizer.fit_transform(self.searchable_content)

    def search(self, query: str) -> List[Dict]:
        if not query.strip():
            return []

        q_vec = self.vectorizer.transform([preprocess_text(query)])
        sims = cosine_similarity(q_vec, self.tfidf_matrix).flatten()

        # top 50 with a small threshold
        top_idx = sims.argsort()[-50:][::-1]
        results = []
        for i in top_idx:
            score = float(sims[i])
            if score < 0.01:
                continue
            item = dict(self.publications[i])  # copy
            item["score"] = round(score, 2)

            # Ensure required fields exist for frontend
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

        return results
