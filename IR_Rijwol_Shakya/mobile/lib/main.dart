import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:url_launcher/url_launcher.dart';
import 'api.dart';
import 'models.dart';

const String kApiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://10.0.2.2:8000',
);
const Color kBrandColor = Color(0xFF88CFFF);

void main() {
  runApp(const IRApp());
}

class IRApp extends StatelessWidget {
  const IRApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'IR Rijwol Shakya',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: kBrandColor),
        scaffoldBackgroundColor: const Color(0xFFF6F7FB),
        fontFamily: 'Poppins',
        cardTheme: const CardThemeData(
          elevation: 1.5,
          color: Colors.white,
          shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.all(Radius.circular(14))),
        ),
        inputDecorationTheme: const InputDecorationTheme(
          filled: true,
          fillColor: Colors.white,
          border: OutlineInputBorder(),
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Colors.white,
          foregroundColor: Color(0xFF1F2937),
          elevation: 0.5,
        ),
        chipTheme: const ChipThemeData(
          side: BorderSide(color: Color(0xFFE5E7EB)),
          labelStyle: TextStyle(color: Color(0xFF374151)),
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
  late final Animation<double> _ringSpin;
  late final Animation<double> _dotsSpin;
  late final Animation<double> _textPop;
  late final Animation<double> _textShine;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 3000),
    );
    _fade = CurvedAnimation(parent: _controller, curve: Curves.easeOut);
    _scale = Tween<double>(begin: 0.9, end: 1.0).animate(
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
    _ringSpin = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: Curves.linear),
    );
    _dotsSpin = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: Curves.linear),
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

    Future.delayed(const Duration(milliseconds: 5000), () {
      if (!mounted) return;
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => const HomeScreen()),
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
            colors: [Color(0xFFEEF2FF), Color(0xFFE0F2FE)],
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
                    ringSpin: _ringSpin,
                    dotsSpin: _dotsSpin,
                  ),
                  SizedBox(height: 16),
                  _PopShineText(
                    text: 'IR Rijwol Shakya',
                    pop: _textPop,
                    shine: _textShine,
                    style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w700,
                      color: Color(0xFF1F2937),
                    ),
                  ),
                  SizedBox(height: 6),
                  _PopShineText(
                    text: 'Search & Classify Research',
                    pop: _textPop,
                    shine: _textShine,
                    style: const TextStyle(color: Color(0xFF6B7280)),
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

class _SplashLogo extends StatelessWidget {
  const _SplashLogo({
    required this.spin,
    required this.pulse,
    required this.glow,
    required this.ringSpin,
    required this.dotsSpin,
  });

  final Animation<double> spin;
  final Animation<double> pulse;
  final Animation<double> glow;
  final Animation<double> ringSpin;
  final Animation<double> dotsSpin;

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: Listenable.merge([spin, pulse, glow, ringSpin, dotsSpin]),
      builder: (context, child) {
        return Transform.scale(
          scale: pulse.value,
          child: Transform.rotate(
            angle: spin.value * 6.28318,
            child: child,
          ),
        );
      },
      child: Stack(
        alignment: Alignment.center,
        children: [
          SizedBox(
            width: 300,
            height: 300,
            child: CustomPaint(
              painter: _ShimmerRingPainter(ringSpin.value),
            ),
          ),
          SizedBox(
            width: 300,
            height: 300,
            child: CustomPaint(
              painter: _ParticleDotsPainter(dotsSpin.value),
            ),
          ),
          Container(
            width: 250,
            height: 250,
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFFEEF2FF), kBrandColor],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(120),
              boxShadow: [
                BoxShadow(
                  color: kBrandColor.withOpacity(glow.value * 0.35),
                  blurRadius: 28,
                  spreadRadius: 2,
                  offset: const Offset(0, 10),
                ),
                const BoxShadow(
                  color: Color(0x22000000),
                  blurRadius: 18,
                  offset: Offset(0, 8),
                ),
              ],
            ),
            child: _AnimatedLogo(shine: ringSpin, glow: glow),
          ),
        ],
      ),
    );
  }
}

class _AnimatedLogo extends StatelessWidget {
  const _AnimatedLogo({required this.shine, required this.glow});

  static final Future<String> _logoSvg =
      rootBundle.loadString('assets/logo/transparent-logo.svg').then(
            (data) => data.replaceAll(
              RegExp(r'<metadata[^>]*>.*?</metadata>', dotAll: true),
              '',
            ),
          );

