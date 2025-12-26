#!/usr/bin/env python3
"""
Playwright crawler with persistent profile to pass captcha once.
Run first time with --headless=0 to solve captcha, then reuse the profile.
"""
import argparse
import json
import os
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

DEFAULT_PORTAL_ROOT = os.getenv("PORTAL_ROOT", "https://pureportal.coventry.ac.uk")
DEFAULT_BASE_URL = os.getenv(
    "BASE_URL",
    f"{DEFAULT_PORTAL_ROOT}/en/organisations/fbl-school-of-economics-finance-and-accounting/publications/",
)
PERSONS_PREFIX = "/en/persons/"

FIRST_DIGIT = re.compile(r"\d")
NAME_PAIR = re.compile(
    r"[A-Z][A-Za-z'’\-]+,\s*(?:[A-Z](?:\.)?)(?:\s*[A-Z](?:\.)?)*", flags=re.UNICODE
)
SPACE = re.compile(r"\s+")


def _uniq_str(seq: List[str]) -> List[str]:
    seen, out = set(), []
    for x in seq:
        x = x.strip()
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _uniq_authors(
    objs: List[Dict[str, Optional[str]]],
) -> List[Dict[str, Optional[str]]]:
    seen: set[Tuple[str, str]] = set()
    out: List[Dict[str, Optional[str]]] = []
    for o in objs:
        name = (o.get("name") or "").strip()
        profile = (o.get("profile") or "").strip()
        key = (name, profile)
        if name and key not in seen:
            seen.add(key)
            out.append({"name": name, "profile": profile or None})
    return out


def _is_person_profile_url(href: str) -> bool:
    if not href:
        return False
    try:
        u = urlparse(href)
    except Exception:
        return False
    if u.netloc and "coventry.ac.uk" not in u.netloc:
        return False
    path = (u.path or "").rstrip("/")
    if not path.startswith(PERSONS_PREFIX):
        return False
    slug = path[len(PERSONS_PREFIX) :].strip("/")
    if not slug or slug.startswith("?"):
        return False
    return True


def _looks_like_person_name(text: str) -> bool:
    if not text:
        return False
    t = text.strip()
    bad = {"profiles", "persons", "people", "overview"}
    if t.lower() in bad:
        return False
    return ((" " in t) or ("," in t)) and sum(ch.isalpha() for ch in t) >= 4


def _authors_from_page(page) -> List[Dict]:
    anchors = page.query_selector_all("a[href*='/en/persons/']")
    candidates: List[Dict[str, Optional[str]]] = []
    for a in anchors:
        try:
            href = (a.get_attribute("href") or "").strip()
            if not _is_person_profile_url(href):
                continue
            text = (a.inner_text() or "").strip()
            if not _looks_like_person_name(text):
                continue
            candidates.append({"name": text, "profile": urljoin(page.url, href)})
        except Exception:
            continue
    return _uniq_authors(candidates)


def _authors_from_subtitle(page, title_text: str) -> List[str]:
    date_el = page.query_selector("span.date")
    if not date_el:
        return []
    try:
        subtitle = date_el.evaluate_handle("el => el.closest('.subtitle') || el.parentElement")
        line = subtitle.evaluate("el => el.innerText") if subtitle else ""
    except Exception:
        line = ""
    if title_text and title_text in line:
        line = line.replace(title_text, "")
    line = " ".join(line.split()).strip()
    m = FIRST_DIGIT.search(line)
    pre_date = line[: m.start()].strip(" -—–·•,;|") if m else line
    pre_date = pre_date.replace(" & ", ", ").replace(" and ", ", ")
    pairs = NAME_PAIR.findall(pre_date)
    return _uniq_str(pairs)


def _wrap_names_as_objs(names: List[str]) -> List[Dict]:
    return _uniq_authors([{"name": n, "profile": None} for n in names])


