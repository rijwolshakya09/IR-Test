"use client";

import { useState, useEffect, useCallback } from "react";
import { ApiService, ClassificationResult, ModelInfo } from "../services/api";
import LoadingSpinner from "./LoadingSpinner";
import { useToast } from "../contexts/ToastContext";

export default function DocumentClassification() {
  const [text, setText] = useState("");
  const [modelType, setModelType] = useState<"naive_bayes" | "logistic_regression">("naive_bayes");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ClassificationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);
  const [trainingLoading, setTrainingLoading] = useState(false);
  const { addToast } = useToast();

  const loadModelInfo = useCallback(async () => {
    try {
      const info = await ApiService.getModelInfo(modelType);
      setModelInfo(info);
    } catch (err) {
      console.error("Failed to load model info:", err);
    }
  }, [modelType]);

  // Load model info on component mount and when model type changes
  useEffect(() => {
    loadModelInfo();
  }, [loadModelInfo]);

  const handleClassify = async () => {
    if (!text.trim()) {
      setError("Please enter some text to classify");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const classificationResult = await ApiService.classifyText(text, modelType);
      setResult(classificationResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Classification failed");
    } finally {
      setLoading(false);
    }
  };

  const handleTrainModels = async () => {
    setTrainingLoading(true);
    try {
      await ApiService.trainModels();
      await loadModelInfo(); // Reload model info after training
      addToast("Models trained successfully!", "success");
    } catch (err) {
      addToast(`Training failed: ${err instanceof Error ? err.message : "Unknown error"}`, "error");
    } finally {
      setTrainingLoading(false);
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category.toLowerCase()) {
      case "politics":
        return "text-red-400 bg-red-900/20 border-red-800";
      case "business":
        return "text-green-400 bg-green-900/20 border-green-800";
      case "health":
        return "text-blue-400 bg-blue-900/20 border-blue-800";
      default:
        return "text-gray-400 bg-gray-900/20 border-gray-800";
    }
  };

  const formatConfidence = (confidence: number) => {
    return `${(confidence * 100).toFixed(1)}%`;
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Header Section */}
      <div className="text-center">
        <h1 className="text-4xl font-bold text-white mb-4">Document Classification</h1>
        <p className="text-gray-300 text-lg">
          Classify text documents into Politics, Business, or Health categories using machine learning
        </p>
      </div>

      {/* Model Info Card */}
      {modelInfo && (
        <div className="bg-slate-800/60 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-white">Model Information</h2>
            <button
              onClick={handleTrainModels}
              disabled={trainingLoading}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-800 disabled:opacity-50 text-white rounded-lg font-medium transition-colors duration-200 flex items-center gap-2 cursor-pointer disabled:cursor-not-allowed"
            >
              {trainingLoading ? (
                <>
                  <LoadingSpinner size="sm" />
                  Training...
                </>
              ) : (
                "Retrain Models"
              )}
            </button>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-400">Model Type:</span>
              <p className="text-white font-medium capitalize">{modelInfo.model_type.replace("_", " ")}</p>
            </div>
            <div>
              <span className="text-gray-400">Status:</span>
              <p className={`font-medium ${modelInfo.is_trained ? "text-green-400" : "text-red-400"}`}>
                {modelInfo.is_trained ? "Trained" : "Not Trained"}
              </p>
            </div>
            <div>
              <span className="text-gray-400">Documents:</span>
              <p className="text-white font-medium">{modelInfo.total_documents}</p>
            </div>
            <div>
              <span className="text-gray-400">Categories:</span>
              <p className="text-white font-medium">{modelInfo.categories.join(", ")}</p>
            </div>
          </div>
        </div>
      )}

      {/* Classification Form */}
      <div className="bg-slate-800/60 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
        <div className="space-y-4">
          {/* Model Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Select Model</label>
            <select
              value={modelType}
              onChange={(e) => setModelType(e.target.value as "naive_bayes" | "logistic_regression")}
              className="w-full p-3 bg-slate-700 border border-slate-600 rounded-lg text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent cursor-pointer"
            >
              <option value="naive_bayes">Naive Bayes</option>
              <option value="logistic_regression">Logistic Regression</option>
            </select>
          </div>

          {/* Text Input */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Text to Classify</label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Enter the text you want to classify..."
              rows={6}
              className="w-full p-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-vertical"
            />
            <p className="text-sm text-gray-400 mt-1">Characters: {text.length}</p>
          </div>

          {/* Action Button */}
          <button
            onClick={handleClassify}
            disabled={loading || !text.trim()}
            className="w-full py-3 px-6 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-800 disabled:opacity-50 text-white font-medium rounded-lg transition-colors duration-200 flex items-center justify-center gap-2 cursor-pointer disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <LoadingSpinner size="sm" />
                Classifying...
              </>
            ) : (
              "Classify Text"
            )}
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-900/20 border border-red-800 rounded-xl p-4">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {/* Results Display */}
      {result && (
        <div className="bg-slate-800/60 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
          <h2 className="text-xl font-semibold text-white mb-4">Classification Results</h2>

          {/* Main Result */}
          <div className="mb-6">
            <div className="flex items-center gap-3 mb-2">
              <span className="text-gray-400">Predicted Category:</span>
              <span
                className={`px-3 py-1 rounded-full text-sm font-medium border ${getCategoryColor(
                  result.predicted_category
                )}`}
              >
                {result.predicted_category.toUpperCase()}
              </span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-gray-400">Confidence:</span>
              <span className="text-white font-medium text-lg">{formatConfidence(result.confidence)}</span>
            </div>
          </div>

          {/* Probability Breakdown */}
          <div className="mb-6">
            <h3 className="text-lg font-medium text-white mb-3">Probability Breakdown</h3>
            <div className="space-y-3">
              {Object.entries(result.probabilities).map(([category, probability]) => (
                <div key={category} className="flex items-center gap-3">
                  <span className={`w-20 text-sm font-medium capitalize ${getCategoryColor(category).split(" ")[0]}`}>
                    {category}:
                  </span>
                  <div className="flex-1 bg-slate-700 rounded-full h-3 overflow-hidden">
                    <div
                      className={`h-full transition-all duration-300 ${
                        category === "politics"
                          ? "bg-red-500"
                          : category === "business"
                          ? "bg-green-500"
                          : "bg-blue-500"
                      }`}
                      style={{ width: `${probability * 100}%` }}
                    />
                  </div>
                  <span className="text-white font-medium w-12 text-right">{formatConfidence(probability)}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Additional Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-400">Model Used:</span>
              <p className="text-white font-medium capitalize">{result.model_used.replace("_", " ")}</p>
            </div>
            {result.text_length && (
              <div>
                <span className="text-gray-400">Text Length:</span>
                <p className="text-white font-medium">{result.text_length} characters</p>
              </div>
            )}
          </div>

          {/* Explanation */}
          {result.explanation && (
            <div className="mt-4 p-4 bg-slate-700/50 rounded-lg">
              <h4 className="text-sm font-medium text-gray-300 mb-2">Explanation:</h4>
              <p className="text-gray-200 text-sm leading-relaxed">{result.explanation}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
