import 'dart:async';
import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:url_launcher/url_launcher.dart';
import 'api.dart';
import 'models.dart';

const String kApiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://localhost:8000',
);

void main() {
  runApp(const IRWebApp());
}

class IRWebApp extends StatelessWidget {
  const IRWebApp({super.key});

  @override
  Widget build(BuildContext context) {
    final baseTextTheme = ThemeData.light().textTheme.apply(
          fontFamily: 'Poppins',
        );
    return MaterialApp(
      title: 'IR Rijwol Shakya | Web',
      theme: ThemeData(
        colorScheme: const ColorScheme.light(
          primary: Color(0xFF0B3B49),
          secondary: Color(0xFFEA8A3A),
          surface: Color(0xFFF8F4EF),
          onSurface: Color(0xFF1F2937),
        ),
        scaffoldBackgroundColor: const Color(0xFFF4F1EC),
        fontFamily: 'Poppins',
        textTheme: baseTextTheme.copyWith(
          displayLarge: baseTextTheme.displayLarge?.copyWith(
            fontSize: 44,
            fontWeight: FontWeight.w700,
            color: const Color(0xFF0F172A),
          ),
          displayMedium: baseTextTheme.displayMedium?.copyWith(
            fontSize: 30,
            fontWeight: FontWeight.w700,
            color: const Color(0xFF0F172A),
          ),
          titleLarge: baseTextTheme.titleLarge?.copyWith(
            fontSize: 22,
            fontWeight: FontWeight.w600,
          ),
          titleMedium: baseTextTheme.titleMedium?.copyWith(
            fontSize: 18,
            fontWeight: FontWeight.w600,
          ),
        ),
        useMaterial3: true,
      ),
      home: const SplashScreen(),
    );
  }
}

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<double> _fade;
  late final Animation<double> _scale;
  late final Animation<double> _spin;
  late final Animation<double> _pulse;
  late final Animation<double> _glow;
  late final Animation<double> _textPop;
  late final Animation<double> _textShine;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2600),
    );
    _fade = CurvedAnimation(parent: _controller, curve: Curves.easeOut);
    _scale = Tween<double>(begin: 0.92, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOutBack),
    );
    _spin = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOutCubic),
    );
    _pulse = Tween<double>(begin: 0.95, end: 1.05).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
    _glow = Tween<double>(begin: 0.2, end: 0.9).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOutSine),
    );
    _textPop = Tween<double>(begin: 0.85, end: 1.0).animate(
      CurvedAnimation(
        parent: _controller,
        curve: const Interval(0.15, 0.6, curve: Curves.easeOutBack),
      ),
    );
    _textShine = Tween<double>(begin: -0.3, end: 1.3).animate(
      CurvedAnimation(
        parent: _controller,
        curve: const Interval(0.2, 0.9, curve: Curves.easeInOut),
      ),
    );

    _controller.forward();
    Future.delayed(const Duration(milliseconds: 3600), () {
      if (!mounted) return;
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => const HomePage()),
      );
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFFF1E8DA), Color(0xFFDDEBF2)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: Center(
          child: FadeTransition(
            opacity: _fade,
            child: ScaleTransition(
              scale: _scale,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  _SplashLogo(
                    spin: _spin,
                    pulse: _pulse,
                    glow: _glow,
                  ),
                  const SizedBox(height: 18),
                  _PopShineText(
                    text: 'IR Rijwol Shakya',
                    pop: _textPop,
                    shine: _textShine,
                    style: const TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.w700,
                      color: Color(0xFF0F172A),
                    ),
                  ),
                  const SizedBox(height: 6),
                  _PopShineText(
                    text: 'Search & Classify Research',
                    pop: _textPop,
                    shine: _textShine,
                    style: const TextStyle(color: Color(0xFF64748B)),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final ApiService _api = ApiService(baseUrl: kApiBaseUrl);
  final TextEditingController _queryController = TextEditingController();
  final TextEditingController _classifyController = TextEditingController();
  final TextEditingController _authorController = TextEditingController();
  final TextEditingController _yearFromController = TextEditingController();
  final TextEditingController _yearToController = TextEditingController();
  Timer? _searchDebounce;

  SearchResponse? _searchResponse;
  bool _searchLoading = false;
  String? _searchError;
  int _page = 1;
  final int _pageSize = 8;
  int? _lastSearchMs;
  String _sortBy = 'score';

  ClassificationResult? _classificationResult;
  bool _classifyLoading = false;
  String? _classifyError;

  ModelInfo? _modelInfo;
  bool _modelLoading = false;
  String? _modelError;

  final List<String> _modelTypes = const [
    'naive_bayes',
    'logistic_regression',
  ];
  String _selectedModel = 'naive_bayes';

  @override
  void initState() {
    super.initState();
    _fetchModelInfo();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _runSearch();
    });
  }

  @override
  void dispose() {
    _searchDebounce?.cancel();
    _queryController.dispose();
    _classifyController.dispose();
    _authorController.dispose();
    _yearFromController.dispose();
    _yearToController.dispose();
    super.dispose();
  }

  int? _parseYear(String raw) {
    final trimmed = raw.trim();
    if (trimmed.isEmpty) return null;
    final val = int.tryParse(trimmed);
    return val != null && val > 0 ? val : null;
  }

  void _onQueryChanged(String _) {}

  Future<void> _runSearch({int? page}) async {
    final nextPage = page ?? 1;
    setState(() {
      _searchLoading = true;
      _searchError = null;
    });

    final stopwatch = Stopwatch()..start();
    try {
      final response = await _api.searchPublications(
        query: _queryController.text.trim(),
        page: nextPage,
        size: _pageSize,
        author: _authorController.text.trim(),
        yearFrom: _parseYear(_yearFromController.text),
        yearTo: _parseYear(_yearToController.text),
        sort: _sortBy,
      );
      stopwatch.stop();
      setState(() {
        _searchResponse = response;
        _page = response.page;
        _lastSearchMs = stopwatch.elapsedMilliseconds;
      });
    } catch (error) {
      stopwatch.stop();
      setState(() {
        _searchError = error.toString();
        _lastSearchMs = stopwatch.elapsedMilliseconds;
      });
    } finally {
      setState(() {
        _searchLoading = false;
      });
    }
  }

  void _clearFilters() {
    setState(() {
      _authorController.clear();
      _yearFromController.clear();
      _yearToController.clear();
      _sortBy = 'score';
    });
    _runSearch(page: 1);
  }

  Future<void> _runClassification() async {
    if (_classifyController.text.trim().isEmpty) {
      setState(() {
        _classifyError = 'Enter text to classify.';
      });
      return;
    }
    setState(() {
      _classifyLoading = true;
      _classifyError = null;
    });

    try {
      final result = await _api.classifyText(
        text: _classifyController.text.trim(),
        modelType: _selectedModel,
      );
      setState(() {
        _classificationResult = result;
      });
    } catch (error) {
      setState(() {
        _classifyError = error.toString();
      });
    } finally {
      setState(() {
        _classifyLoading = false;
      });
    }
  }

  Future<void> _fetchModelInfo() async {
    setState(() {
      _modelLoading = true;
      _modelError = null;
    });
    try {
      final info = await _api.getModelInfo(modelType: _selectedModel);
      setState(() {
        _modelInfo = info;
      });
    } catch (error) {
      setState(() {
        _modelError = error.toString();
      });
    } finally {
      setState(() {
        _modelLoading = false;
      });
    }
  }

  Future<void> _trainModels() async {
    setState(() {
      _modelLoading = true;
      _modelError = null;
    });
    try {
      await _api.trainModels();
      await _fetchModelInfo();
    } catch (error) {
      setState(() {
        _modelError = error.toString();
      });
    } finally {
      setState(() {
        _modelLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        body: Stack(
          children: [
            const _WebBackground(),
            SafeArea(
              child: Column(
                children: [
                  LayoutBuilder(
                    builder: (context, constraints) {
                      final isWide = constraints.maxWidth >= 1100;
                      return Padding(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 20,
                          vertical: 10,
                        ),
                        child: _buildHeader(context, isWide),
                      );
                    },
                  ),
                  Expanded(
                    child: TabBarView(
                      children: [
                        _buildSearchScreen(context),
                        _buildClassificationScreen(context),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context, bool isWide) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.72),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFFE7E2D8)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 24,
            offset: const Offset(0, 16),
          ),
        ],
      ),
      child: isWide
          ? const Stack(
              alignment: Alignment.center,
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    Expanded(child: _HeaderBody(isWide: true)),
                    SizedBox(width: 16),
                    _HeaderTabBar(),
                  ],
                ),
                _HeaderLogoRow(),
              ],
            )
          : Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _HeaderBody(isWide: isWide),
                const SizedBox(height: 10),
                const _HeaderLogoRow(),
                const SizedBox(height: 10),
                const _HeaderTabBar(),
              ],
            ),
    );
  }

  Widget _buildSearchScreen(BuildContext context) {
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0, end: 1),
      duration: const Duration(milliseconds: 900),
      curve: Curves.easeOutCubic,
      builder: (context, value, child) => Opacity(
        opacity: value,
        child: Transform.translate(
          offset: Offset(0, 24 * (1 - value)),
          child: child,
        ),
      ),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final maxWidth = math.min(constraints.maxWidth, 1100.0);
          return SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 6),
            child: Align(
              alignment: Alignment.topCenter,
              child: ConstrainedBox(
                constraints: BoxConstraints(maxWidth: maxWidth),
                child: _buildSearchPanel(context),
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildClassificationScreen(BuildContext context) {
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0, end: 1),
      duration: const Duration(milliseconds: 900),
      curve: Curves.easeOutCubic,
      builder: (context, value, child) => Opacity(
        opacity: value,
        child: Transform.translate(
          offset: Offset(0, 24 * (1 - value)),
          child: child,
        ),
      ),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final maxWidth = math.min(constraints.maxWidth, 900.0);
          return SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 6),
            child: Align(
              alignment: Alignment.topCenter,
              child: ConstrainedBox(
                constraints: BoxConstraints(maxWidth: maxWidth),
                child: _buildInsightPanel(context),
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildSearchPanel(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final isNarrow = constraints.maxWidth < 640;
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _SectionCard(
              title: 'Search publications',
              subtitle: 'Query the IR index and explore ranked results.',
              child: Column(
                children: [
                  if (isNarrow)
                    Column(
                      children: [
                        TextField(
                          controller: _queryController,
                          decoration: InputDecoration(
                            hintText: 'Search by title, author, or keyword',
                            prefixIcon: const Icon(Icons.search_rounded),
                            filled: true,
                            fillColor: Colors.white,
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(16),
                              borderSide: BorderSide.none,
                            ),
                          ),
                          onSubmitted: (_) => _runSearch(),
                        ),
                        const SizedBox(height: 12),
                        SizedBox(
                          width: double.infinity,
                          child: FilledButton.icon(
                            onPressed:
                                _searchLoading ? null : () => _runSearch(),
                            icon: const Icon(Icons.search_rounded),
                            label: Text(
                                _searchLoading ? 'Searching...' : 'Search'),
                          ),
                        ),
                      ],
                    )
                  else
                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _queryController,
                            decoration: InputDecoration(
                              hintText: 'Search by title, author, or keyword',
                              prefixIcon: const Icon(Icons.search_rounded),
                              filled: true,
                              fillColor: Colors.white,
                              border: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(16),
                                borderSide: BorderSide.none,
                              ),
                            ),
                            onSubmitted: (_) => _runSearch(),
                          ),
                        ),
                        const SizedBox(width: 12),
                        FilledButton.icon(
                          onPressed: _searchLoading ? null : () => _runSearch(),
                          icon: const Icon(Icons.search_rounded),
                          label:
                              Text(_searchLoading ? 'Searching...' : 'Search'),
                        ),
                      ],
                    ),
                  const SizedBox(height: 12),
                  _buildFilters(context, isNarrow),
                  const SizedBox(height: 12),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        _lastSearchMs == null
                            ? 'Showing ${_searchResponse?.results.length ?? 0} of '
                                '${_searchResponse?.total ?? 0}'
                            : 'Showing ${_searchResponse?.results.length ?? 0} of '
                                '${_searchResponse?.total ?? 0} '
                                'in ${(_lastSearchMs! / 1000).toStringAsFixed(2)}s',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: const Color(0xFF6B7280),
                            ),
                      ),
                      Row(
                        children: [
                          IconButton(
                            onPressed: _searchLoading || _page <= 1
                                ? null
                                : () => _runSearch(page: _page - 1),
                            icon: const Icon(Icons.arrow_back_rounded),
                          ),
                          Text('Page $_page'),
                          IconButton(
                            onPressed: _searchLoading ||
                                    (_searchResponse?.totalPages ?? 1) <= _page
                                ? null
                                : () => _runSearch(page: _page + 1),
                            icon: const Icon(Icons.arrow_forward_rounded),
                          ),
                        ],
                      ),
                    ],
                  ),
                  if (_searchError != null)
                    _InlineAlert(message: _searchError!),
                ],
              ),
            ),
            const SizedBox(height: 16),
            _buildResults(context),
          ],
        );
      },
    );
  }

  Widget _buildResults(BuildContext context) {
    if (_searchLoading && _searchResponse == null) {
      return const _LoadingCard(label: 'Pulling ranked publications...');
    }
    if (_searchResponse == null || _searchResponse!.results.isEmpty) {
      return _SectionCard(
        title: 'No results yet',
        subtitle: 'Run a search to populate the research feed.',
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Use the search bar above to explore publications from the '
              'crawler dataset.',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: const Color(0xFF6B7280),
                  ),
            ),
            const SizedBox(height: 8),
            Text(
              'Tip: try broad queries (e.g., "machine learning") and then '
              'refine.',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: const Color(0xFF6B7280),
                  ),
            ),
          ],
        ),
      );
    }

    return Column(
      children: _searchResponse!.results
          .asMap()
          .entries
          .map((entry) => Padding(
                padding: const EdgeInsets.only(bottom: 14),
                child: _ResultCard(
                  publication: entry.value,
                  index: entry.key,
                  total: _searchResponse!.results.length,
                  query: _queryController.text.trim(),
                ),
              ))
          .toList(),
    );
  }

  Widget _buildFilters(BuildContext context, bool isNarrow) {
    final inputDecoration = InputDecoration(
      filled: true,
      fillColor: Colors.white,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: BorderSide.none,
      ),
      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
    );
    final authorField = TextField(
      controller: _authorController,
      decoration: inputDecoration.copyWith(
        labelText: 'Author',
        prefixIcon: const Icon(Icons.person_outline),
      ),
      onSubmitted: (_) => _runSearch(page: 1),
    );
    final yearFromField = TextField(
      controller: _yearFromController,
      keyboardType: TextInputType.number,
      decoration: inputDecoration.copyWith(
        labelText: 'Year from',
        prefixIcon: const Icon(Icons.calendar_today_outlined),
      ),
      onSubmitted: (_) => _runSearch(page: 1),
    );
    final yearToField = TextField(
      controller: _yearToController,
      keyboardType: TextInputType.number,
      decoration: inputDecoration.copyWith(
        labelText: 'Year to',
        prefixIcon: const Icon(Icons.event_available_outlined),
      ),
      onSubmitted: (_) => _runSearch(page: 1),
    );
    final sortField = DropdownButtonFormField<String>(
      initialValue: _sortBy,
      decoration: inputDecoration.copyWith(
        labelText: 'Sort by',
        prefixIcon: const Icon(Icons.sort),
      ),
      items: const [
        DropdownMenuItem(value: 'score', child: Text('Relevance')),
        DropdownMenuItem(value: 'date', child: Text('Newest')),
        DropdownMenuItem(value: 'title', child: Text('Title A-Z')),
      ],
      onChanged: (value) {
        if (value == null) return;
        setState(() => _sortBy = value);
        _runSearch(page: 1);
      },
    );
    if (isNarrow) {
      return Column(
        children: [
          authorField,
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(child: yearFromField),
              const SizedBox(width: 10),
              Expanded(child: yearToField),
            ],
          ),
          const SizedBox(height: 10),
          sortField,
          const SizedBox(height: 10),
          Align(
            alignment: Alignment.centerRight,
            child: TextButton(
              onPressed: _clearFilters,
              child: const Text('Clear filters'),
            ),
          ),
        ],
      );
    }
    return Column(
      children: [
        Row(
          children: [
            Expanded(child: authorField),
            const SizedBox(width: 12),
            Expanded(child: yearFromField),
            const SizedBox(width: 12),
            Expanded(child: yearToField),
          ],
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(child: sortField),
            const SizedBox(width: 12),
            TextButton(
              onPressed: _clearFilters,
              child: const Text('Clear filters'),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildInsightPanel(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final isWide = constraints.maxWidth >= 860;
        final classifyCard = _SectionCard(
          title: 'Classify text',
          subtitle: 'Predict categories with the IR classifier.',
          child: LayoutBuilder(
            builder: (context, constraints) {
              final isNarrow = constraints.maxWidth < 520;
              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  TextField(
                    controller: _classifyController,
                    maxLines: 6,
                    decoration: InputDecoration(
                      hintText: 'Paste an abstract or research summary...',
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(16),
                        borderSide: BorderSide.none,
                      ),
                      filled: true,
                      fillColor: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 12),
                  if (isNarrow)
                    Column(
                      children: [
                        DropdownButtonFormField<String>(
                          initialValue: _selectedModel,
                          decoration: InputDecoration(
                            labelText: 'Model',
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(14),
                            ),
                          ),
                          items: _modelTypes
                              .map(
                                (model) => DropdownMenuItem(
                                  value: model,
                                  child: Text(_prettyModelName(model)),
                                ),
                              )
                              .toList(),
                          onChanged: (value) {
                            if (value == null) return;
                            setState(() {
                              _selectedModel = value;
                            });
                            _fetchModelInfo();
                          },
                        ),
                        const SizedBox(height: 12),
                        SizedBox(
                          width: double.infinity,
                          child: FilledButton.icon(
                            onPressed:
                                _classifyLoading ? null : _runClassification,
                            icon: const Icon(Icons.auto_awesome_rounded),
                            label: Text(
                                _classifyLoading ? 'Analyzing...' : 'Classify'),
                          ),
                        ),
                      ],
                    )
                  else
                    Row(
                      children: [
                        Expanded(
                          child: DropdownButtonFormField<String>(
                            initialValue: _selectedModel,
                            decoration: InputDecoration(
                              labelText: 'Model',
                              border: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(14),
                              ),
                            ),
                            items: _modelTypes
                                .map(
                                  (model) => DropdownMenuItem(
                                    value: model,
                                    child: Text(_prettyModelName(model)),
                                  ),
                                )
                                .toList(),
                            onChanged: (value) {
                              if (value == null) return;
                              setState(() {
                                _selectedModel = value;
                              });
                              _fetchModelInfo();
                            },
                          ),
                        ),
                        const SizedBox(width: 12),
                        FilledButton.icon(
                          onPressed:
                              _classifyLoading ? null : _runClassification,
                          icon: const Icon(Icons.auto_awesome_rounded),
                          label: Text(
                            _classifyLoading ? 'Analyzing...' : 'Classify',
                          ),
                        ),
                      ],
                    ),
                  if (_classifyError != null)
                    _InlineAlert(message: _classifyError!),
                  if (_classificationResult != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 16),
                      child:
                          _ClassificationCard(result: _classificationResult!),
                    ),
                ],
              );
            },
          ),
        );
        final modelCard = _SectionCard(
          title: 'Model status',
          subtitle: 'Check training readiness and categories.',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      'Active model: ${_prettyModelName(_selectedModel)}',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                  ),
                  OutlinedButton.icon(
                    onPressed: _modelLoading ? null : _trainModels,
                    icon: const Icon(Icons.sync_rounded),
                    label: Text(_modelLoading ? 'Training...' : 'Train models'),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              if (_modelLoading && _modelInfo == null)
                const LinearProgressIndicator(),
              if (_modelError != null) _InlineAlert(message: _modelError!),
              if (_modelInfo != null) _ModelInfoCard(info: _modelInfo!),
            ],
          ),
        );

        if (isWide) {
          return Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(child: classifyCard),
              const SizedBox(width: 16),
              Expanded(child: modelCard),
            ],
          );
        }

        return Column(
          children: [
            classifyCard,
            const SizedBox(height: 16),
            modelCard,
          ],
        );
      },
    );
  }
}

