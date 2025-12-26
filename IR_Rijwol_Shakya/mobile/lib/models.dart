class Author {
  final String name;
  final String? profile;

  Author({required this.name, this.profile});

  factory Author.fromJson(Map<String, dynamic> json) {
    return Author(
      name: json['name'] ?? '',
      profile: json['profile'],
    );
  }
}

class Publication {
  final String title;
  final String link;
  final List<Author> authors;
  final String publishedDate;
  final String abstractText;
  final double score;

  Publication({
    required this.title,
    required this.link,
    required this.authors,
    required this.publishedDate,
    required this.abstractText,
    required this.score,
  });

  factory Publication.fromJson(Map<String, dynamic> json) {
    final authorsJson = (json['authors'] as List<dynamic>? ?? [])
        .map((a) => Author.fromJson(a as Map<String, dynamic>))
        .toList();

    return Publication(
      title: json['title'] ?? '',
      link: json['link'] ?? '',
      authors: authorsJson,
      publishedDate: json['published_date'] ?? '',
      abstractText: json['abstract'] ?? '',
      score: (json['score'] ?? 0).toDouble(),
    );
  }
}

class SearchResponse {
  final List<Publication> results;
  final int total;
  final int page;
  final int size;
  final int totalPages;

  SearchResponse({
    required this.results,
    required this.total,
    required this.page,
    required this.size,
    required this.totalPages,
  });

  factory SearchResponse.fromJson(Map<String, dynamic> json) {
    final items = (json['results'] as List<dynamic>? ?? [])
        .map((e) => Publication.fromJson(e as Map<String, dynamic>))
        .toList();

    return SearchResponse(
      results: items,
      total: json['total'] ?? 0,
      page: json['page'] ?? 1,
      size: json['size'] ?? 10,
      totalPages: json['total_pages'] ?? 1,
    );
  }
}

class ClassificationResult {
  final String predictedCategory;
  final double confidence;
  final Map<String, double> probabilities;
  final String explanation;
  final String modelUsed;

  ClassificationResult({
    required this.predictedCategory,
    required this.confidence,
    required this.probabilities,
    required this.explanation,
    required this.modelUsed,
  });

  factory ClassificationResult.fromJson(Map<String, dynamic> json) {
    final probs = <String, double>{};
    final raw = json['probabilities'] as Map<String, dynamic>? ?? {};
    raw.forEach((k, v) => probs[k] = (v ?? 0).toDouble());

    return ClassificationResult(
      predictedCategory: json['predicted_category'] ?? '',
      confidence: (json['confidence'] ?? 0).toDouble(),
      probabilities: probs,
      explanation: json['explanation'] ?? '',
      modelUsed: json['model_used'] ?? '',
    );
  }
}

class ModelInfo {
  final String modelType;
  final bool isTrained;
  final int totalDocuments;
  final List<String> categories;

  ModelInfo({
    required this.modelType,
    required this.isTrained,
    required this.totalDocuments,
    required this.categories,
  });

  factory ModelInfo.fromJson(Map<String, dynamic> json) {
    final cats = (json['categories'] as List<dynamic>? ?? [])
        .map((e) => e.toString())
        .toList();
    return ModelInfo(
      modelType: json['model_type'] ?? '',
      isTrained: json['is_trained'] ?? false,
      totalDocuments: json['total_documents'] ?? 0,
      categories: cats,
    );
  }
}
