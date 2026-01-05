import 'dart:convert';
import 'package:http/http.dart' as http;
import 'models.dart';

class ApiService {
  ApiService({required this.baseUrl});

  final String baseUrl;

  Future<SearchResponse> searchPublications({
    String query = '',
    int page = 1,
    int size = 10,
  }) async {
    final uri = Uri.parse('$baseUrl/search').replace(queryParameters: {
      'query': query,
      'page': page.toString(),
      'size': size.toString(),
    });

    final response = await http.get(uri);
    if (response.statusCode != 200) {
      throw Exception('Search failed: ${response.statusCode}');
    }

    final jsonMap = json.decode(response.body) as Map<String, dynamic>;
    return SearchResponse.fromJson(jsonMap);
  }

  Future<ClassificationResult> classifyText({
    required String text,
    String modelType = 'naive_bayes',
  }) async {
    final uri = Uri.parse('$baseUrl/classify');
    final response = await http.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'text': text, 'model_type': modelType}),
    );

    if (response.statusCode != 200) {
      throw Exception('Classification failed: ${response.statusCode}');
    }

    final jsonMap = json.decode(response.body) as Map<String, dynamic>;
    return ClassificationResult.fromJson(jsonMap);
  }

  Future<ModelInfo> getModelInfo({String modelType = 'naive_bayes'}) async {
    final uri = Uri.parse('$baseUrl/model-info').replace(queryParameters: {
      'model_type': modelType,
    });

    final response = await http.get(uri);
    if (response.statusCode != 200) {
      throw Exception('Model info failed: ${response.statusCode}');
    }

    final jsonMap = json.decode(response.body) as Map<String, dynamic>;
    return ModelInfo.fromJson(jsonMap);
  }

  Future<void> trainModels() async {
    final uri = Uri.parse('$baseUrl/train-models');
    final response = await http.post(uri);
    if (response.statusCode != 200) {
      throw Exception('Train models failed: ${response.statusCode}');
    }
  }
}