  final Animation<double> shine;
  final Animation<double> glow;

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: Listenable.merge([shine, glow]),
      builder: (context, child) {
        final t = shine.value;
        final start = (t - 0.35).clamp(0.0, 1.0);
        final mid = t.clamp(0.0, 1.0);
        final end = (t + 0.35).clamp(0.0, 1.0);

        return Transform.scale(
          scale: 0.96 + (glow.value * 0.04),
          child: ShaderMask(
            shaderCallback: (rect) {
              return LinearGradient(
                begin: Alignment.centerLeft,
                end: Alignment.centerRight,
                colors: [
                  Colors.white.withOpacity(0.0),
                  Colors.white.withOpacity(0.6),
                  Colors.white.withOpacity(0.0),
                ],
                stops: [start, mid, end],
              ).createShader(rect);
            },
            blendMode: BlendMode.srcATop,
            child: child,
          ),
        );
      },
      child: Padding(
        padding: const EdgeInsets.all(0),
        child: FutureBuilder<String>(
          future: _logoSvg,
          builder: (context, snapshot) {
            if (snapshot.hasData) {
              return SvgPicture.string(
                snapshot.data ?? '',
                width: 900,
                height: 900,
                fit: BoxFit.contain,
              );
            }
            return const SizedBox(width: 900, height: 900);
          },
        ),
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
                  Colors.white,
                  baseColor.withOpacity(0.9),
                ],
                stops: [start, mid, end],
              ).createShader(rect);
            },
            blendMode: BlendMode.srcIn,
            child: Text(text, style: style.copyWith(color: Colors.white)),
          ),
        );
      },
    );
  }
}

class _ShimmerRingPainter extends CustomPainter {
  _ShimmerRingPainter(this.t);

  final double t;

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2 - 6;
    final sweep = SweepGradient(
      startAngle: 0,
      endAngle: 6.28318,
      colors: [
        kBrandColor.withOpacity(0.0),
        kBrandColor,
        kBrandColor.withOpacity(0.0),
      ],
      stops: const [0.2, 0.5, 0.8],
      transform: GradientRotation(t * 6.28318),
    );
    final paint = Paint()
      ..shader =
          sweep.createShader(Rect.fromCircle(center: center, radius: radius))
      ..style = PaintingStyle.stroke
      ..strokeWidth = 6;
    canvas.drawCircle(center, radius, paint);
  }

  @override
  bool shouldRepaint(covariant _ShimmerRingPainter oldDelegate) {
    return oldDelegate.t != t;
  }
}

class _ParticleDotsPainter extends CustomPainter {
  _ParticleDotsPainter(this.t);

  final double t;

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2 - 8;
    final angles = [0.0, 2.1, 4.2];
    for (int i = 0; i < angles.length; i++) {
      final a = angles[i] + t * 6.28318;
      final p = Offset(
        center.dx + radius * 0.75 * math.sin(a),
        center.dy + radius * 0.75 * math.cos(a),
      );
      final paint = Paint()
        ..color = i == 0 ? kBrandColor : const Color(0xFF06B6D4)
        ..style = PaintingStyle.fill;
      canvas.drawCircle(p, 4, paint);
    }
  }

  @override
  bool shouldRepaint(covariant _ParticleDotsPainter oldDelegate) {
    return oldDelegate.t != t;
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _tabIndex = 0;

  @override
  Widget build(BuildContext context) {
    final pages = [const SearchScreen(), const ClassificationScreen()];

    return Scaffold(
      appBar: AppBar(
        title: const Text('IR Rijwol Shakya'),
      ),
      body: SafeArea(child: pages[_tabIndex]),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _tabIndex,
        onDestinationSelected: (index) => setState(() => _tabIndex = index),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.search), label: 'Search'),
          NavigationDestination(icon: Icon(Icons.category), label: 'Classify'),
        ],
      ),
    );
  }
}

class SearchScreen extends StatefulWidget {
  const SearchScreen({super.key});

  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  final _queryController = TextEditingController();
  final _api = ApiService(baseUrl: kApiBaseUrl);

  bool _loading = false;
  String? _error;
  SearchResponse? _response;
  int _page = 1;
  int _pageSize = 10;
  String _sortBy = 'relevance';
  String _sortOrder = 'desc';
  double _minScore = 0.0;
  bool _onlyWithAbstract = false;
  int? _searchMs;

