#!/usr/bin/env python3

import csv
import os
import re
from collections import Counter, defaultdict
from typing import Dict, List

import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer


# Ensure NLTK resources are available
def _ensure_nltk():
    try:
        _ = stopwords.words("english")
        word_tokenize("test")
    except LookupError:
        nltk.download("stopwords")
        nltk.download("punkt")
        try:
            nltk.download("punkt_tab")
        except Exception:
            pass


_ensure_nltk()


class DocumentClusteringSystem:
    def __init__(self, data_dir: str = "../data", n_clusters: int | None = None):
        self.data_dir = data_dir
        self.stemmer = PorterStemmer()
        self.stop_words = set(stopwords.words("english"))
        self.vectorizer = None
        self.model = None
        self.is_trained = False

        self.categories = self._load_categories()
        self.training_documents = self._load_training_documents()
        self.n_clusters = n_clusters or max(2, len(self.categories))
        self.cluster_label_map: Dict[int, str] = {}

    def _load_categories(self) -> List[str]:
        categories_file = os.path.join(self.data_dir, "categories.csv")
        categories: List[str] = []
        try:
            with open(categories_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("category"):
                        categories.append(row["category"].strip())
        except FileNotFoundError:
            categories = ["business", "entertainment", "health"]
        return categories

    def _load_training_documents(self) -> List[Dict]:
        training_file = os.path.join(self.data_dir, "training_documents.csv")
        documents = []
        try:
            with open(training_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    documents.append({"text": row["text"], "category": row["category"]})
        except FileNotFoundError:
            documents = []
        return documents

    def preprocess_text(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^a-zA-Z\s]", " ", text)
        tokens = word_tokenize(text)
        processed_tokens = [
            self.stemmer.stem(token)
            for token in tokens
            if token not in self.stop_words and len(token) > 2
        ]
        return " ".join(processed_tokens)

    def train_model(self) -> Dict:
        if not self.training_documents:
            raise ValueError("No training documents available for clustering")

        texts = [doc["text"] for doc in self.training_documents]
        processed_texts = [self.preprocess_text(text) for text in texts]

        self.vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
        vectors = self.vectorizer.fit_transform(processed_texts)

        self.model = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
        cluster_assignments = self.model.fit_predict(vectors)

        label_counts = defaultdict(Counter)
        for cluster_id, doc in zip(cluster_assignments, self.training_documents):
            label_counts[cluster_id][doc["category"]] += 1

        self.cluster_label_map = {
            cluster_id: counts.most_common(1)[0][0] if counts else "unknown"
            for cluster_id, counts in label_counts.items()
        }

        cluster_sizes = Counter(cluster_assignments)
        self.is_trained = True

        return {
            "clusters": self.n_clusters,
            "cluster_sizes": {int(k): int(v) for k, v in cluster_sizes.items()},
            "cluster_labels": self.cluster_label_map,
            "total_documents": len(self.training_documents),
            "categories": self.categories,
        }

    def assign_cluster(self, text: str) -> Dict:
        if not self.is_trained:
            raise ValueError("Model must be trained before clustering")

        processed_text = self.preprocess_text(text)
        vector = self.vectorizer.transform([processed_text])
        cluster_id = int(self.model.predict(vector)[0])
        distances = self.model.transform(vector)[0]
        distance = float(distances[cluster_id])
        label = self.cluster_label_map.get(cluster_id, "unknown")

        return {
            "cluster_id": cluster_id,
            "cluster_label": label,
            "distance_to_centroid": distance,
            "text_length": len(text),
            "processed_text_length": len(processed_text),
        }

    def get_model_info(self) -> Dict:
        return {
            "is_trained": self.is_trained,
            "clusters": self.n_clusters,
            "total_documents": len(self.training_documents),
            "categories": self.categories,
            "cluster_labels": self.cluster_label_map,
        }


_clusterer: DocumentClusteringSystem | None = None


def _get_clusterer() -> DocumentClusteringSystem:
    global _clusterer
    if _clusterer is None:
        _clusterer = DocumentClusteringSystem()
        try:
            _clusterer.train_model()
        except Exception as e:
            print(f"Warning: Could not auto-train clustering model: {e}")
    return _clusterer


def cluster_document(text: str) -> Dict:
    clusterer = _get_clusterer()
    return clusterer.assign_cluster(text)


def get_cluster_model_info() -> Dict:
    clusterer = _get_clusterer()
    return clusterer.get_model_info()


def train_cluster_model() -> Dict:
    clusterer = _get_clusterer()
    return clusterer.train_model()