def _extract_detail(page, link: str, title_hint: str) -> Dict:
    page.goto(link, wait_until="domcontentloaded")
    time.sleep(0.2)

    title = title_hint or ""
    try:
        h1 = page.query_selector("h1")
        if h1:
            title = h1.inner_text().strip()
    except Exception:
        pass

    published_date = ""
    try:
        date_el = page.query_selector("span.date")
        if date_el:
            published_date = date_el.inner_text().strip()
    except Exception:
        pass

    author_objs = _authors_from_page(page)
    if not author_objs:
        names = _authors_from_subtitle(page, title)
        author_objs = _wrap_names_as_objs(names)

    abstract_txt = ""
    try:
        candidates = page.query_selector_all("div.textblock, div.abstract, section.abstract")
        for c in candidates:
            txt = (c.inner_text() or "").strip()
            if len(txt) > 40:
                abstract_txt = txt[:1000]
                break
    except Exception:
        pass

    return {
        "title": title,
        "link": link,
        "authors": author_objs,
        "published_date": published_date,
        "abstract": abstract_txt,
    }


def _gather_listing(page, base_url: str, max_pages: int) -> List[Dict]:
    all_rows: List[Dict] = []
    for page_idx in range(max_pages):
        url = f"{base_url}?page={page_idx}"
        page.goto(url, wait_until="domcontentloaded")
        try:
            page.wait_for_selector(".result-container h3.title a", timeout=8000)
        except PWTimeout:
            pass
        rows = []
        for a in page.query_selector_all(".result-container h3.title a"):
            title = (a.inner_text() or "").strip()
            link = a.get_attribute("href") or ""
            if title and link:
                rows.append({"title": title, "link": link})
        if rows:
            all_rows.extend(rows)
            print(f"[LIST] Page {page_idx+1}/{max_pages} → {len(rows)} items")
        else:
            print(f"[LIST] Page {page_idx+1}/{max_pages} → empty (stopping early)")
            break
    uniq = {}
    for r in all_rows:
        uniq[r["link"]] = r
    return list(uniq.values())


def main():
    ap = argparse.ArgumentParser(description="Playwright crawler (persistent profile).")
    ap.add_argument("--outdir", default="../data")
    ap.add_argument("--base-url", default=DEFAULT_BASE_URL)
    ap.add_argument("--max-pages", type=int, default=10)
    ap.add_argument("--user-data-dir", default="./pw-profile")
    ap.add_argument("--headless", type=int, default=0, help="0 = visible, 1 = headless")
    ap.add_argument(
        "--wait-for-human",
        action="store_true",
        help="Pause before crawling so you can solve captcha.",
    )
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            args.user_data_dir,
            headless=bool(args.headless),
            viewport={"width": 1366, "height": 900},
        )
        page = context.new_page()

        if args.wait_for_human and not args.headless:
            # Navigate to the listing page so the captcha is visible.
            page.goto(args.base_url, wait_until="domcontentloaded")
            print("Solve the captcha in the opened browser tab, then press Enter here to continue...")
            input()

        print("[STAGE 1] Collecting listing links…")
        listing = _gather_listing(page, args.base_url, args.max_pages)
        if not listing:
            print("No publications found on listing pages.")
            context.close()
            return

        (outdir / "publications_links.json").write_text(
            json.dumps(listing, indent=2), encoding="utf-8"
        )

        print("[STAGE 2] Scraping details…")
        results = []
        for i, it in enumerate(listing, 1):
            try:
                rec = _extract_detail(page, it["link"], it.get("title", ""))
                results.append(rec)
                if i % 5 == 0:
                    print(f"[DETAIL] {i}/{len(listing)} parsed")
            except Exception as e:
                print(f"[DETAIL] ERR {it['link']}: {str(e)[:100]}")
                results.append(
                    {
                        "title": it.get("title", ""),
                        "link": it["link"],
                        "authors": [],
                        "published_date": "",
                        "abstract": "",
                    }
                )

        (outdir / "publications.json").write_text(
            json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        context.close()
        print(f"[DONE] Saved {len(results)} records → {outdir / 'publications.json'}")


if __name__ == "__main__":
    main()