String _prettyModelName(String model) {
  switch (model) {
    case 'naive_bayes':
      return 'Naive Bayes';
    case 'logistic_regression':
      return 'Logistic Regression';
    default:
      return model.replaceAll('_', ' ');
  }
}

class _HeaderBody extends StatelessWidget {
  const _HeaderBody({required this.isWide});

  final bool isWide;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final titleStyle = theme.textTheme.displayLarge?.copyWith(
      fontSize: isWide ? 36 : 26,
    );
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Container(
              padding: EdgeInsets.all(isWide ? 8 : 6),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: const Color(0xFFE7E2D8)),
              ),
              child: SvgPicture.asset(
                'assets/logo/transparent-logo.svg',
                height: isWide ? 34 : 26,
                width: isWide ? 34 : 26,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                'IR Rijwol Shakya',
                style: titleStyle,
              ),
            ),
          ],
        ),
      ],
    );
  }
}

class _HeaderTabBar extends StatelessWidget {
  const _HeaderTabBar();

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final maxWidth = math.min(constraints.maxWidth, 360.0);
        return Align(
          alignment: Alignment.centerRight,
          child: ConstrainedBox(
            constraints: BoxConstraints(maxWidth: maxWidth),
            child: Container(
              padding: const EdgeInsets.all(2),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.85),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: const Color(0xFFE7E2D8)),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.04),
                    blurRadius: 14,
                    offset: const Offset(0, 8),
                  ),
                ],
              ),
              child: const TabBar(
                indicator: BoxDecoration(
                  color: Color(0xFF0B3B49),
                  borderRadius: BorderRadius.all(Radius.circular(12)),
                ),
                indicatorSize: TabBarIndicatorSize.tab,
                indicatorPadding: EdgeInsets.zero,
                labelColor: Colors.white,
                unselectedLabelColor: Color(0xFF4B5563),
                labelStyle: TextStyle(fontWeight: FontWeight.w600),
                tabs: [
                  Tab(text: 'Search'),
                  Tab(text: 'Classify'),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}

class _HeaderLogoRow extends StatelessWidget {
  const _HeaderLogoRow();

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.center,
      child: Image.asset(
        'assets/softwarica.png',
        height: 50,
        fit: BoxFit.contain,
      ),
    );
  }
}

