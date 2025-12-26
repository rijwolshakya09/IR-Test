// API service for making requests to the backend
export const API_BASE_URL = "http://localhost:8000";

export interface Author {
  name: string;
  profile: string | null;
}

export interface Publication {
  title: string;
  link: string;
  authors: Author[];
  published_date: string;
  abstract: string;
  score: number;
}

export interface SearchResponse {
  results: Publication[];
  total: number;
  page: number;
  size: number;
  total_pages: number;
}

export interface ClassificationResult {
  predicted_category: string;
  confidence: number;
  probabilities: {
    politics: number;
    business: number;
    health: number;
  };
  explanation: string;
  model_used: string;
  text_length?: number;
  processed_text_length?: number;
}

export interface ModelInfo {
  model_type: string;
  is_trained: boolean;
  total_documents: number;
  categories: string[];
}

export class ApiService {
  static async searchPublications(query: string = "", page: number = 1, size: number = 10): Promise<SearchResponse> {
    const params = new URLSearchParams({
      query,
      page: page.toString(),
      size: size.toString(),
    });

    const response = await fetch(`${API_BASE_URL}/search?${params}`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  static async checkHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/`);
      return response.ok;
    } catch {
      return false;
    }
  }

  static async classifyText(text: string, modelType: string = "naive_bayes"): Promise<ClassificationResult> {
    const response = await fetch(`${API_BASE_URL}/classify`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        text,
        model_type: modelType,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  static async getModelInfo(modelType: string = "naive_bayes"): Promise<ModelInfo> {
    const response = await fetch(`${API_BASE_URL}/model-info?model_type=${modelType}`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  static async trainModels(): Promise<{ message: string; results: Record<string, unknown> }> {
    const response = await fetch(`${API_BASE_URL}/train-models`, {
      method: "POST",
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }
}
