#!/usr/bin/env python3

import csv
import os
import pickle
import re
from typing import Dict, List
from collections import Counter

import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB


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


class DocumentClassificationSystem:
    def __init__(self, model_type: str = "naive_bayes", data_dir: str = "../data"):
        self.model_type = model_type
        self.data_dir = data_dir
        self.stemmer = PorterStemmer()
        self.stop_words = set(stopwords.words("english"))
        self.keyword_map = self._build_keyword_map()
        self.vectorizer = None
        self.model = None
        self.is_trained = False

        self.categories = self._load_categories()
        self.label_encoder = {cat: idx for idx, cat in enumerate(self.categories)}
        self.label_decoder = {idx: cat for cat, idx in self.label_encoder.items()}
        self.training_documents = self._load_training_documents()

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
            documents = self._get_fallback_training_documents()
        return documents

    def _get_fallback_training_documents(self) -> List[Dict]:
        return [
            {
                "text": "Company reports record revenue and higher profit margins.",
                "category": "business",
            },
            {
                "text": "Startup secures new funding round to expand market operations.",
                "category": "business",
            },
            {
                "text": "Stock market volatility impacts investor confidence this quarter.",
                "category": "business",
            },
            {
                "text": "The new film premiere draws large crowds and critical acclaim.",
                "category": "entertainment",
            },
            {
                "text": "Music festival lineup includes award-winning international artists.",
                "category": "entertainment",
            },
            {
                "text": "Streaming series finale boosts subscription numbers worldwide.",
                "category": "entertainment",
            },
            {
                "text": "Researchers discover a new treatment for chronic disease.",
                "category": "health",
            },
            {
                "text": "Hospitals adopt improved surgical protocols to reduce recovery time.",
                "category": "health",
            },
            {
                "text": "Public health study links exercise to lower cardiovascular risk.",
                "category": "health",
            },
        ]

    def _build_keyword_map(self) -> Dict[str, List[str]]:
        return {
            "business": [
                "business",
                "account",
                "finance",
                "market",
                "revenue",
                "profit",
                "earnings",
                "stock",
                "investment",
                "merger",
                "startup",
                "budget",
                "sales",
                "supply",
                "logistics",
                "operations",
            ],
            "entertainment": [
                "entertainment",
                "movie",
                "movies",
                "film",
                "series",
                "television",
                "tv",
                "music",
                "concert",
                "festival",
                "award",
                "game",
                "gaming",
                "theater",
                "theatre",
                "podcast",
                "streaming",
                "animation",
                "show",
                "box",
                "office",
            ],
            "health": [
                "health",
                "hospital",
                "clinic",
                "patient",
                "vaccine",
                "disease",
                "treatment",
                "medical",
                "mental",
                "wellness",
                "epidemiology",
                "diagnosis",
                "trial",
                "drug",
                "nutrition",
                "care",
                "surgery",
                "public",
            ],
        }

    def _tokenize(self, text: str) -> List[str]:
        text = text.lower()
        text = re.sub(r"[^a-zA-Z\s]", " ", text)
        tokens = word_tokenize(text)
        return [
            self.stemmer.stem(token)
            for token in tokens
            if token not in self.stop_words and len(token) > 2
        ]

    def preprocess_text(self, text: str) -> str:
        return " ".join(self._tokenize(text))

    def _keyword_fallback(self, text: str) -> Dict | None:
        tokens = self._tokenize(text)
        if not tokens:
            return None
        scores = {}
        for category in self.categories:
            keywords = self.keyword_map.get(category, [])
            keyword_stems = {self.stemmer.stem(k) for k in keywords}
            score = sum(1 for token in tokens if token in keyword_stems)
            scores[category] = score

        total = sum(scores.values())
        if total == 0:
            return None

        predicted_category = max(scores.items(), key=lambda item: item[1])[0]
        probabilities = {cat: val / total for cat, val in scores.items()}
        confidence = probabilities.get(predicted_category, 0.0)
        explanation = (
            "The model used a keyword fallback because the input did not match "
            "the learned vocabulary. Add more descriptive text for higher confidence."
        )
        return {
            "predicted_category": predicted_category,
            "confidence": confidence,
            "probabilities": probabilities,
            "explanation": explanation,
            "model_used": f"{self.model_type} (keyword fallback)",
            "text_length": len(text),
            "processed_text_length": len(" ".join(tokens)),
        }

    def _no_signal_response(self, text: str, processed_text: str) -> Dict:
        total = max(1, len(self.categories))
        probabilities = {cat: 1 / total for cat in self.categories}
        predicted_category = self.categories[0] if self.categories else "unknown"
        explanation = (
            "The input did not contain enough known terms to score reliably. "
            "Try a longer sentence or add more context."
        )
        return {
            "predicted_category": predicted_category,
            "confidence": probabilities.get(predicted_category, 0.0),
            "probabilities": probabilities,
            "explanation": explanation,
            "model_used": f"{self.model_type} (no-signal fallback)",
            "text_length": len(text),
            "processed_text_length": len(processed_text),
        }

    def train_model(self) -> Dict:
        texts = [doc["text"] for doc in self.training_documents]
        labels = [self.label_encoder[doc["category"]] for doc in self.training_documents]
        processed_texts = [self.preprocess_text(text) for text in texts]
        num_classes = len(set(labels))
        counts = Counter(labels)
        can_stratify = all(v >= 2 for v in counts.values()) and num_classes > 1

        # If dataset is tiny, train on all data without a test split.
        if len(labels) < max(6, num_classes * 2):
            X_train = processed_texts
            y_train = labels
            X_test = []
            y_test = []
        else:
            test_size = max(0.2, num_classes / len(labels))
            X_train, X_test, y_train, y_test = train_test_split(
                processed_texts,
                labels,
                test_size=test_size,
                random_state=42,
                stratify=labels if can_stratify else None,
            )

        self.vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
        X_train_vec = self.vectorizer.fit_transform(X_train)

        if self.model_type == "naive_bayes":
            self.model = MultinomialNB()
        else:
            self.model = LogisticRegression(random_state=42, max_iter=1000)

        self.model.fit(X_train_vec, y_train)

        accuracy = None
        report = {}
        if X_test:
            X_test_vec = self.vectorizer.transform(X_test)
            y_pred = self.model.predict(X_test_vec)
            accuracy = accuracy_score(y_test, y_pred)
            target_names = [
                self.label_decoder[i] for i in sorted(self.label_decoder.keys())
            ]
            report = classification_report(
                y_test, y_pred, target_names=target_names, output_dict=True
            )

        self.is_trained = True
        return {
            "accuracy": accuracy,
            "classification_report": report,
            "model_type": self.model_type,
            "training_size": len(X_train),
            "test_size": len(X_test),
            "categories": self.categories,
        }

    def classify_text(self, text: str) -> Dict:
        if not self.is_trained:
            raise ValueError("Model must be trained before classification")

        processed_text = self.preprocess_text(text)
        if not processed_text:
            fallback = self._keyword_fallback(text)
            if fallback:
                return fallback
            return self._no_signal_response(text, processed_text)
        text_vec = self.vectorizer.transform([processed_text])
        if text_vec.nnz == 0:
            fallback = self._keyword_fallback(text)
            if fallback:
                return fallback
            return self._no_signal_response(text, processed_text)
        prediction = self.model.predict(text_vec)[0]
        probabilities = self.model.predict_proba(text_vec)[0]

        category = self.label_decoder[prediction]
        confidence = float(probabilities[prediction])
        prob_dict = {
            self.label_decoder[i]: float(prob) for i, prob in enumerate(probabilities)
        }

        explanation = self._generate_explanation(category, confidence, prob_dict)

        return {
            "predicted_category": category,
            "confidence": confidence,
            "probabilities": prob_dict,
            "explanation": explanation,
            "model_used": self.model_type,
            "text_length": len(text),
            "processed_text_length": len(processed_text),
        }

    def _generate_explanation(self, category: str, confidence: float, probabilities: Dict[str, float]) -> str:
        sorted_probs = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
        alternatives = [f"{cat}: {prob*100:.1f}%" for cat, prob in sorted_probs[1:]]
        if confidence >= 0.8:
            conf_level = "high"
        elif confidence >= 0.6:
            conf_level = "moderate"
        else:
            conf_level = "low"

        explanation = (
            f"The {self.model_type.replace('_', ' ')} model classified this text as "
            f"'{category}' with {confidence*100:.1f}% confidence. This is a {conf_level}-confidence prediction."
        )
        if alternatives:
            explanation += f" Alternative classifications: {', '.join(alternatives)}"
        return explanation

    def get_model_info(self) -> Dict:
        return {
            "model_type": self.model_type,
            "is_trained": self.is_trained,
            "total_documents": len(self.training_documents),
            "categories": self.categories,
        }

    def save_model(self, filepath: str):
        if not self.is_trained:
            raise ValueError("Model must be trained before saving")
        model_data = {
            "model": self.model,
            "vectorizer": self.vectorizer,
            "label_encoder": self.label_encoder,
            "label_decoder": self.label_decoder,
            "model_type": self.model_type,
            "categories": self.categories,
        }
        with open(filepath, "wb") as f:
            pickle.dump(model_data, f)

    def load_model(self, filepath: str):
        with open(filepath, "rb") as f:
            model_data = pickle.load(f)
        self.model = model_data["model"]
        self.vectorizer = model_data["vectorizer"]
        self.label_encoder = model_data["label_encoder"]
        self.label_decoder = model_data["label_decoder"]
        self.model_type = model_data["model_type"]
        self.categories = model_data["categories"]
        self.is_trained = True


_classifiers: Dict[str, DocumentClassificationSystem] = {}


def _get_classifier(model_type: str = "naive_bayes") -> DocumentClassificationSystem:
    if model_type not in _classifiers:
        _classifiers[model_type] = DocumentClassificationSystem(model_type=model_type)
        try:
            _classifiers[model_type].train_model()
        except Exception as e:
            print(f"Warning: Could not auto-train {model_type} model: {e}")
    return _classifiers[model_type]


def classify_document(text: str, model_type: str = "naive_bayes") -> Dict:
    classifier = _get_classifier(model_type)
    return classifier.classify_text(text)


def get_model_info(model_type: str = "naive_bayes") -> Dict:
    classifier = _get_classifier(model_type)
    return classifier.get_model_info()


def train_models() -> Dict:
    results = {}
    for model_type in ["naive_bayes", "logistic_regression"]:
        classifier = _get_classifier(model_type)
        training_result = classifier.train_model()
        results[model_type] = training_result
    return results