class _SplashLogo extends StatelessWidget {
  const _SplashLogo({
    required this.spin,
    required this.pulse,
    required this.glow,
  });

  final Animation<double> spin;
  final Animation<double> pulse;
  final Animation<double> glow;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 160,
      width: 160,
      child: AnimatedBuilder(
        animation: Listenable.merge([spin, pulse, glow]),
        builder: (context, child) {
          return Transform.scale(
            scale: 0.98 + (pulse.value * 0.04),
            child: Stack(
              alignment: Alignment.center,
              children: [
                Transform.rotate(
                  angle: spin.value * math.pi * 2,
                  child: Container(
                    height: 140,
                    width: 140,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: RadialGradient(
                        colors: [
                          const Color(0xFF0B3B49).withOpacity(0.08),
                          Colors.transparent,
                        ],
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: const Color(0xFF0B3B49)
                              .withOpacity(0.15 + glow.value * 0.25),
                          blurRadius: 28,
                          spreadRadius: 2,
                          offset: const Offset(0, 12),
                        ),
                      ],
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.all(18),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    shape: BoxShape.circle,
                    border: Border.all(color: const Color(0xFFE7E2D8)),
                  ),
                  child: SvgPicture.asset(
                    'assets/logo/transparent-logo.svg',
                    width: 84,
                    height: 84,
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _PopShineText extends StatelessWidget {
  const _PopShineText({
    required this.text,
    required this.pop,
    required this.shine,
    required this.style,
  });

  final String text;
  final Animation<double> pop;
  final Animation<double> shine;
  final TextStyle style;

  @override
  Widget build(BuildContext context) {
    final baseColor = style.color ?? const Color(0xFF111827);
    return AnimatedBuilder(
      animation: Listenable.merge([pop, shine]),
      builder: (context, child) {
        final t = shine.value;
        final start = (t - 0.3).clamp(0.0, 1.0);
        final mid = t.clamp(0.0, 1.0);
        final end = (t + 0.3).clamp(0.0, 1.0);

        return Transform.scale(
          scale: pop.value,
          child: ShaderMask(
            shaderCallback: (rect) {
              return LinearGradient(
                begin: Alignment.centerLeft,
                end: Alignment.centerRight,
                colors: [
                  baseColor.withOpacity(0.45),
                  baseColor.withOpacity(0.95),
                  baseColor.withOpacity(0.45),
                ],
                stops: [start, mid, end],
              ).createShader(rect);
            },
            blendMode: BlendMode.srcATop,
            child: child,
          ),
        );
      },
      child: Text(text, style: style),
    );
  }
}

class _WebBackground extends StatelessWidget {
  const _WebBackground();

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [Color(0xFFF7F0E6), Color(0xFFE7EEF2)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
      ),
      child: CustomPaint(
        painter: _BlobPainter(),
        child: const SizedBox.expand(),
      ),
    );
  }
}

class _BlobPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..style = PaintingStyle.fill;
    paint.color = const Color(0xFFEAD7B8).withOpacity(0.45);
    canvas.drawCircle(
      Offset(size.width * 0.82, size.height * 0.15),
      math.min(size.width, size.height) * 0.18,
      paint,
    );

    paint.color = const Color(0xFFB9D9E3).withOpacity(0.6);
    canvas.drawCircle(
      Offset(size.width * 0.15, size.height * 0.25),
      math.min(size.width, size.height) * 0.22,
      paint,
    );

    paint.color = const Color(0xFFD3C4F1).withOpacity(0.18);
    canvas.drawCircle(
      Offset(size.width * 0.55, size.height * 0.85),
      math.min(size.width, size.height) * 0.28,
      paint,
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _InfoPill extends StatelessWidget {
  const _InfoPill({
    required this.label,
    required this.value,
    required this.icon,
  });

  final String label;
  final String value;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      decoration: BoxDecoration(
        color: const Color(0xFFF9FAFB),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFFE5E7EB)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: const Color(0xFF6B7280)),
          const SizedBox(width: 6),
          Text(
            '$label: ',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: const Color(0xFF6B7280),
                  fontWeight: FontWeight.w600,
                ),
          ),
          Flexible(
            child: Text(
              value,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: const Color(0xFF374151),
                  ),
            ),
          ),
        ],
      ),
    );
  }
}

