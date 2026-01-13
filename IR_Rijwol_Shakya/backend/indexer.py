#!/usr/bin/env python3
import argparse
import json
import os
import re
from collections import Counter
from typing import Dict, List

import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize


def _ensure_nltk():
    try:
        _ = stopwords.words("english")
        word_tokenize("ok")
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


def preprocess_text(text: str) -> List[str]:
    if not text:
        return []
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = word_tokenize(text)
    return [STEM.stem(t) for t in tokens if t not in STOP and len(t) > 1]


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


def load_publications(primary_path: str, fallback_path: str) -> List[Dict]:
    try:
        with open(primary_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        with open(fallback_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    return data


def build_inverted_index(publications: List[Dict]) -> Dict:
    docs = [_normalize_record(p) for p in publications]
    index: Dict[str, Dict] = {}
    doc_len: List[int] = []

    for doc_id, pub in enumerate(docs):
        title = pub.get("title", "")
        authors_objects = pub.get("authors", [])
        authors_text = " ".join(
            [
                author.get("name", "") if isinstance(author, dict) else str(author)
                for author in authors_objects
            ]
        )
        abstract = pub.get("abstract", "")
        tokens = preprocess_text(f"{title} {authors_text} {abstract}")
        doc_len.append(max(1, len(tokens)))
        counts = Counter(tokens)
        for term, tf in counts.items():
            entry = index.get(term)
            if not entry:
                entry = {"df": 0, "postings": {}}
                index[term] = entry
            entry["postings"][str(doc_id)] = tf

    for term, entry in index.items():
        entry["df"] = len(entry["postings"])

    return {"docs": docs, "doc_len": doc_len, "index": index}


def main():
    ap = argparse.ArgumentParser(description="Build inverted index for publications")
    ap.add_argument("--data-dir", default="../data", help="Data directory")
    ap.add_argument(
        "--input",
        default="publications.json",
        help="Input JSON file within data dir",
    )
    ap.add_argument(
        "--fallback",
        default="publications_links.json",
        help="Fallback input JSON file within data dir",
    )
    ap.add_argument(
        "--output",
        default="inverted_index.json",
        help="Output JSON file within data dir",
    )
    args = ap.parse_args()

    data_dir = os.path.abspath(args.data_dir)
    primary_path = os.path.join(data_dir, args.input)
    fallback_path = os.path.join(data_dir, args.fallback)
    out_path = os.path.join(data_dir, args.output)

    publications = load_publications(primary_path, fallback_path)
    index_data = build_inverted_index(publications)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    print(f"[INDEX] Saved inverted index to {out_path}")


if __name__ == "__main__":
    main()