  Future<void> _search({int? page}) async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final start = DateTime.now();
      final res = await _api.searchPublications(
        query: _queryController.text.trim(),
        page: page ?? _page,
        size: _pageSize,
      );
      setState(() {
        _response = res;
        _page = res.page;
        _searchMs = DateTime.now().difference(start).inMilliseconds;
      });
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  List<Publication> _applyFilters(List<Publication> input) {
    var results = input;

    if (_onlyWithAbstract) {
      results = results.where((p) => p.abstractText.isNotEmpty).toList();
    }

    if (_minScore > 0) {
      results = results.where((p) => p.score >= _minScore).toList();
    }

    results.sort((a, b) {
      int dir = _sortOrder == 'asc' ? 1 : -1;
      switch (_sortBy) {
        case 'date':
          final aDate = DateTime.tryParse(a.publishedDate) ?? DateTime(1970);
          final bDate = DateTime.tryParse(b.publishedDate) ?? DateTime(1970);
          return aDate.compareTo(bDate) * dir;
        case 'title':
          return a.title.toLowerCase().compareTo(b.title.toLowerCase()) * dir;
        default:
          return a.score.compareTo(b.score) * dir;
      }
    });

    return results;
  }

  @override
  Widget build(BuildContext context) {
    final results = _applyFilters(_response?.results ?? []);

    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          _SearchHeader(
            queryController: _queryController,
            onSearch: () => _search(page: 1),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              ElevatedButton.icon(
                onPressed: () => _openFilters(context),
                icon: const Icon(Icons.tune),
                label: const Text('Filters'),
              ),
              const SizedBox(width: 12),
              if (_response != null) Text('Total: ${_response!.total}'),
              const Spacer(),
              IconButton(
                tooltip: 'Refresh',
                onPressed: _loading ? null : () => _search(page: _page),
                icon: const Icon(Icons.refresh),
              ),
            ],
          ),
          const SizedBox(height: 8),
          _SearchStatus(
            loading: _loading,
            error: _error,
            total: _response?.total ?? 0,
            page: _page,
            totalPages: _response?.totalPages ?? 1,
            pageResults: results.length,
            searchMs: _searchMs,
          ),
          const SizedBox(height: 8),
          Expanded(
            child: RefreshIndicator(
              onRefresh: () => _search(page: _page),
              child: _loading
                  ? ListView.separated(
                      itemCount: 6,
                      separatorBuilder: (_, __) => const SizedBox(height: 8),
                      itemBuilder: (context, index) {
                        return const _LoadingCard();
                      },
                    )
                  : results.isEmpty
                      ? const Center(child: Text('No results'))
                      : ListView.separated(
                          itemCount: results.length,
                          separatorBuilder: (_, __) =>
                              const SizedBox(height: 8),
                          itemBuilder: (context, index) {
                            final pub = results[index];
                            return PublicationCard(publication: pub);
                          },
                        ),
            ),
          ),
          _PaginationBar(
            page: _page,
            totalPages: _response?.totalPages ?? 1,
            loading: _loading,
            onPrev: () => _search(page: _page - 1),
            onNext: () => _search(page: _page + 1),
          ),
        ],
      ),
    );
  }

  @override
  void initState() {
    super.initState();
    _search(page: 1);
  }

  void _openFilters(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (ctx) {
        int tempPageSize = _pageSize;
        String tempSortBy = _sortBy;
        String tempSortOrder = _sortOrder;
        double tempMinScore = _minScore;
        bool tempOnlyWithAbstract = _onlyWithAbstract;

        return StatefulBuilder(
          builder: (context, setModalState) {
            return SafeArea(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Text(
                      'Filters & Sorting',
                      style:
                          TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 12),
                    _FiltersBar(
                      pageSize: tempPageSize,
                      sortBy: tempSortBy,
                      sortOrder: tempSortOrder,
                      minScore: tempMinScore,
                      onlyWithAbstract: tempOnlyWithAbstract,
                      onPageSizeChanged: (v) =>
                          setModalState(() => tempPageSize = v),
                      onSortByChanged: (v) =>
                          setModalState(() => tempSortBy = v),
                      onSortOrderChanged: (v) =>
                          setModalState(() => tempSortOrder = v),
                      onMinScoreChanged: (v) =>
                          setModalState(() => tempMinScore = v),
                      onOnlyWithAbstractChanged: (v) =>
                          setModalState(() => tempOnlyWithAbstract = v),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        TextButton(
                          onPressed: () {
                            setModalState(() {
                              tempPageSize = 10;
                              tempSortBy = "relevance";
                              tempSortOrder = "desc";
                              tempMinScore = 0.0;
                              tempOnlyWithAbstract = false;
                            });
                          },
                          child: const Text('Clear'),
                        ),
                        const Spacer(),
                        ElevatedButton(
                          onPressed: () {
                            setState(() {
                              _pageSize = tempPageSize;
                              _sortBy = tempSortBy;
                              _sortOrder = tempSortOrder;
                              _minScore = tempMinScore;
                              _onlyWithAbstract = tempOnlyWithAbstract;
                            });
                            Navigator.of(ctx).pop();
                          },
                          child: const Text('Apply'),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }
}

class _LoadingCard extends StatelessWidget {
  const _LoadingCard();

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(10),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
                height: 14, width: double.infinity, color: Colors.black12),
            const SizedBox(height: 8),
            Container(height: 12, width: 160, color: Colors.black12),
            const SizedBox(height: 8),
            Container(
                height: 12, width: double.infinity, color: Colors.black12),
            const SizedBox(height: 6),
            Container(
                height: 12, width: double.infinity, color: Colors.black12),
          ],
        ),
      ),
    );
  }
}