class _SectionCard extends StatelessWidget {
  const _SectionCard({
    required this.title,
    required this.subtitle,
    required this.child,
  });

  final String title;
  final String subtitle;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.9),
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: const Color(0xFFE7E2D8)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 18,
            offset: const Offset(0, 14),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 4),
          Text(
            subtitle,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: const Color(0xFF6B7280),
                ),
          ),
          const SizedBox(height: 16),
          child,
        ],
      ),
    );
  }
}

class _ResultCard extends StatefulWidget {
  const _ResultCard({
    required this.publication,
    required this.index,
    required this.total,
    required this.query,
  });

  final Publication publication;
  final int index;
  final int total;
  final String query;

  @override
  State<_ResultCard> createState() => _ResultCardState();
}

class _ResultCardState extends State<_ResultCard> {
  bool _hovered = false;

  List<String> _queryTokens(String query) {
    return query
        .toLowerCase()
        .split(RegExp(r'\s+'))
        .where((t) => t.length > 1)
        .toSet()
        .toList();
  }

  Widget _highlightedText(
    BuildContext context,
    String text,
    String query,
    TextStyle? baseStyle,
    int maxLines,
  ) {
    final tokens = _queryTokens(query);
    if (tokens.isEmpty || text.isEmpty) {
      return Text(
        text,
        maxLines: maxLines,
        overflow: TextOverflow.ellipsis,
        style: baseStyle,
      );
    }
    final pattern = RegExp(
      '(${tokens.map(RegExp.escape).join("|")})',
      caseSensitive: false,
    );
    final spans = <TextSpan>[];
    int start = 0;
    for (final match in pattern.allMatches(text)) {
      if (match.start > start) {
        spans.add(TextSpan(text: text.substring(start, match.start)));
      }
      spans.add(
        TextSpan(
          text: text.substring(match.start, match.end),
          style: baseStyle?.copyWith(
            fontWeight: FontWeight.w700,
            color: const Color(0xFF0B3B49),
          ),
        ),
      );
      start = match.end;
    }
    if (start < text.length) {
      spans.add(TextSpan(text: text.substring(start)));
    }
    return RichText(
      text: TextSpan(style: baseStyle, children: spans),
      maxLines: maxLines,
      overflow: TextOverflow.ellipsis,
    );
  }

