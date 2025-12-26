#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Document Classification System - CSV-based Version
Implements a proper machine learning-based text classification system
following the assignment requirements:
1. Load documents from CSV files for easy scaling to 500+ documents
2. Train a standard classification model (Naive Bayes, Logistic Regression)
3. Classify new documents using the trained model
"""

import json
import re
import pickle
import os
import csv
from typing import Dict, List, Tuple, Optional
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
import numpy as np


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
    def __init__(self, model_type="naive_bayes", data_dir="../data"):
        """
        Initialize the classification system

        Args:
            model_type (str): 'naive_bayes' or 'logistic_regression'
            data_dir (str): Directory containing CSV data files
        """
        self.model_type = model_type
        self.data_dir = data_dir
        self.stemmer = PorterStemmer()
        self.stop_words = set(stopwords.words("english"))
        self.vectorizer = None
        self.model = None
        self.is_trained = False

        # Load categories and create label encoders
        self.categories = self._load_categories()
        self.label_encoder = {cat: idx for idx, cat in enumerate(self.categories)}
        self.label_decoder = {idx: cat for cat, idx in self.label_encoder.items()}

        # Load training documents from CSV
        self.training_documents = self._load_training_documents()

    def _load_categories(self) -> List[str]:
        """Load categories from CSV file"""
        categories_file = os.path.join(self.data_dir, "categories.csv")
        categories = []

        try:
            with open(categories_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    categories.append(row["category"])
        except FileNotFoundError:
            # Fallback to default categories
            categories = ["politics", "business", "health"]

        return categories

    def _load_training_documents(self) -> List[Dict]:
        """Load training documents from CSV file"""
        training_file = os.path.join(self.data_dir, "training_documents.csv")
        documents = []

        try:
            with open(training_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    documents.append({"text": row["text"], "category": row["category"]})
            print(f"Loaded {len(documents)} training documents from {training_file}")
        except FileNotFoundError:
            print(f"Training file {training_file} not found, using fallback data")
            documents = self._get_fallback_training_documents()

        return documents

    def _get_fallback_training_documents(self) -> List[Dict]:
        """
        Fallback training documents if CSV file is not available
        """
        return [
            {
                "text": "The government announced new policies to tackle climate change and economic issues",
                "category": "politics",
            },
            {
                "text": "Parliament voted on controversial legislation affecting immigration and social services",
                "category": "politics",
            },
            {
                "text": "The company reported strong quarterly earnings with increased revenue and market expansion",
                "category": "business",
            },
            {
                "text": "Tech startup secured funding for innovative product development and market growth",
                "category": "business",
            },
            {
                "text": "Medical researchers discovered breakthrough treatment for chronic disease management",
                "category": "health",
            },
            {
                "text": "Healthcare system implemented new patient safety protocols and quality improvements",
                "category": "health",
            },
        ]

    def get_training_stats(self) -> Dict:
        """Get statistics about the training data"""
        stats = {}
        for category in self.categories:
            count = sum(
                1 for doc in self.training_documents if doc["category"] == category
            )
            stats[category] = count
        stats["total"] = len(self.training_documents)
        return stats

    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text for classification

        Args:
            text (str): Raw text to preprocess

        Returns:
            str: Preprocessed text
        """
        # Convert to lowercase
        text = text.lower()

        # Remove punctuation and special characters
        text = re.sub(r"[^a-zA-Z\s]", " ", text)

        # Tokenize
        tokens = word_tokenize(text)

        # Remove stopwords and stem
        processed_tokens = [
            self.stemmer.stem(token)
            for token in tokens
            if token not in self.stop_words and len(token) > 2
        ]

        return " ".join(processed_tokens)

    def train_model(self) -> Dict:
        """
        Train the classification model

        Returns:
            Dict: Training results including accuracy and classification report
        """
        # Prepare training data
        texts = [doc["text"] for doc in self.training_documents]
        labels = [
            self.label_encoder[doc["category"]] for doc in self.training_documents
        ]

        # Preprocess texts
        processed_texts = [self.preprocess_text(text) for text in texts]

        # Split data for training and testing
        X_train, X_test, y_train, y_test = train_test_split(
            processed_texts, labels, test_size=0.2, random_state=42, stratify=labels
        )

        # Vectorize text
        self.vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
        X_train_vec = self.vectorizer.fit_transform(X_train)
        X_test_vec = self.vectorizer.transform(X_test)

        # Train model
        if self.model_type == "naive_bayes":
            self.model = MultinomialNB()
        else:  # logistic_regression
            self.model = LogisticRegression(random_state=42, max_iter=1000)

        self.model.fit(X_train_vec, y_train)

        # Evaluate model
        y_pred = self.model.predict(X_test_vec)
        accuracy = accuracy_score(y_test, y_pred)

        # Generate classification report
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
        """
        Classify a given text

        Args:
            text (str): Text to classify

        Returns:
            Dict: Classification results
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before classification")

        # Preprocess text
        processed_text = self.preprocess_text(text)

        # Vectorize
        text_vec = self.vectorizer.transform([processed_text])

        # Predict
        prediction = self.model.predict(text_vec)[0]
        probabilities = self.model.predict_proba(text_vec)[0]

        # Prepare results
        category = self.label_decoder[prediction]
        confidence = probabilities[prediction]

        # Get probabilities for all categories
        prob_dict = {
            self.label_decoder[i]: prob for i, prob in enumerate(probabilities)
        }

        # Generate explanation
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

    def _generate_explanation(
        self, category: str, confidence: float, probabilities: Dict[str, float]
    ) -> str:
        """Generate explanation for the classification result"""

        # Sort probabilities for alternatives
        sorted_probs = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
        alternatives = [f"{cat}: {prob*100:.1f}%" for cat, prob in sorted_probs[1:]]

        # Confidence level
        if confidence >= 0.8:
            conf_level = "high"
        elif confidence >= 0.6:
            conf_level = "moderate"
        else:
            conf_level = "low"

        explanation = f"The {self.model_type.replace('_', ' ')} model classified this text as '{category}' with {confidence*100:.1f}% confidence. This is a {conf_level}-confidence prediction."

        if alternatives:
            explanation += f" Alternative classifications: {', '.join(alternatives)}"

        return explanation

    def get_model_info(self) -> Dict:
        """Get information about the current model"""
        return {
            "model_type": self.model_type,
            "is_trained": self.is_trained,
            "total_documents": len(self.training_documents),
            "categories": self.categories,
            "training_stats": self.get_training_stats(),
        }

    def save_model(self, filepath: str):
        """Save the trained model to file"""
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
        """Load a trained model from file"""
        with open(filepath, "rb") as f:
            model_data = pickle.load(f)

        self.model = model_data["model"]
        self.vectorizer = model_data["vectorizer"]
        self.label_encoder = model_data["label_encoder"]
        self.label_decoder = model_data["label_decoder"]
        self.model_type = model_data["model_type"]
        self.categories = model_data["categories"]
        self.is_trained = True


# Test function
def test_classification_system():
    """Test the classification system"""
    print("Testing Document Classification System with CSV data...")

    # Test with both model types
    for model_type in ["naive_bayes", "logistic_regression"]:
        print(f"\n--- Testing {model_type.replace('_', ' ').title()} ---")

        # Initialize system
        classifier = DocumentClassificationSystem(model_type=model_type)

        # Print training stats
        stats = classifier.get_training_stats()
        print(f"Training data: {stats}")

        # Train model
        print("Training model...")
        results = classifier.train_model()
        print(f"Training completed. Accuracy: {results['accuracy']:.3f}")

        # Test classification
        test_texts = [
            "The government announced new economic policies to reduce unemployment.",
            "The company reported strong quarterly earnings with 15% growth.",
            "Medical researchers discovered a breakthrough treatment for cancer.",
        ]

        for text in test_texts:
            result = classifier.classify_text(text)
            print(f"\nText: {text[:50]}...")
            print(
                f"Predicted: {result['predicted_category']} ({result['confidence']:.3f})"
            )


# Global classifier instances for the API
_classifiers = {}


def _get_classifier(model_type="naive_bayes"):
    """Get or create a classifier instance for the given model type"""
    if model_type not in _classifiers:
        _classifiers[model_type] = DocumentClassificationSystem(model_type=model_type)
        # Auto-train the model when first created
        try:
            _classifiers[model_type].train_model()
        except Exception as e:
            print(f"Warning: Could not auto-train {model_type} model: {e}")
    return _classifiers[model_type]


def classify_document(text: str, model_type: str = "naive_bayes") -> Dict:
    """
    Standalone function to classify a document (for API compatibility)

    Args:
        text: The text to classify
        model_type: The model type ('naive_bayes' or 'logistic_regression')

    Returns:
        Classification result dictionary
    """
    classifier = _get_classifier(model_type)
    return classifier.classify_text(text)


def get_model_info(model_type: str = "naive_bayes") -> Dict:
    """
    Get information about the classification model (for API compatibility)

    Args:
        model_type: The model type ('naive_bayes' or 'logistic_regression')

    Returns:
        Model information dictionary
    """
    classifier = _get_classifier(model_type)
    return classifier.get_model_info()


def train_models() -> Dict:
    """
    Train both classification models (for API compatibility)

    Returns:
        Training results for both models
    """
    results = {}

    for model_type in ["naive_bayes", "logistic_regression"]:
        classifier = _get_classifier(model_type)
        training_result = classifier.train_model()
        results[model_type] = training_result

    return results


if __name__ == "__main__":
    test_classification_system()
