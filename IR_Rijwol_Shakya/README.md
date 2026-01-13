# IR_Rijwol_Shakya

Rewritten IR project with FastAPI backend + Flutter mobile app.

## Structure
- backend/: FastAPI API server (search + classification)
- crawler/: Selenium crawler (Coventry PurePortal)
- data/: publications + training data
- mobile/: Flutter mobile app

## Backend setup
1) Create venv and install requirements:

```bash
cd IR_Rijwol_Shakya/backend
python3 -m venv ../.venv
source ../.venv/bin/activate
pip install -r requirements.txt
```

2) Run backend:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Environment options:
- `DATA_DIR` (default `../data`)
- `SEARCH_CACHE_TTL` in seconds (default `60`)
- `SEARCH_CACHE_MAX` (default `128`)

## Flutter mobile app
1) Install Flutter SDK and run:

```bash
cd IR_Rijwol_Shakya/mobile
flutter pub get
flutter run
```

2) API base URL is set in `mobile/lib/main.dart` (default Android emulator):
- Android emulator: `http://10.0.2.2:8000`
- iOS simulator: `http://localhost:8000`
- Real device: use your LAN IP (e.g., `http://192.168.x.x:8000`)

You can also override at runtime:

```bash
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

## Flutter web app
1) Install Flutter SDK and run:

```bash
cd IR_Rijwol_Shakya/flutter_web
flutter pub get
flutter run -d chrome
```

2) API base URL is set in `flutter_web/lib/main.dart` (default localhost):
- Web (local backend): `http://localhost:8000`

You can also override at runtime:

```bash
flutter run -d chrome --dart-define=API_BASE_URL=http://localhost:8000
```

## Crawler
Crawler uses Selenium + BeautifulSoup for Coventry PurePortal:

```bash
cd IR_Rijwol_Shakya/crawler
pip install -r requirements.txt
python3 crawler.py --max-pages 10 --workers 3 --use-regular-selenium
```

Crawler options:
- Default target: Coventry PurePortal ICS Research Centre publications
- `--portal-root` (env: `PORTAL_ROOT`)
- `--base-url` (env: `BASE_URL`)
- `--retries` (env: `CRAWLER_RETRIES`)
- `--retry-delay` (env: `CRAWLER_RETRY_DELAY`)
- `--crawl-delay` (env: `CRAWLER_DELAY`) to respect polite delays
- `--screenshot-dir` to save failure screenshots
- `--rebuild-index` to refresh the inverted index after crawl

### Scheduled crawl (weekly)
Run a simple weekly scheduler (Sunday at midnight):

```bash
cd IR_Rijwol_Shakya/crawler
python3 schedule_crawler.py
```

## Next steps
- Adjust crawler targets and selectors if you change the source portal
- Populate `data/publications.json` and `data/training_documents.csv`
- Build the inverted index after crawling: `python3 backend/indexer.py --data-dir data`
- Tweak Flutter UI and filters to match your desired design

## Assignment compliance checklist
- Crawler targets Coventry PurePortal (ICS Research Centre) and extracts title, authors, date, abstract, and author profile links.
- Politeness: robots.txt checks, crawl delay, and retries are built in.
- Inverted index: build with `backend/indexer.py` and search uses it when available.
- Query processor: ranked results exposed via `/search` and shown in Flutter web.
- Classification: Naive Bayes and Logistic Regression models trained from `data/` CSVs.