class _SearchHeader extends StatelessWidget {
  const _SearchHeader({required this.queryController, required this.onSearch});

  final TextEditingController queryController;
  final VoidCallback onSearch;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const Text(
          'Discover Research',
          style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 4),
        const Text(
          'Search by title, author, or abstract keywords.',
          style: TextStyle(color: Color(0xFF6B7280)),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: queryController,
          decoration: const InputDecoration(
            labelText: 'Search publications',
            border: OutlineInputBorder(),
            prefixIcon: Icon(Icons.search),
          ),
          onSubmitted: (_) => onSearch(),
        ),
        const SizedBox(height: 8),
        ElevatedButton.icon(
          onPressed: onSearch,
          icon: const Icon(Icons.search),
          label: const Text('Search'),
        ),
      ],
    );
  }
}

class _FiltersBar extends StatelessWidget {
  const _FiltersBar({
    required this.pageSize,
    required this.sortBy,
    required this.sortOrder,
    required this.minScore,
    required this.onlyWithAbstract,
    required this.onPageSizeChanged,
    required this.onSortByChanged,
    required this.onSortOrderChanged,
    required this.onMinScoreChanged,
    required this.onOnlyWithAbstractChanged,
  });

  final int pageSize;
  final String sortBy;
  final String sortOrder;
  final double minScore;
  final bool onlyWithAbstract;
  final ValueChanged<int> onPageSizeChanged;
  final ValueChanged<String> onSortByChanged;
  final ValueChanged<String> onSortOrderChanged;
  final ValueChanged<double> onMinScoreChanged;
  final ValueChanged<bool> onOnlyWithAbstractChanged;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            Row(
              children: [
                Expanded(
                  child: DropdownButtonFormField<String>(
                    initialValue: sortBy,
                    decoration: const InputDecoration(labelText: 'Sort by'),
                    items: const [
                      DropdownMenuItem(
                          value: 'relevance', child: Text('Relevance')),
                      DropdownMenuItem(value: 'date', child: Text('Date')),
                      DropdownMenuItem(value: 'title', child: Text('Title')),
                    ],
                    onChanged: (v) => onSortByChanged(v ?? 'relevance'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: DropdownButtonFormField<String>(
                    initialValue: sortOrder,
                    decoration: const InputDecoration(labelText: 'Order'),
                    items: const [
                      DropdownMenuItem(value: 'desc', child: Text('Desc')),
                      DropdownMenuItem(value: 'asc', child: Text('Asc')),
                    ],
                    onChanged: (v) => onSortOrderChanged(v ?? 'desc'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: DropdownButtonFormField<int>(
                    initialValue: pageSize,
                    decoration: const InputDecoration(labelText: 'Page size'),
                    items: const [
                      DropdownMenuItem(value: 10, child: Text('10')),
                      DropdownMenuItem(value: 20, child: Text('20')),
                      DropdownMenuItem(value: 30, child: Text('30')),
                    ],
                    onChanged: (v) => onPageSizeChanged(v ?? 10),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Row(
                    children: [
                      Switch(
                        value: onlyWithAbstract,
                        onChanged: onOnlyWithAbstractChanged,
                      ),
                      const Text('Has abstract'),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                const Text('Min score'),
                Expanded(
                  child: Slider(
                    value: minScore,
                    min: 0,
                    max: 1,
                    divisions: 10,
                    label: minScore.toStringAsFixed(1),
                    onChanged: onMinScoreChanged,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _SearchStatus extends StatelessWidget {
  const _SearchStatus({
    required this.loading,
    required this.error,
    required this.total,
    required this.page,
    required this.totalPages,
    required this.pageResults,
    required this.searchMs,
  });

  final bool loading;
  final String? error;
  final int total;
  final int page;
  final int totalPages;
  final int pageResults;
  final int? searchMs;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        if (loading) const LinearProgressIndicator(),
        if (error != null)
          Padding(
            padding: const EdgeInsets.only(top: 8),
            child: Text(error!, style: const TextStyle(color: Colors.red)),
          ),
        const SizedBox(height: 4),
        Wrap(
          spacing: 8,
          children: [
            Chip(label: Text('Total: $total')),
            Chip(label: Text('Page: $page/$totalPages')),
            Chip(label: Text('Showing: $pageResults')),
            if (searchMs != null)
              Chip(
                  label:
                      Text('Time: ${(searchMs! / 1000).toStringAsFixed(2)}s')),
          ],
        ),
      ],
    );
  }
}

class _PaginationBar extends StatelessWidget {
  const _PaginationBar({
    required this.page,
    required this.totalPages,
    required this.loading,
    required this.onPrev,
    required this.onNext,
  });

  final int page;
  final int totalPages;
  final bool loading;
  final VoidCallback onPrev;
  final VoidCallback onNext;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        TextButton(
          onPressed: (page > 1 && !loading) ? onPrev : null,
          child: const Text('Prev'),
        ),
        Text('Page $page of $totalPages'),
        TextButton(
          onPressed: (page < totalPages && !loading) ? onNext : null,
          child: const Text('Next'),
        ),
      ],
    );
  }
}

class PublicationCard extends StatelessWidget {
  const PublicationCard({super.key, required this.publication});

  final Publication publication;

  Future<void> _openLink(String url) async {
    final uri = Uri.tryParse(url);
    if (uri == null) {
      return;
    }
    await launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  void _showDetails(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (ctx) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'Publication Details',
                        style: TextStyle(
                            fontSize: 16, fontWeight: FontWeight.bold),
                      ),
                      IconButton(
                        icon: const Icon(Icons.close),
                        onPressed: () => Navigator.of(ctx).pop(),
                      ),
                    ],
                  ),
                  Text(
                    publication.title,
                    style: const TextStyle(
                        fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  Text(publication.publishedDate.isEmpty
                      ? 'Date not available'
                      : publication.publishedDate),
                  const SizedBox(height: 8),
                  Text(publication.abstractText.isEmpty
                      ? 'No abstract available.'
                      : publication.abstractText),
                  const SizedBox(height: 12),
                  Wrap(
                    spacing: 6,
                    children: publication.authors
                        .map((a) => Chip(label: Text(a.name)))
                        .toList(),
                  ),
                  const SizedBox(height: 12),
                  ElevatedButton.icon(
                    onPressed: () => _openLink(publication.link),
                    icon: const Icon(Icons.open_in_new),
                    label: const Text('Open Publication'),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final maxAuthors = 2;
    final shownAuthors = publication.authors.take(maxAuthors).toList();
    final remainingAuthors = publication.authors.length - shownAuthors.length;

    return InkWell(
      onTap: () => _showDetails(context),
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(10),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      publication.title,
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                  ),
                  if (publication.score > 0)
                    Chip(
                        label: Text(
                            'Score ${publication.score.toStringAsFixed(2)}')),
                ],
              ),
              const SizedBox(height: 4),
              Text(publication.publishedDate.isEmpty
                  ? 'Date not available'
                  : publication.publishedDate),
              const SizedBox(height: 6),
              Text(
                publication.abstractText.isEmpty
                    ? 'No abstract available.'
                    : publication.abstractText,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 6),
              Wrap(
                spacing: 6,
                children: [
                  ...shownAuthors.map((a) => Chip(label: Text(a.name))),
                  if (remainingAuthors > 0)
                    Chip(label: Text('+$remainingAuthors')),
                ],
              ),
              const SizedBox(height: 6),
              Row(
                children: [
                  Expanded(
                    child: Text(
                      publication.link,
                      style: const TextStyle(color: Color(0xFF4F46E5)),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  IconButton(
                    tooltip: 'Open link',
                    onPressed: () => _openLink(publication.link),
                    icon: const Icon(Icons.open_in_new, size: 18),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class ClassificationScreen extends StatefulWidget {
  const ClassificationScreen({super.key});

  @override
  State<ClassificationScreen> createState() => _ClassificationScreenState();
}

class _ClassificationScreenState extends State<ClassificationScreen> {
  final _textController = TextEditingController();
  final _api = ApiService(baseUrl: kApiBaseUrl);

  String _modelType = 'naive_bayes';
  bool _loading = false;
  String? _error;
  ClassificationResult? _result;
  ModelInfo? _modelInfo;
  bool _training = false;

  Future<void> _loadModelInfo() async {
    try {
      final info = await _api.getModelInfo(modelType: _modelType);
      setState(() => _modelInfo = info);
    } catch (_) {
      setState(() => _modelInfo = null);
    }
  }

  Future<void> _trainModels() async {
    setState(() => _training = true);
    try {
      await _api.trainModels();
      await _loadModelInfo();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Models trained successfully.')),
        );
      }
    } finally {
      setState(() => _training = false);
    }
  }

  Future<void> _classify() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final res = await _api.classifyText(
        text: _textController.text.trim(),
        modelType: _modelType,
      );
      setState(() => _result = res);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  void initState() {
    super.initState();
    _loadModelInfo();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      height: MediaQuery.of(context).size.height,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: SingleChildScrollView(
          child: Column(
            children: [
              const Align(
                alignment: Alignment.centerLeft,
                child: Text(
                  'Document Classification',
                  style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
                ),
              ),
              const SizedBox(height: 6),
              const Align(
                alignment: Alignment.centerLeft,
                child: Text(
                  'Classify text into politics, business, or health.',
                  style: TextStyle(color: Color(0xFF6B7280)),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _textController,
                maxLines: 3,
                decoration: const InputDecoration(
                  labelText: 'Enter text to classify',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: DropdownButtonFormField<String>(
                      initialValue: _modelType,
                      decoration: const InputDecoration(labelText: 'Model'),
                      items: const [
                        DropdownMenuItem(
                            value: 'naive_bayes', child: Text('Naive Bayes')),
                        DropdownMenuItem(
                            value: 'logistic_regression',
                            child: Text('Logistic Regression')),
                      ],
                      onChanged: (value) {
                        setState(() => _modelType = value ?? 'naive_bayes');
                        _loadModelInfo();
                      },
                    ),
                  ),
                  const SizedBox(width: 12),
                  ElevatedButton(
                    onPressed: _training ? null : _trainModels,
                    child: _training
                        ? const Text('Training...')
                        : const Text('Train'),
                  ),
                ],
              ),
              if (_modelInfo != null)
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Wrap(
                    spacing: 8,
                    children: [
                      Chip(label: Text('Docs: ${_modelInfo!.totalDocuments}')),
                      Chip(label: Text('Trained: ${_modelInfo!.isTrained}')),
                    ],
                  ),
                ),
              const SizedBox(height: 12),
              ElevatedButton.icon(
                onPressed: _loading ? null : _classify,
                icon: const Icon(Icons.analytics),
                label: const Text('Classify'),
              ),
              if (_loading)
                const Padding(
                  padding: EdgeInsets.only(top: 8),
                  child: LinearProgressIndicator(),
                ),
              if (_error != null)
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child:
                      Text(_error!, style: const TextStyle(color: Colors.red)),
                ),
              if (_result != null)
                Padding(
                  padding: const EdgeInsets.only(top: 12),
                  child: Card(
                    child: ListTile(
                      title: Text('Prediction: ${_result!.predictedCategory}'),
                      subtitle: Text(
                        'Confidence: ${(_result!.confidence * 100).toStringAsFixed(1)}%\n${_result!.explanation}',
                      ),
                    ),
                  ),
                ),
              if (_result != null)
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Wrap(
                    spacing: 8,
                    children: _result!.probabilities.entries
                        .map((e) => Chip(
                            label: Text(
                                '${e.key}: ${(e.value * 100).toStringAsFixed(1)}%')))
                        .toList(),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
