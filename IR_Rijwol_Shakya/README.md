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

## Crawler
Crawler uses Playwright with a persistent profile to pass captcha:

```bash
cd IR_Rijwol_Shakya/crawler
pip install -r requirements.txt
python3 -m playwright install chromium

# First run (visible) to solve captcha:
python3 playwright_crawler.py --outdir ../data --user-data-dir ./pw-profile --headless 0 --wait-for-human

# Later runs (headless) reuse the profile:
python3 playwright_crawler.py --outdir ../data --user-data-dir ./pw-profile --headless 1
```

Crawler options:
- `--portal-root` (env: `PORTAL_ROOT`)
- `--base-url` (env: `BASE_URL`)
- `--retries` (env: `CRAWLER_RETRIES`)
- `--retry-delay` (env: `CRAWLER_RETRY_DELAY`)
- `--screenshot-dir` to save failure screenshots
- `--user-data-dir` to reuse captcha-approved session (Playwright)

### OpenAlex (data science) test data
If you need large, captcha-free test data, use OpenAlex:

```bash
cd IR_Rijwol_Shakya/crawler
pip install -r requirements.txt
python3 openalex_crawler.py --outdir ../data --query "data science" --max-records 2000 --mailto you@example.com
```

## Next steps
- Adjust crawler targets and selectors if you change the source portal
- Populate `data/publications.json` and `data/training_documents.csv`
- Tweak Flutter UI and filters to match your desired design
