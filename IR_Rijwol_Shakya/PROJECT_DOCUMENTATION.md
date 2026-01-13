# Intelligent Information Retrieval (ST7071CEM)

## Project Documentation — IR_Rijwol_Shakya

**Project type:** Vertical search engine + ML text categorization (classification + clustering)

---

## Table of Contents

1. Introduction
2. Crawler
   1. Crawler Overview
   2. Find the Authors
   3. Find the Publications
   4. Politeness (robots.txt + rate limiting)
   5. Scheduling
3. Classification
   1. Data Preparation
   2. Train/Test Split
   3. Model Selection
   4. Model Evaluation
   5. Classifying New Inputs
4. Search Engine
   1. Pre-processing
   2. Indexing (Inverted Index)
   3. Vectorization (TF–IDF)
5. User Interface
   1. Web UI
   2. Mobile UI
6. Search
   1. Query Processing
   2. Result Ranking
   3. Filtering + Pagination
7. Comparison (Index-based vs TF–IDF fallback)
8. Partial Search Query (Stemming-based matching)
9. Conclusion
10. References
11. Appendix

---

## 1. Introduction

This project implements a minimum viable vertical search engine (similar in interaction to Google Scholar) focused on retrieving publications from Coventry University’s PurePortal for the **ICS Research Centre for Computational Science and Mathematical Modelling**.

The system includes:

- A **polite web crawler** that collects publication metadata (title, link, authors, author profile links, publication date, abstract where available).
- An **indexer** that builds an **inverted index** from crawled content.
- A **query processor** that ranks results by relevance.
- A FastAPI backend to expose search and ML functionality.
- A Flutter web UI (and a Flutter mobile app) to provide an interactive interface with clickable links.

---

## 2. Crawler

### 2.1 Crawler Overview

The crawler is implemented in [IR_Rijwol_Shakya/crawler/crawler.py](IR_Rijwol_Shakya/crawler/crawler.py) using Selenium and BeautifulSoup.

**Target:** Coventry PurePortal organisation publications listing.

- Default portal root: `https://pureportal.coventry.ac.uk`
- Default listing URL: `/en/organisations/.../publications/?page=N`

**Pipeline design (2 stages):**

- **Stage 1 (Listing):** Collect all publication detail links from multiple paginated listing pages.
- **Stage 2 (Detail):** Visit each publication page and extract metadata.

**Outputs (JSON):**

- `data/publications_links.json` — minimal listing results (title + link).
- `data/publications.json` — merged detailed publication records.

### 2.2 Find the Authors

Authors are extracted primarily from the publication detail page.

The crawler attempts multiple strategies in order (fast + robust):

1. **Header anchors** above the PurePortal tab navigation: collects `/en/persons/<slug>` links and captures both:
   - `name`
   - `profile` (PurePortal author profile link)
2. **Subtitle parsing** (authors + date line): extracts author name patterns (e.g., `Surname, I.`)
3. **Meta tags** such as `citation_author`
4. **HTML fallback** using BeautifulSoup (`a[href*='/en/persons/']`)

The final author list is de-duplicated and stored as:

```json
"authors": [
  {"name": "First Last", "profile": "https://pureportal.../en/persons/..."}
]
```

### 2.3 Find the Publications

Stage 1 visits listing pages and extracts publication title + URL:

- CSS selector: `.result-container h3.title a`

Stage 2 visits each publication link and extracts:

- `title` (page `h1`)
- `link`
- `authors` (as described above)
- `published_date` (from `span.date`, `time[datetime]`, etc.)
- `abstract` (best-effort extraction)

### 2.4 Politeness (robots.txt + rate limiting)

To avoid hitting servers too fast and to respect crawling rules, the crawler implements:

1. **robots.txt parsing** using `urllib.robotparser`:
   - `can_fetch(USER_AGENT, url)` is checked before each page load.
2. **Crawl delay enforcement**:
   - Uses the maximum of:
     - `CRAWLER_DELAY` (local configured minimum delay)
     - `robots.txt` crawl-delay (if present)
   - Applies per-host waiting based on the last request time.

Relevant behavior is implemented via:

- `_robots_allow(url)`
- `_respect_crawl_delay(url)`

> Note: Selenium loads pages in a browser, but the project still enforces robots rules and host-level delay **before** each navigation.

### 2.5 Scheduling

A weekly scheduler exists in [IR_Rijwol_Shakya/crawler/schedule_crawler.py](IR_Rijwol_Shakya/crawler/schedule_crawler.py) using APScheduler.

Default schedule:

- **Sunday 00:00** (weekly)

It launches the crawler via the virtual environment’s Python (if available) or falls back to the system Python.

---

## 3. Classification

This project includes a text classification component implemented in [IR_Rijwol_Shakya/backend/classification_ml.py](IR_Rijwol_Shakya/backend/classification_ml.py).

### 3.1 Data Preparation

Training data is loaded from:

- `data/categories.csv`
- `data/training_documents.csv`

The dataset contains at least these classes:

- `business`
- `entertainment`
- `health`

Pre-processing steps:

- lowercasing
- removing non-alphanumeric characters
- tokenization
- stop-word removal
- stemming using Porter Stemmer

### 3.2 Train/Test Split

The training pipeline splits the dataset into train and test sets internally (via scikit-learn utilities).

### 3.3 Model Selection

Two model types are supported:

- Naïve Bayes (`multinomial_nb`)
- Logistic Regression

The API exposes model selection via `model_type`.

### 3.4 Model Evaluation

The training function computes:

- accuracy
- classification report (precision/recall/F1)

These are returned by `/train-models`.

### 3.5 Classifying New Inputs

Classification is provided via FastAPI:

- `POST /classify` with `{ "text": "...", "model_type": "naive_bayes" }`