  @override
  Widget build(BuildContext context) {
    final publication = widget.publication;
    final profileAuthors =
        publication.authors.where((a) => (a.profile ?? '').isNotEmpty).toList();
    final titleStyle = Theme.of(context).textTheme.titleMedium?.copyWith(
          color: const Color(0xFF0F172A),
          height: 1.3,
        );
    final bodyStyle = Theme.of(context).textTheme.bodyMedium?.copyWith(
          color: const Color(0xFF4B5563),
        );
    return MouseRegion(
      onEnter: (_) => setState(() => _hovered = true),
      onExit: (_) => setState(() => _hovered = false),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: _hovered ? const Color(0xFFFFF9F0) : Colors.white,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: const Color(0xFFE7E2D8)),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(_hovered ? 0.08 : 0.04),
              blurRadius: _hovered ? 18 : 12,
              offset: const Offset(0, 12),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: _highlightedText(
                    context,
                    publication.title,
                    widget.query,
                    titleStyle,
                    2,
                  ),
                ),
                const SizedBox(width: 12),
                _ScoreBadge(score: publication.score),
              ],
            ),
            const SizedBox(height: 6),
            Wrap(
              spacing: 6,
              runSpacing: 4,
              children: [
                _MetaChip(
                  icon: Icons.calendar_today_outlined,
                  label: publication.publishedDate.isEmpty
                      ? 'Unknown date'
                      : publication.publishedDate,
                ),
                _MetaChip(
                  icon: Icons.people_alt_outlined,
                  label: publication.authors.isEmpty
                      ? 'Unknown authors'
                      : publication.authors.map((a) => a.name).join(', '),
                ),
                const _MetaChip(
                  icon: Icons.public,
                  label: 'PurePortal ICS',
                ),
              ],
            ),
            if (profileAuthors.isNotEmpty) ...[
              const SizedBox(height: 10),
              Wrap(
                spacing: 8,
                runSpacing: 6,
                children: profileAuthors.map((author) {
                  return TextButton.icon(
                    onPressed: () => _launchLink(author.profile!),
                    icon: const Icon(Icons.person_outline, size: 16),
                    label: Text(author.name),
                    style: TextButton.styleFrom(
                      foregroundColor: const Color(0xFF0B3B49),
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 8,
                      ),
                      backgroundColor: const Color(0xFFE9EEF0),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                      ),
                    ),
                  );
                }).toList(),
              ),
            ],
            const SizedBox(height: 10),
            _highlightedText(
              context,
              publication.abstractText.isEmpty
                  ? 'No abstract provided.'
                  : publication.abstractText,
              widget.query,
              bodyStyle,
              4,
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Text(
                  'Result ${widget.index + 1} of ${widget.total}',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: const Color(0xFF6B7280),
                      ),
                ),
                const Spacer(),
                if (profileAuthors.isEmpty)
                  Text(
                    'No author profiles',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: const Color(0xFF6B7280),
                        ),
                  ),
                if (profileAuthors.isEmpty) const SizedBox(width: 8),
                TextButton.icon(
                  onPressed: publication.link.isEmpty
                      ? null
                      : () => _launchLink(publication.link),
                  icon: const Icon(Icons.open_in_new_rounded),
                  label: const Text('Open source'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _launchLink(String url) async {
    final uri = Uri.tryParse(url);
    if (uri == null) return;
    await launchUrl(uri, mode: LaunchMode.externalApplication);
  }
}

class _ScoreBadge extends StatelessWidget {
  const _ScoreBadge({required this.score});

  final double score;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: const Color(0xFF0B3B49),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        score.toStringAsFixed(2),
        style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Colors.white,
              fontWeight: FontWeight.w600,
            ),
      ),
    );
  }
}

