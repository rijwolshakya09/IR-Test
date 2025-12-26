#!/usr/bin/env python3
"""
OpenAlex crawler for data-science testing data.
Generates publications.json/publications_links.json compatible with the app.
"""
import argparse
import json
import time
from pathlib import Path
from typing import Dict, List

import requests

OPENALEX_BASE = "https://api.openalex.org/works"


def _decode_abstract(inv_idx: Dict) -> str:
    """Convert OpenAlex inverted index to a string."""
    if not inv_idx:
        return ""
    pos_to_word = {}
    for word, positions in inv_idx.items():
        for pos in positions:
            pos_to_word[pos] = word
    return " ".join(pos_to_word[i] for i in sorted(pos_to_word.keys()))


def _authors_list(authorships: List[Dict]) -> List[Dict]:
    out = []
    for a in authorships or []:
        author = a.get("author") or {}
        name = (author.get("display_name") or "").strip()
        if name:
            out.append({"name": name, "profile": author.get("id")})
    return out


def _record_from_work(w: Dict) -> Dict:
    abstract = _decode_abstract(w.get("abstract_inverted_index") or {})
    link = w.get("doi") or w.get("primary_location", {}).get("landing_page_url") or w.get("id")
    return {
        "title": w.get("title") or "",
        "link": link or "",
        "authors": _authors_list(w.get("authorships") or []),
        "published_date": w.get("publication_date") or "",
        "abstract": abstract,
    }


def main():
    ap = argparse.ArgumentParser(description="OpenAlex data-science crawler")
    ap.add_argument("--outdir", default="../data")
    ap.add_argument("--query", default="data science")
    ap.add_argument("--max-records", type=int, default=1000)
    ap.add_argument("--per-page", type=int, default=200)
    ap.add_argument("--mailto", default=None, help="Contact email for OpenAlex polite pool")
    ap.add_argument("--sleep", type=float, default=0.1, help="Delay between requests")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    headers = {"User-Agent": "IR_Rijwol_Shakya/1.0"}
    if args.mailto:
        headers["User-Agent"] += f" (mailto:{args.mailto})"

    cursor = "*"
    records: List[Dict] = []
    links: List[Dict] = []

    while len(records) < args.max_records:
        params = {
            "search": args.query,
            "per-page": min(200, args.per_page),
            "cursor": cursor,
        }
        r = requests.get(OPENALEX_BASE, params=params, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()
        works = data.get("results", [])
        if not works:
            break
        for w in works:
            rec = _record_from_work(w)
            records.append(rec)
            links.append({"title": rec["title"], "link": rec["link"]})
            if len(records) >= args.max_records:
                break
        cursor = data.get("meta", {}).get("next_cursor")
        if not cursor:
            break
        time.sleep(args.sleep)

    (outdir / "publications.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (outdir / "publications_links.json").write_text(
        json.dumps(links, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[DONE] Saved {len(records)} records → {outdir / 'publications.json'}")


if __name__ == "__main__":
    main()