The response includes:

- predicted category
- confidence
- probability distribution across categories
- explanation string

---

## 4. Search Engine

The search engine is implemented in:

- [IR_Rijwol_Shakya/backend/search.py](IR_Rijwol_Shakya/backend/search.py)
- [IR_Rijwol_Shakya/backend/indexer.py](IR_Rijwol_Shakya/backend/indexer.py)

### 4.1 Pre-processing

For both indexing and query processing, the system applies:

- lowercasing
- punctuation removal
- tokenization (NLTK)
- stop-word removal (NLTK)
- stemming (Porter stemmer)

This makes matching more robust to variations like pluralization and word forms.

### 4.2 Indexing (Inverted Index)

The inverted index is constructed by [IR_Rijwol_Shakya/backend/indexer.py](IR_Rijwol_Shakya/backend/indexer.py).

Each document is a publication record. Indexing text uses:

- title
- authors (names)
- abstract

**Index structure (stored in `data/inverted_index.json`):**

```json
{
  "docs": [ {"title": "...", "authors": [...], "abstract": "...", "published_date": "...", "link": "..."} ],
  "doc_len": [123, 98, 110],
  "index": {
    "term": {
      "df": 10,
      "postings": {"0": 2, "5": 1}
    }
  }
}
```

### 4.3 Vectorization (TF–IDF)

The search engine supports two retrieval modes:

1. **Index-based scoring (preferred when `inverted_index.json` exists):**

   - Computes a lightweight TF–IDF style score per document:
     - $idf = \log\left(\frac{N+1}{df+1}\right)+1$
     - $score += \frac{tf}{doc\_len} \cdot idf$

2. **TF–IDF matrix fallback (if no index exists):**
   - Builds a TF–IDF matrix using scikit-learn’s `TfidfVectorizer`
   - Ranks results by cosine similarity between query vector and document vectors

---

## 5. User Interface

### 5.1 Web UI

Flutter web UI is implemented in:

- [IR_Rijwol_Shakya/flutter_web/lib/main.dart](IR_Rijwol_Shakya/flutter_web/lib/main.dart)
- [IR_Rijwol_Shakya/flutter_web/lib/api.dart](IR_Rijwol_Shakya/flutter_web/lib/api.dart)

Capabilities:

- Search publications
- Filter by author
- Filter by year range
- Sort results
- Click publication links (opens in browser)

API base URL is configurable with:

- `--dart-define=API_BASE_URL=http://localhost:8000`

### 5.2 Mobile UI

Flutter mobile app exists under:

- [IR_Rijwol_Shakya/mobile](IR_Rijwol_Shakya/mobile)

It connects to the same FastAPI backend (base URL can be overridden at runtime).

---

## 6. Search

### 6.1 Query Processing

The backend endpoint is:

- `GET /search?query=...&page=1&size=10&author=...&year_from=...&year_to=...&sort=score`

The system normalizes and stems the query and ranks the most relevant publications.

### 6.2 Result Ranking

Default ranking:

- `sort=score` (descending)

Additional sorting supported:

- `sort=date`
- `sort=title`

### 6.3 Filtering + Pagination

Filtering:

- author substring match in author names
- year range match extracted from `published_date`

Pagination:

- `page` and `size`
- returns `total` and `total_pages`

---

## 7. Comparison (Index-based vs TF–IDF fallback)

This project can run in either:

- **Index-based mode:** fast scoring using a persistent inverted index.
- **TF–IDF fallback mode:** recomputed TF–IDF matrix in-memory when no index file is present.

In typical usage, index-based mode is recommended because:

- It avoids recomputing document vectors at server startup.
- It aligns closely with IR principles taught in the module (inverted index + postings lists).

---

## 8. Partial Search Query (Stemming-based matching)

Because both indexing and querying use Porter stemming, queries can match multiple word forms.

Example:

- Query: `computing models`
- Can match documents containing `compute`, `computer`, `computational`, etc., after stemming.

> This project uses stemming (not lemmatization). If you want to show “stemming vs lemmatizer” in the report/viva, you can describe stemming formally and explain why it was chosen.

---

## 9. Conclusion

The system provides an end-to-end vertical IR pipeline:

- Crawling PurePortal publication pages
- Extracting and storing structured metadata
- Building an inverted index
- Ranking results by relevance
- Providing a usable web/mobile interface

It also includes ML components (classification and clustering) to demonstrate the module’s learning outcomes related to text analytics.

---

## 10. References

Fill this section with the sources you used for:

- training documents (news sites / datasets)
- any libraries or tutorials that influenced your approach

> Do not claim sources you did not use. Add citations matching your report style (Harvard/IEEE) as required.

---

## 11. Appendix

### A. How to Run (recommended)

From the project root:

1. Start backend + Flutter web:

```bash
START_WEB=1 bash run.sh
```

2. Stop everything:

```bash
bash stop.sh
```

### B. Run crawler manually

```bash
cd IR_Rijwol_Shakya/crawler
python3 crawler.py --max-pages 10 --workers 3 --use-regular-selenium --rebuild-index
```

### C. Backend API summary

- `GET /health`
- `GET /search`
- `POST /classify`
- `GET /model-info`
- `POST /train-models`
- `POST /cluster`
- `GET /cluster-model-info`
- `POST /train-cluster-model`

### D. Key output files

- `data/publications_links.json`
- `data/publications.json`
- `data/inverted_index.json`
- `data/categories.csv`
- `data/training_documents.csv`

### E. Screenshots to include in report/viva

Add screenshots for:

- crawler running and saving outputs
- inverted index JSON structure
- search results UI with clickable links
- classification results for multiple inputs (short/long; with/without stop words)
- clustering results for multiple inputs