class _MetaChip extends StatelessWidget {
  const _MetaChip({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: const Color(0xFFF8F1E7),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: const Color(0xFF6B7280)),
          const SizedBox(width: 4),
          Flexible(
            child: Text(
              label,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: const Color(0xFF374151),
                  ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ClassificationCard extends StatelessWidget {
  const _ClassificationCard({required this.result});

  final ClassificationResult result;

  @override
  Widget build(BuildContext context) {
    final sorted = result.probabilities.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFFF3F8FB),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFDAE7EF)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.auto_awesome_rounded,
                  color: Theme.of(context).colorScheme.primary),
              const SizedBox(width: 8),
              Text(
                result.predictedCategory,
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const Spacer(),
              Text(
                '${(result.confidence * 100).toStringAsFixed(1)}% confident',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: const Color(0xFF4B5563),
                    ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            result.explanation,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: const Color(0xFF4B5563),
                ),
          ),
          const SizedBox(height: 12),
          ...sorted.map(
            (entry) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(child: Text(entry.key)),
                      Text('${(entry.value * 100).toStringAsFixed(1)}%'),
                    ],
                  ),
                  const SizedBox(height: 4),
                  LinearProgressIndicator(
                    value: entry.value,
                    minHeight: 6,
                    borderRadius: BorderRadius.circular(6),
                    backgroundColor: const Color(0xFFDDE7ED),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ModelInfoCard extends StatelessWidget {
  const _ModelInfoCard({required this.info});

  final ModelInfo info;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFFFFBF5),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFF3E5D0)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Wrap(
            spacing: 10,
            runSpacing: 6,
            children: [
              _StatusPill(
                label: info.isTrained ? 'Trained' : 'Not trained',
                color: info.isTrained
                    ? const Color(0xFF2E7D32)
                    : const Color(0xFF9A3412),
              ),
              _StatusPill(
                label: '${info.totalDocuments} docs',
                color: const Color(0xFF0B3B49),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            'Categories',
            style: Theme.of(context).textTheme.titleSmall,
          ),
          const SizedBox(height: 6),
          Wrap(
            spacing: 8,
            runSpacing: 6,
            children: info.categories
                .map(
                  (category) => _StatusPill(
                    label: category,
                    color: const Color(0xFF475569),
                  ),
                )
                .toList(),
          ),
        ],
      ),
    );
  }
}

class _StatusPill extends StatelessWidget {
  const _StatusPill({required this.label, required this.color});

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Text(
        label,
        style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: color,
              fontWeight: FontWeight.w600,
            ),
      ),
    );
  }
}

class _InlineAlert extends StatelessWidget {
  const _InlineAlert({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(top: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFFFFF1F2),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFFECACA)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.error_outline, color: Color(0xFFDC2626)),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              message,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: const Color(0xFFB91C1C),
                  ),
            ),
          ),
        ],
      ),
    );
  }
}

class _LoadingCard extends StatelessWidget {
  const _LoadingCard({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFFE7E2D8)),
      ),
      child: Row(
        children: [
          const CircularProgressIndicator(),
          const SizedBox(width: 16),
          Text(label),
        ],
      ),
    );
  }
}
