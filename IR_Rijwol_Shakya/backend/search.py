import json
import math
import re
from typing import List, Dict

import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ---------- IO ----------
def load_publications(
    filepath_primary: str = "../data/publications.json",
    filepath_fallback: str = "../data/publications_links.json",
) -> List[Dict]:
    try:
        with open(filepath_primary, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        with open(filepath_fallback, "r", encoding="utf-8") as f:
            data = json.load(f)
    return data


def load_inverted_index(filepath: str = "../data/inverted_index.json") -> Dict:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


# ---------- NLTK helpers ----------
def _ensure_nltk():
    try:
        _ = stopwords.words("english")
        nltk.word_tokenize("ok")
    except LookupError:
        nltk.download("stopwords")
        nltk.download("punkt")
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
    if not v:
        return []
    if isinstance(v, list):
        if len(v) and isinstance(v[0], dict) and "name" in v[0]:
            return v
        return [{"name": str(x).strip(), "profile": None} for x in v if str(x).strip()]
    return [{"name": str(v).strip(), "profile": None}]


def _normalize_record(r: Dict) -> Dict:
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
    def __init__(self, publications: List[Dict], index_data: Dict = None):
        self.use_index = False
        if index_data and index_data.get("index") and index_data.get("docs"):
            self.use_index = True
            self.index = index_data.get("index", {})
            self.doc_len = index_data.get("doc_len", [])
            self.publications = index_data.get("docs", [])
        else:
            self.publications = [_normalize_record(p) for p in publications]
            self.searchable_content = []
            for pub in self.publications:
                title = pub.get("title", "")
                authors_objects = pub.get("authors", [])
                authors_text = " ".join(
                    [
                        author.get("name", "") if isinstance(author, dict) else str(author)
                        for author in authors_objects
                    ]
                )
                abstract = pub.get("abstract", "")
                blob = (
                    f"{preprocess_text(title)} {preprocess_text(authors_text)} "
                    f"{preprocess_text(abstract)}"
                )
                self.searchable_content.append(blob)

            self.vectorizer = TfidfVectorizer()
            self.tfidf_matrix = self.vectorizer.fit_transform(self.searchable_content)

    def search(self, query: str) -> List[Dict]:
        if not query.strip():
            return []

        if self.use_index:
            tokens = preprocess_text(query).split()
            scores: Dict[int, float] = {}
            n_docs = len(self.publications)
            for term in tokens:
                entry = self.index.get(term)
                if not entry:
                    continue
                df = entry.get("df", 0) or 0
                idf = math.log((n_docs + 1) / (df + 1)) + 1.0
                postings = entry.get("postings", {})
                for doc_id_str, tf in postings.items():
                    doc_id = int(doc_id_str)
                    length = self.doc_len[doc_id] if doc_id < len(self.doc_len) else 1
                    score = (float(tf) / max(1, length)) * idf
                    scores[doc_id] = scores.get(doc_id, 0.0) + score

            ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            results = []
            for doc_id, score in ranked:
                if score < 0.01:
                    continue
                item = dict(self.publications[doc_id])
                item["score"] = round(float(score), 2)
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

        q_vec = self.vectorizer.transform([preprocess_text(query)])
        sims = cosine_similarity(q_vec, self.tfidf_matrix).flatten()
        top_idx = sims.argsort()[::-1]
        results = []
        for i in top_idx:
            score = float(sims[i])
            if score < 0.01:
                continue
            item = dict(self.publications[i])
            item["score"] = round(score, 2)
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
