#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse, json, os, time, re, unicodedata, random
from math import ceil
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse, quote
from urllib import robotparser, request as urlrequest
from threading import Lock
import subprocess
import sys

from bs4 import BeautifulSoup

# Undetected Chrome Driver
try:
    import undetected_chromedriver as uc
    USE_UNDETECTED = True
except ImportError:
    print("[WARNING] undetected-chromedriver not installed. Install with: pip install undetected-chromedriver")
    print("[WARNING] Falling back to regular Selenium (may fail with Cloudflare)")
    USE_UNDETECTED = False

# Selenium - always import these
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Selenium Stealth
try:
    from selenium_stealth import stealth
    USE_STEALTH = True
    print("[INFO] selenium-stealth is available")
except ImportError:
    USE_STEALTH = False
    print("[WARNING] selenium-stealth not installed. Install with: pip install selenium-stealth")
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Parallelism
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------- Config ----------
DEFAULT_PORTAL_ROOT = os.getenv("PORTAL_ROOT", "https://pureportal.coventry.ac.uk")
DEFAULT_BASE_URL = os.getenv(
    "BASE_URL",
    f"{DEFAULT_PORTAL_ROOT}/en/organisations/ics-research-centre-for-computational-science-and-mathematical-mo/publications/",
)
PORTAL_ROOT = DEFAULT_PORTAL_ROOT
PERSONS_PREFIX = "/en/persons/"
BASE_URL = DEFAULT_BASE_URL
RETRIES = int(os.getenv("CRAWLER_RETRIES", "3"))
RETRY_DELAY = float(os.getenv("CRAWLER_RETRY_DELAY", "2.5"))
CRAWL_DELAY = float(os.getenv("CRAWLER_DELAY", "1.0"))
SCREENSHOT_DIR = None
DEBUG_CAPTURE = False
USER_AGENT = os.getenv(
    "CRAWLER_USER_AGENT",
    "IR-Crawler/1.0 (+https://pureportal.coventry.ac.uk)",
)
_ROBOTS_CACHE: Dict[str, robotparser.RobotFileParser] = {}
_ROBOTS_LOCK = Lock()
_LAST_REQUEST: Dict[str, float] = {}


# =========================== Chrome helpers ===========================
def build_chrome_options_stealth(headless: bool, legacy_headless: bool = False):
    """Build Chrome options with enhanced stealth features"""
    if USE_UNDETECTED:
        options = uc.ChromeOptions()
    else:
        options = Options()
    
    if headless:
        if legacy_headless:
            options.add_argument("--headless")
        else:
            options.add_argument("--headless=new")
    
    # Realistic window size
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    
    # Anti-detection arguments
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    
    # Updated user agent (Chrome 131)
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )
    
    # Preferences to appear more human
    prefs = {
        "profile.default_content_setting_values": {
            "notifications": 2,
            "geolocation": 2,
        },
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
    }
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # Performance optimizations
    options.page_load_strategy = "normal"  # Changed from "eager" for better Cloudflare handling
    
    return options


def make_driver(headless: bool, legacy_headless: bool = False):
    """Create a stealth web driver"""
    if USE_UNDETECTED:
        # Undetected ChromeDriver - best for bypassing Cloudflare
        options = build_chrome_options_stealth(headless, legacy_headless)
        
        # Fix for Apple Silicon Macs
        import platform
        use_subprocess = False
        if platform.system() == 'Darwin' and platform.machine() == 'arm64':
            print("[INFO] Detected Apple Silicon Mac - using subprocess mode")
            use_subprocess = True
        
        try:
            driver = uc.Chrome(
                options=options,
                version_main=None,  # Auto-detect Chrome version
                driver_executable_path=None,
                headless=headless,
                use_subprocess=use_subprocess
            )
        except Exception as e:
            if "Bad CPU type" in str(e) or "arm64" in str(e):
                print(f"[WARNING] undetected-chromedriver failed on Apple Silicon: {e}")
                print("[INFO] Falling back to regular Selenium...")
                # Fall back to regular Selenium
                service = ChromeService(ChromeDriverManager().install(), log_output=os.devnull)
                options = build_chrome_options_stealth(headless, legacy_headless)
                driver = webdriver.Chrome(service=service, options=options)
            else:
                raise
    else:
        # Regular Selenium with stealth enhancements
        service = ChromeService(ChromeDriverManager().install(), log_output=os.devnull)
        options = build_chrome_options_stealth(headless, legacy_headless)
        driver = webdriver.Chrome(service=service, options=options)
    
    # Set timeouts
    driver.set_page_load_timeout(30)
    driver.implicitly_wait(1)
    
    # Apply selenium-stealth if available
    if USE_STEALTH and not USE_UNDETECTED:
        print("[STEALTH] Applying selenium-stealth patches...")
        stealth(driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
        )
    
    # Inject anti-detection JavaScript
    try:
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
                window.chrome = {runtime: {}, loadTimes: function() {}, csi: function() {}};
                Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
                Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
                
                // Spoof permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """
        })
    except Exception:
        pass
    
    return driver


def _maybe_screenshot(driver, label: str):
    if not SCREENSHOT_DIR:
        return
    try:
        Path(SCREENSHOT_DIR).mkdir(parents=True, exist_ok=True)
        ts = int(time.time())
        out = Path(SCREENSHOT_DIR) / f"{label}-{ts}.png"
        driver.save_screenshot(str(out))
        print(f"[SCREENSHOT] Saved to {out}")
    except Exception as e:
        print(f"[SCREENSHOT] Failed: {e}")


def _maybe_dump_html(driver, label: str):
    if not SCREENSHOT_DIR:
        return
    try:
        Path(SCREENSHOT_DIR).mkdir(parents=True, exist_ok=True)
        ts = int(time.time())
        out = Path(SCREENSHOT_DIR) / f"{label}-{ts}.html"
        out.write_text(driver.page_source, encoding="utf-8")
        print(f"[HTML] Saved to {out}")
    except Exception as e:
        print(f"[HTML] Failed: {e}")


def _fetch_robots_txt(robots_url: str) -> Optional[str]:
    try:
        req = urlrequest.Request(robots_url, headers={"User-Agent": USER_AGENT})
        with urlrequest.urlopen(req, timeout=10) as resp:
            return resp.read().decode("utf-8", "ignore")
    except Exception as e:
        print(f"[ROBOTS] Warning: failed to fetch {robots_url}: {e}")
        return None


def _get_robot_parser(url: str) -> robotparser.RobotFileParser:
    parsed = urlparse(url)
    key = parsed.netloc
    with _ROBOTS_LOCK:
        rp = _ROBOTS_CACHE.get(key)
        if rp:
            return rp
        rp = robotparser.RobotFileParser()
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        body = _fetch_robots_txt(robots_url)
        if body is None:
            rp.parse([])
        else:
            rp.parse(body.splitlines())
        _ROBOTS_CACHE[key] = rp
        return rp


def _robots_allow(url: str) -> bool:
    rp = _get_robot_parser(url)
    return rp.can_fetch(USER_AGENT, url)


def _robots_delay(url: str) -> float:
    rp = _get_robot_parser(url)
    delay = rp.crawl_delay(USER_AGENT)
    return float(delay) if delay else 0.0


def _respect_crawl_delay(url: str):
    parsed = urlparse(url)
    netloc = parsed.netloc
    delay = max(CRAWL_DELAY, _robots_delay(url))
    if delay <= 0:
        return
    with _ROBOTS_LOCK:
        last = _LAST_REQUEST.get(netloc)
        now = time.monotonic()
        if last is not None:
            wait = delay - (now - last)
            if wait > 0:
                print(f"[POLITE] Sleeping {wait:.1f}s before next request to {netloc}")
                time.sleep(wait)
        _LAST_REQUEST[netloc] = time.monotonic()


def wait_for_cloudflare_with_auto_click(driver, timeout: int = 30) -> bool:
    """Wait for Cloudflare challenge and attempt to auto-click if possible"""
    try:
        print("[CLOUDFLARE] Checking for challenge...")
        start = time.time()
        last_action_time = start
        
        while time.time() - start < timeout:
            page_source = driver.page_source.lower()
            page_title = driver.title.lower()
            
            # Check if we're past Cloudflare
            if "cloudflare" not in page_source and "cloudflare" not in page_title:
                print("[CLOUDFLARE] ✓ No challenge detected - page loaded!")
                return True
            
            # Try to find and click the Cloudflare checkbox automatically
            try:
                # Look for Turnstile challenge iframe
                iframes = driver.find_elements(By.TAG_NAME, "iframe")
                for iframe in iframes:
                    iframe_src = iframe.get_attribute("src") or ""
                    if "challenges.cloudflare.com" in iframe_src or "turnstile" in iframe_src:
                        # Switch to iframe and try to click
                        try:
                            driver.switch_to.frame(iframe)
                            time.sleep(1)
                            
                            # Try multiple selectors for the checkbox
                            checkbox_selectors = [
                                "input[type='checkbox']",
                                "label",
                                "#challenge-stage",
                                ".ctp-checkbox-container",
                                "body"  # Sometimes clicking anywhere in the frame works
                            ]
                            
                            for selector in checkbox_selectors:
                                try:
                                    element = driver.find_element(By.CSS_SELECTOR, selector)
                                    if element.is_displayed():
                                        print("[CLOUDFLARE] 🤖 Attempting auto-click on challenge...")
                                        element.click()
                                        time.sleep(2)
                                        driver.switch_to.default_content()
                                        last_action_time = time.time()
                                        break
                                except:
                                    continue
                            
                            driver.switch_to.default_content()
                        except:
                            driver.switch_to.default_content()
                            pass
            except:
                pass
            
            # Check for different challenge states
            if "just a moment" in page_source or "checking your browser" in page_source:
                elapsed = int(time.time() - start)
                if elapsed - int(last_action_time - start) > 10:
                    print(f"[CLOUDFLARE] ⚠️  Challenge still active after {elapsed}s")
                    print("[CLOUDFLARE] You may need to manually click 'Verify you are human' in the browser")
                time.sleep(2)
                continue
            
            # Check for challenge form
            if driver.find_elements(By.ID, "challenge-form"):
                print(f"[CLOUDFLARE] Auto-challenge in progress... ({int(time.time() - start)}s)")
                time.sleep(2)
                continue
            
            # Might be complete
            print("[CLOUDFLARE] ✓ Challenge appears complete!")
            time.sleep(1)
            return True
        
        print(f"[CLOUDFLARE] ⏱️  Timeout after {timeout}s")
        return False
        
    except Exception as e:
        print(f"[CLOUDFLARE] Error: {e}")
        return False


def safe_get(driver, url: str, label: str):
    """Enhanced safe_get with Cloudflare handling and retries"""
    last_exc = None
    
    for attempt in range(RETRIES + 1):
        try:
            if not _robots_allow(url):
                raise Exception("Blocked by robots.txt rules")
            _respect_crawl_delay(url)

            # Random delay before request (human-like behavior)
            delay = random.uniform(2, 4) if attempt == 0 else random.uniform(3, 6)
            print(f"[{label}] Waiting {delay:.1f}s before request (attempt {attempt + 1}/{RETRIES + 1})")
            time.sleep(delay)
            
            # Load page
            print(f"[{label}] Loading: {url}")
            driver.get(url)
            
            # Additional wait for page to settle
            time.sleep(random.uniform(2, 4))
            
            # Check for Cloudflare challenge
            page_source = driver.page_source.lower()
            page_title = driver.title.lower()
            
            if "cloudflare" in page_source or "cloudflare" in page_title or "just a moment" in page_source:
                _maybe_screenshot(driver, f"{label}-cloudflare-{attempt}")
                if not wait_for_cloudflare_with_auto_click(driver, timeout=45):  # Increased timeout for manual action
                    raise Exception("Cloudflare challenge not completed")
            
            # Verify we got actual content
            if len(driver.page_source) < 1000:
                raise Exception("Page content too short, possible blocking")
            
            # Additional check - make sure we're on the right page
            if "pureportal.coventry.ac.uk" not in driver.current_url:
                raise Exception(f"Unexpected redirect to: {driver.current_url}")
            
            print(f"[{label}] ✓ Page loaded successfully")
            return
            
        except Exception as exc:
            last_exc = exc
            print(f"[{label}] ❌ Attempt {attempt + 1} failed: {str(exc)[:100]}")
            _maybe_screenshot(driver, f"{label}-error-attempt{attempt+1}")
            _maybe_dump_html(driver, f"{label}-error-attempt{attempt+1}")
            
            if attempt < RETRIES:
                backoff = RETRY_DELAY * (attempt + 1) * random.uniform(1.5, 2.5)
                print(f"[{label}] Retrying in {backoff:.1f}s...")
                time.sleep(backoff)
    
    if last_exc:
        raise last_exc


def accept_cookies_if_present(driver):
    """Accept cookie consent if present"""
    try:
        btn = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "onetrust-accept-btn-handler"))
        )
        driver.execute_script("arguments[0].click();", btn)
        print("[COOKIES] Accepted")
        time.sleep(0.5)
    except TimeoutException:
        pass
    except Exception as e:
        print(f"[COOKIES] Error: {e}")


# =========================== Utilities ===========================
FIRST_DIGIT = re.compile(r"\d")
NAME_PAIR = re.compile(
    r"[A-Z][A-Za-z''\-]+,\s*(?:[A-Z](?:\.)?)(?:\s*[A-Z](?:\.)?)*", flags=re.UNICODE
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


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"[^\w\s\-']", " ", s, flags=re.UNICODE).strip().lower()
    return SPACE.sub(" ", s)


def _is_person_profile_url(href: str) -> bool:
    """Accept only /en/persons/<slug> (reject directory / search / empty)."""
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


# =========================== LISTING (Stage 1) ===========================
def scrape_listing_page(driver, page_idx: int) -> List[Dict]:
    url = f"{BASE_URL}?page={page_idx}"
    safe_get(driver, url, f"listing-page-{page_idx+1}")
    
    if DEBUG_CAPTURE and page_idx == 0:
        _maybe_screenshot(driver, "listing-first")
        _maybe_dump_html(driver, "listing-first")
    
    accept_cookies_if_present(driver)
    
    # Wait for results to load
    try:
        WebDriverWait(driver, 15).until(
            lambda d: d.find_elements(By.CSS_SELECTOR, ".result-container h3.title a")
            or "No results" in d.page_source
        )
    except TimeoutException:
        print(f"[LISTING] Timeout waiting for results on page {page_idx+1}")
        pass
    
    rows = []
    for c in driver.find_elements(By.CLASS_NAME, "result-container"):
        try:
            a = c.find_element(By.CSS_SELECTOR, "h3.title a")
            title = a.text.strip()
            link = a.get_attribute("href")
            if title and link:
                rows.append({"title": title, "link": link})
        except Exception:
            continue
    
    return rows


def scrape_single_listing_page(
    page_idx: int, headless: bool = True, legacy_headless: bool = False
) -> List[Dict]:
    """Single page scraper for parallel execution"""
    driver = make_driver(headless, legacy_headless)
    try:
        return scrape_listing_page(driver, page_idx)
    finally:
        try:
            driver.quit()
        except Exception:
            pass


def gather_all_listing_links(
    max_pages: int,
    headless_listing: bool = False,
    legacy_headless: bool = False,
    list_workers: int = 2,  # Reduced default
) -> List[Dict]:
    """Collect listing links - SEQUENTIAL for session reuse"""
    print(
        f"[STAGE 1] Collecting links from {max_pages} pages sequentially (session reuse)..."
    )
    print(f"[STAGE 1] Running in {'headless' if headless_listing else 'visible'} mode")

    all_rows: List[Dict] = []
    
    # Use a SINGLE driver for all listing pages to reuse session/cookies
    driver = make_driver(headless_listing, legacy_headless)
    
    try:
        for page_idx in range(max_pages):
            try:
                print(f"[LIST] Scraping page {page_idx + 1}/{max_pages}...")
                rows = scrape_listing_page(driver, page_idx)
                
                if rows:
                    all_rows.extend(rows)
                    print(f"[LIST] Page {page_idx+1}/{max_pages} → {len(rows)} items")
                else:
                    print(f"[LIST] Page {page_idx+1}/{max_pages} → empty (may have reached end)")
                    # Don't break - might just be an empty page
                
                # Small delay between pages
                if page_idx < max_pages - 1:
                    delay = random.uniform(1, 2)
                    time.sleep(delay)
                    
            except Exception as e:
                print(f"[LIST] Page {page_idx+1} failed: {e}")
                # Continue with next page instead of stopping
                continue
    finally:
        try:
            driver.quit()
        except:
            pass

    uniq = {}
    for r in all_rows:
        uniq[r["link"]] = r
    return list(uniq.values())


# =========================== DETAIL (Stage 2) ===========================
def _maybe_expand_authors(driver):
    try:
        for b in driver.find_elements(
            By.XPATH,
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'show') or "
            "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'more')]",
        )[:2]:
            try:
                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", b
                )
                time.sleep(0.1)
                b.click()
                time.sleep(0.2)
            except Exception:
                continue
    except Exception:
        pass


def _authors_from_header_anchors(driver) -> List[Dict]:
    """
    Grab /en/persons/<slug> anchors ABOVE the tab bar (Overview etc.),
    reject directory link 'Profiles' and other nav chrome.
    """
    # Find Y threshold of tab bar
    tabs_y = None
    for xp in [
        "//a[normalize-space()='Overview']",
        "//nav[contains(@class,'tabbed-navigation')]",
        "//div[contains(@class,'navigation') and .//a[contains(.,'Overview')]]",
    ]:
        try:
            el = driver.find_element(By.XPATH, xp)
            tabs_y = el.location.get("y", None)
            if tabs_y:
                break
        except Exception:
            continue
    if tabs_y is None:
        tabs_y = 900

    candidates: List[Dict[str, Optional[str]]] = []
    seen = set()
    for a in driver.find_elements(By.CSS_SELECTOR, "a[href*='/en/persons/']"):
        try:
            y = a.location.get("y", 99999)
            if y >= tabs_y:
                continue
            href = (a.get_attribute("href") or "").strip()
            if not _is_person_profile_url(href):
                continue
            try:
                name = a.find_element(By.CSS_SELECTOR, "span").text.strip()
            except NoSuchElementException:
                name = (a.text or "").strip()
            if not _looks_like_person_name(name):
                continue
            key = (name, href)
            if key in seen:
                continue
            seen.add(key)
            candidates.append(
                {"name": name, "profile": urljoin(driver.current_url, href)}
            )
        except Exception:
            continue

    return _uniq_authors(candidates)


def _get_meta_list(driver, names_or_props: List[str]) -> List[str]:
    vals = []
    for nm in names_or_props:
        for el in driver.find_elements(
            By.CSS_SELECTOR, f'meta[name="{nm}"], meta[property="{nm}"]'
        ):
            c = (el.get_attribute("content") or "").strip()
            if c:
                vals.append(c)
    return _uniq_str(vals)


def _extract_authors_jsonld(driver) -> List[str]:
    import json as _json

    names = []
    for s in driver.find_elements(
        By.CSS_SELECTOR, 'script[type="application/ld+json"]'
    ):
        txt = (s.get_attribute("textContent") or "").strip()
        if not txt:
            continue
        try:
            data = _json.loads(txt)
        except Exception:
            continue
        objs = data if isinstance(data, list) else [data]
        for obj in objs:
            auth = obj.get("author")
            if not auth:
                continue
            if isinstance(auth, list):
                for a in auth:
                    n = a.get("name") if isinstance(a, dict) else str(a)
                    if n:
                        names.append(n)
            elif isinstance(auth, dict):
                n = auth.get("name")
                if n:
                    names.append(n)
            elif isinstance(auth, str):
                names.append(auth)
    return _uniq_str(names)


def _authors_from_subtitle_simple(driver, title_text: str) -> List[str]:
    """
    Use the subtitle line containing authors + date:
    strip title, cut before first digit (date), parse 'Surname, Initials' pairs.
    """
    try:
        date_el = driver.find_element(By.CSS_SELECTOR, "span.date")
    except NoSuchElementException:
        return []
    try:
        subtitle = date_el.find_element(
            By.XPATH, "ancestor::*[contains(@class,'subtitle')][1]"
        )
    except Exception:
        try:
            subtitle = date_el.find_element(By.XPATH, "..")
        except Exception:
            subtitle = None
    line = subtitle.text if subtitle else ""
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


def _authors_from_bs4(html: str, base_url: str) -> List[Dict]:
    soup = BeautifulSoup(html, "html.parser")
    candidates = []
    for a in soup.select("a[href*='/en/persons/']"):
        href = a.get("href") or ""
        name = a.get_text(strip=True)
        if not _is_person_profile_url(href):
            continue
        if not _looks_like_person_name(name):
            continue
        candidates.append({"name": name, "profile": urljoin(base_url, href)})
    return _uniq_authors(candidates)


def _abstract_from_bs4(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for sel in [
        "section#abstract .textblock",
        "div#abstract .textblock",
        "[data-section='abstract'] .textblock",
        ".abstract .textblock",
    ]:
        el = soup.select_one(sel)
        if el:
            txt = el.get_text(" ", strip=True)
            if len(txt) > 30:
                return txt
    return ""


def extract_detail_for_link(driver, link: str, title_hint: str) -> Dict:
    """Extract publication details with Cloudflare handling"""
    safe_get(driver, link, "detail")

    # Accept cookies
    accept_cookies_if_present(driver)

    # Wait for page to load
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
        )
    except TimeoutException:
        print("[DETAIL] Timeout waiting for h1")
        time.sleep(2)

    # Extract title
    try:
        title = driver.find_element(By.CSS_SELECTOR, "h1").text.strip()
    except NoSuchElementException:
        title = title_hint or ""

    # Expand author lists
    _maybe_expand_authors(driver)

    # AUTHORS: Try main methods efficiently
    author_objs: List[Dict[str, Optional[str]]] = []

    # Method 1: Header anchors (most reliable)
    try:
        author_objs = _authors_from_header_anchors(driver)
        author_objs = [
            a
            for a in author_objs
            if _looks_like_person_name(a.get("name", ""))
            and _is_person_profile_url(a.get("profile", ""))
        ]
    except:
        pass

    # Method 2: If no authors found, try subtitle quickly
    if not author_objs:
        try:
            names = _authors_from_subtitle_simple(driver, title)
            author_objs = _wrap_names_as_objs(names)
        except:
            pass

    # Method 3: Quick meta check if still no authors
    if not author_objs:
        try:
            names = _get_meta_list(driver, ["citation_author"])
            author_objs = _wrap_names_as_objs(names)
        except:
            pass
    if not author_objs:
        try:
            author_objs = _authors_from_bs4(driver.page_source, driver.current_url)
        except Exception:
            pass

    # FAST DATE EXTRACTION with fallback
    published_date = None
    for sel in ["span.date", "time[datetime]", "time"]:
        try:
            el = driver.find_element(By.CSS_SELECTOR, sel)
            published_date = el.get_attribute("datetime") or el.text.strip()
            if published_date:
                break
        except:
            continue

    # ABSTRACT EXTRACTION
    abstract_txt = ""

    # Method 1: Try standard abstract selectors
    abstract_selectors = [
        "section#abstract .textblock",
        "section.abstract .textblock",
        "div.abstract .textblock",
        "div#abstract .textblock",
        "section#abstract",
        "div#abstract",
        "[data-section='abstract'] .textblock",
        ".abstract .textblock",
        ".abstract p",
        ".abstract div",
        "div.textblock",
    ]

    for sel in abstract_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, sel)
            for el in elements:
                txt = el.text.strip()
                if len(txt) > 30:
                    abstract_txt = txt
                    break
            if abstract_txt:
                break
        except:
            continue

    # Method 2: Look for heading with "Abstract"
    if not abstract_txt:
        try:
            abstract_headings = driver.find_elements(
                By.XPATH,
                "//h1[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'abstract')] | //h2[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'abstract')] | //h3[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'abstract')] | //h4[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'abstract')]",
            )

            for h in abstract_headings:
                for xpath in [
                    "./following-sibling::div[1]",
                    "./following-sibling::p[1]",
                    "./following-sibling::section[1]",
                    "./following-sibling::*[1]",
                    "../following-sibling::div[1]",
                    "./parent::*/following-sibling::div[1]",
                ]:
                    try:
                        next_el = h.find_element(By.XPATH, xpath)
                        txt = next_el.text.strip()
                        if len(txt) > 30:
                            abstract_txt = txt
                            break
                    except:
                        continue
                if abstract_txt:
                    break
        except:
            pass

    # Method 3: Meta tags
    if not abstract_txt:
        try:
            meta_selectors = [
                'meta[name="description"]',
                'meta[name="abstract"]',
                'meta[property="og:description"]',
                'meta[name="citation_abstract"]',
            ]
            for sel in meta_selectors:
                try:
                    meta = driver.find_element(By.CSS_SELECTOR, sel)
                    content = meta.get_attribute("content")
                    if content and len(content.strip()) > 30:
                        abstract_txt = content.strip()
                        break
                except:
                    continue
        except:
            pass
    if not abstract_txt:
        try:
            abstract_txt = _abstract_from_bs4(driver.page_source)
        except Exception:
            pass

    return {
        "title": title,
        "link": link,
        "authors": _uniq_authors(author_objs),
        "published_date": published_date,
        "abstract": abstract_txt,
    }


# =========================== Workers ===========================
def worker_detail_batch(
    batch: List[Dict], headless: bool, legacy_headless: bool, worker_id: int = 0
) -> List[Dict]:
    """Process a batch of detail pages with a single driver (session reuse)"""
    driver = make_driver(headless=headless, legacy_headless=legacy_headless)
    out: List[Dict] = []
    try:
        for i, it in enumerate(batch, 1):
            try:
                print(f"[WORKER-{worker_id}] Processing {i}/{len(batch)}: {it.get('title', '')[:50]}")
                rec = extract_detail_for_link(driver, it["link"], it.get("title", ""))
                out.append(rec)
                
                # Small delay between items (session is already warmed up)
                if i < len(batch):
                    delay = random.uniform(1, 2)
                    time.sleep(delay)
                    
            except Exception as e:
                print(f"[WORKER-{worker_id}] ERR {it['link']}: {str(e)[:100]}")
                # Add minimal record to avoid data loss
                out.append(
                    {
                        "title": it.get("title", ""),
                        "link": it["link"],
                        "authors": [],
                        "published_date": None,
                        "abstract": "",
                    }
                )
                continue
    finally:
        try:
            driver.quit()
        except Exception:
            pass
    return out


def chunk(items: List[Dict], n: int) -> List[List[Dict]]:
    """Create chunks for parallel processing"""
    if n <= 1:
        return [items]
    # Create smaller chunks for better parallelism
    size = max(2, ceil(len(items) / (n * 2)))
    return [items[i : i + size] for i in range(0, len(items), size)]


# =========================== Orchestrator ===========================
def main():
    global PORTAL_ROOT, BASE_URL, RETRIES, RETRY_DELAY, CRAWL_DELAY, SCREENSHOT_DIR, DEBUG_CAPTURE
    
    ap = argparse.ArgumentParser(
        description="Cloudflare-resistant Coventry PurePortal scraper with undetected-chromedriver"
    )
    ap.add_argument("--outdir", default="../data", help="Output directory for JSON files")
    ap.add_argument(
        "--portal-root",
        default=DEFAULT_PORTAL_ROOT,
        help="Base portal root (env: PORTAL_ROOT).",
    )
    ap.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help="Listing base URL (env: BASE_URL).",
    )
    ap.add_argument(
        "--max-pages", type=int, default=10, help="Max listing pages to scan (reduced default for safety)"
    )
    ap.add_argument(
        "--workers",
        type=int,
        default=3,
        help="Parallel headless browsers for detail pages (reduced for Cloudflare)",
    )
    ap.add_argument(
        "--list-workers",
        type=int,
        default=2,
        help="Parallel workers for listing pages (reduced for Cloudflare)",
    )
    ap.add_argument(
        "--listing-headless", action="store_true", help="Run listing in headless mode (not recommended initially)"
    )
    ap.add_argument(
        "--legacy-headless", action="store_true", help="Use legacy --headless flag"
    )
    ap.add_argument(
        "--retries",
        type=int,
        default=RETRIES,
        help="Retries for page loads (env: CRAWLER_RETRIES)",
    )
    ap.add_argument(
        "--retry-delay",
        type=float,
        default=RETRY_DELAY,
        help="Base delay between retries in seconds (env: CRAWLER_RETRY_DELAY)",
    )
    ap.add_argument(
        "--crawl-delay",
        type=float,
        default=CRAWL_DELAY,
        help="Polite crawl delay between requests (env: CRAWLER_DELAY)",
    )
    ap.add_argument(
        "--screenshot-dir",
        default=None,
        help="Save screenshots/HTML on failures to this directory (useful for debugging)",
    )
    ap.add_argument(
        "--debug-capture",
        action="store_true",
        help="Always save first listing page HTML + screenshot",
    )
    ap.add_argument(
        "--use-regular-selenium",
        action="store_true",
        help="Force use of regular Selenium instead of undetected-chromedriver (for Mac compatibility)",
    )
    ap.add_argument(
        "--rebuild-index",
        action="store_true",
        help="Rebuild inverted index after crawling",
    )
    
    args = ap.parse_args()
    
    # Force regular Selenium if requested
    if args.use_regular_selenium:
        global USE_UNDETECTED
        USE_UNDETECTED = False
        print("[INFO] Forcing regular Selenium mode (--use-regular-selenium)")
    
    # Update globals
    PORTAL_ROOT = args.portal_root
    BASE_URL = args.base_url
    RETRIES = max(0, args.retries)
    RETRY_DELAY = max(0.1, args.retry_delay)
    CRAWL_DELAY = max(0.0, args.crawl_delay)
    SCREENSHOT_DIR = args.screenshot_dir
    DEBUG_CAPTURE = args.debug_capture
    
    # Validate worker counts
    if args.list_workers > args.max_pages:
        args.list_workers = max(1, args.max_pages)
    
    # Warn about aggressive settings
    if args.workers > 5:
        print(f"[WARNING] Using {args.workers} workers may trigger Cloudflare. Consider --workers 3")
    if args.list_workers > 3:
        print(f"[WARNING] Using {args.list_workers} list workers may trigger Cloudflare. Consider --list-workers 2")
    
    # Check for undetected-chromedriver
    if not USE_UNDETECTED:
        print("[WARNING] Running without undetected-chromedriver - high risk of Cloudflare blocks")
        print("[WARNING] Install with: pip install undetected-chromedriver")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Exiting. Please install undetected-chromedriver first.")
            return

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    start_time = time.time()
    
    print("\n" + "="*60)
    print("CLOUDFLARE-RESISTANT WEB SCRAPER")
    print("="*60)
    print(f"Mode: {'Undetected ChromeDriver' if USE_UNDETECTED else 'Regular Selenium (RISKY)'}")
    print(f"Workers: {args.workers} detail, {args.list_workers} listing")
    print(f"Max pages: {args.max_pages}")
    print(f"Headless listing: {args.listing_headless}")
    print(f"Output: {outdir}")
    print("="*60 + "\n")

    # -------- Stage 1: Listing collection
    print(f"[STAGE 1] Collecting publication links...")
    listing = gather_all_listing_links(
        args.max_pages,
        headless_listing=args.listing_headless,
        legacy_headless=args.legacy_headless,
        list_workers=args.list_workers,
    )
    stage1_time = time.time() - start_time
    print(f"[STAGE 1] ✓ Collected {len(listing)} unique links in {stage1_time:.1f}s")

    if not listing:
        print("[ERROR] No publications found. Possible Cloudflare block. Try:")
        print("  1. Run without --listing-headless flag")
        print("  2. Install undetected-chromedriver: pip install undetected-chromedriver")
        print("  3. Reduce workers: --list-workers 1")
        print("  4. Check screenshots if --screenshot-dir was set")
        return

    # Save listing
    (outdir / "publications_links.json").write_text(
        json.dumps(listing, indent=2), encoding="utf-8"
    )
    print(f"[STAGE 1] Saved links to {outdir}/publications_links.json\n")

    # -------- Stage 2: Detail scraping
    detail_workers = max(1, min(args.workers, len(listing)))
    print(f"[STAGE 2] Scraping {len(listing)} publication details...")
    print(f"[STAGE 2] Using {detail_workers} parallel workers (each reuses session)")
    
    stage2_start = time.time()
    batches = chunk(listing, detail_workers)
    results: List[Dict] = []
    
    with ThreadPoolExecutor(max_workers=detail_workers) as ex:
        futs = [
            ex.submit(worker_detail_batch, batch, True, args.legacy_headless, idx)
            for idx, batch in enumerate(batches)
        ]
        done = 0
        for fut in as_completed(futs):
            part = fut.result() or []
            results.extend(part)
            done += 1
            print(
                f"[STAGE 2] ✓ Completed {done}/{len(batches)} batches (+{len(part)} items)"
            )

    stage2_time = time.time() - stage2_start
    total_time = time.time() - start_time

    # -------- Merge and save final results
    by_link: Dict[str, Dict] = {}
    for it in listing:
        by_link[it["link"]] = {"title": it["title"], "link": it["link"]}
    for rec in results:
        by_link[rec["link"]] = rec

    final_rows = list(by_link.values())
    out_path = outdir / "publications.json"
    out_path.write_text(
        json.dumps(final_rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Performance summary
    print(f"\n{'='*60}")
    print(f"[PERFORMANCE SUMMARY]")
    print(f"{'='*60}")
    print(f"Total items processed: {len(final_rows)}")
    print(f"Stage 1 (listing): {stage1_time:.1f}s")
    print(f"Stage 2 (details): {stage2_time:.1f}s")
    print(f"Total time: {total_time:.1f}s")
    print(f"Average time per item: {total_time/len(final_rows):.2f}s")
    print(f"Items per minute: {(len(final_rows) * 60 / total_time):.1f}")
    
    # Calculate success rate
    successful = sum(1 for r in final_rows if r.get('authors') or r.get('abstract'))
    success_rate = (successful / len(final_rows) * 100) if final_rows else 0
    print(f"Success rate: {success_rate:.1f}% ({successful}/{len(final_rows)} with data)")
    
    print(f"\n[DONE] ✓ Saved {len(final_rows)} records → {out_path}")

    if args.rebuild_index:
        indexer_path = Path(__file__).resolve().parents[1] / "backend" / "indexer.py"
        if indexer_path.exists():
            print("[INDEX] Rebuilding inverted index...")
            try:
                subprocess.run(
                    [
                        sys.executable,
                        str(indexer_path),
                        "--data-dir",
                        str(outdir),
                    ],
                    check=False,
                )
            except Exception as e:
                print(f"[INDEX] Failed to rebuild index: {e}")
        else:
            print("[INDEX] indexer.py not found; skipping index rebuild.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()


# def _maybe_screenshot(driver, label: str):
#     if not SCREENSHOT_DIR:
#         return
#     try:
#         Path(SCREENSHOT_DIR).mkdir(parents=True, exist_ok=True)
#         ts = int(time.time())
#         out = Path(SCREENSHOT_DIR) / f"{label}-{ts}.png"
#         driver.save_screenshot(str(out))
#         print(f"[SCREENSHOT] Saved to {out}")
#     except Exception as e:
#         print(f"[SCREENSHOT] Failed: {e}")


# def _maybe_dump_html(driver, label: str):
#     if not SCREENSHOT_DIR:
#         return
#     try:
#         Path(SCREENSHOT_DIR).mkdir(parents=True, exist_ok=True)
#         ts = int(time.time())
#         out = Path(SCREENSHOT_DIR) / f"{label}-{ts}.html"
#         out.write_text(driver.page_source, encoding="utf-8")
#         print(f"[HTML] Saved to {out}")
#     except Exception as e:
#         print(f"[HTML] Failed: {e}")


# def wait_for_cloudflare(driver, timeout: int = 30) -> bool:
#     """Wait for Cloudflare challenge to complete - including manual checkbox"""
#     try:
#         print("[CLOUDFLARE] Checking for challenge...")
#         start = time.time()
        
#         while time.time() - start < timeout:
#             page_source = driver.page_source.lower()
#             page_title = driver.title.lower()
            
#             # Check if we're past Cloudflare
#             if "cloudflare" not in page_source and "cloudflare" not in page_title:
#                 print("[CLOUDFLARE] No challenge detected - page loaded!")
#                 return True
            
#             # Check for challenge elements
#             try:
#                 # Look for the verification checkbox/button
#                 challenge_frame = driver.find_elements(By.TAG_NAME, "iframe")
#                 if challenge_frame:
#                     print("[CLOUDFLARE] ⚠️  MANUAL ACTION REQUIRED!")
#                     print("[CLOUDFLARE] Please click 'Verify you are human' checkbox in the browser window")
#                     print(f"[CLOUDFLARE] Waiting... ({int(time.time() - start)}s / {timeout}s)")
#                     time.sleep(3)
#                     continue
                    
#                 # Check for challenge form
#                 challenge = driver.find_elements(By.ID, "challenge-form")
#                 if challenge:
#                     print(f"[CLOUDFLARE] Challenge form detected, waiting... ({int(time.time() - start)}s)")
#                     time.sleep(2)
#                     continue
                
#                 # Check if challenge text is present but no interactive elements
#                 if "just a moment" in page_source or "checking your browser" in page_source:
#                     print(f"[CLOUDFLARE] Auto-challenge in progress... ({int(time.time() - start)}s)")
#                     time.sleep(2)
#                     continue
                    
#                 # If we get here, might be past the challenge
#                 print("[CLOUDFLARE] Challenge appears complete!")
#                 time.sleep(1)  # Give it a moment to fully load
#                 return True
                
#             except Exception as e:
#                 # No challenge elements found
#                 print("[CLOUDFLARE] Challenge cleared!")
#                 return True
        
#         print(f"[CLOUDFLARE] ⏱️  Timeout after {timeout}s")
#         return False
        
#     except Exception as e:
#         print(f"[CLOUDFLARE] Error: {e}")
#         return False


# def safe_get(driver, url: str, label: str):
#     """Enhanced safe_get with Cloudflare handling and retries"""
#     last_exc = None
    
#     for attempt in range(RETRIES + 1):
#         try:
#             # Random delay before request (human-like behavior)
#             delay = random.uniform(2, 4) if attempt == 0 else random.uniform(3, 6)
#             print(f"[{label}] Waiting {delay:.1f}s before request (attempt {attempt + 1}/{RETRIES + 1})")
#             time.sleep(delay)
            
#             # Load page
#             print(f"[{label}] Loading: {url}")
#             driver.get(url)
            
#             # Additional wait for page to settle
#             time.sleep(random.uniform(2, 4))
            
#             # Check for Cloudflare challenge
#             page_source = driver.page_source.lower()
#             page_title = driver.title.lower()
            
#             if "cloudflare" in page_source or "cloudflare" in page_title or "just a moment" in page_source:
#                 _maybe_screenshot(driver, f"{label}-cloudflare-{attempt}")
#                 if not wait_for_cloudflare(driver, timeout=45):  # Increased timeout for manual action
#                     raise Exception("Cloudflare challenge not completed")
            
#             # Verify we got actual content
#             if len(driver.page_source) < 1000:
#                 raise Exception("Page content too short, possible blocking")
            
#             # Additional check - make sure we're on the right page
#             if "pureportal.coventry.ac.uk" not in driver.current_url:
#                 raise Exception(f"Unexpected redirect to: {driver.current_url}")
            
#             print(f"[{label}] ✓ Page loaded successfully")
#             return
            
#         except Exception as exc:
#             last_exc = exc
#             print(f"[{label}] ❌ Attempt {attempt + 1} failed: {str(exc)[:100]}")
#             _maybe_screenshot(driver, f"{label}-error-attempt{attempt+1}")
#             _maybe_dump_html(driver, f"{label}-error-attempt{attempt+1}")
            
#             if attempt < RETRIES:
#                 backoff = RETRY_DELAY * (attempt + 1) * random.uniform(1.5, 2.5)
#                 print(f"[{label}] Retrying in {backoff:.1f}s...")
#                 time.sleep(backoff)
    
#     if last_exc:
#         raise last_exc


# def accept_cookies_if_present(driver):
#     """Accept cookie consent if present"""
#     try:
#         btn = WebDriverWait(driver, 5).until(
#             EC.presence_of_element_located((By.ID, "onetrust-accept-btn-handler"))
#         )
#         driver.execute_script("arguments[0].click();", btn)
#         print("[COOKIES] Accepted")
#         time.sleep(0.5)
#     except TimeoutException:
#         pass
#     except Exception as e:
#         print(f"[COOKIES] Error: {e}")


# # =========================== Utilities ===========================
# FIRST_DIGIT = re.compile(r"\d")
# NAME_PAIR = re.compile(
#     r"[A-Z][A-Za-z''\-]+,\s*(?:[A-Z](?:\.)?)(?:\s*[A-Z](?:\.)?)*", flags=re.UNICODE
# )
# SPACE = re.compile(r"\s+")


# def _uniq_str(seq: List[str]) -> List[str]:
#     seen, out = set(), []
#     for x in seq:
#         x = x.strip()
#         if x and x not in seen:
#             seen.add(x)
#             out.append(x)
#     return out


# def _uniq_authors(
#     objs: List[Dict[str, Optional[str]]],
# ) -> List[Dict[str, Optional[str]]]:
#     seen: set[Tuple[str, str]] = set()
#     out: List[Dict[str, Optional[str]]] = []
#     for o in objs:
#         name = (o.get("name") or "").strip()
#         profile = (o.get("profile") or "").strip()
#         key = (name, profile)
#         if name and key not in seen:
#             seen.add(key)
#             out.append({"name": name, "profile": profile or None})
#     return out


# def _norm(s: str) -> str:
#     s = unicodedata.normalize("NFKD", s)
#     s = "".join(ch for ch in s if not unicodedata.combining(ch))
#     s = re.sub(r"[^\w\s\-']", " ", s, flags=re.UNICODE).strip().lower()
#     return SPACE.sub(" ", s)


# def _is_person_profile_url(href: str) -> bool:
#     """Accept only /en/persons/<slug> (reject directory / search / empty)."""
#     if not href:
#         return False
#     try:
#         u = urlparse(href)
#     except Exception:
#         return False
#     if u.netloc and "coventry.ac.uk" not in u.netloc:
#         return False
#     path = (u.path or "").rstrip("/")
#     if not path.startswith(PERSONS_PREFIX):
#         return False
#     slug = path[len(PERSONS_PREFIX) :].strip("/")
#     if not slug or slug.startswith("?"):
#         return False
#     return True


# def _looks_like_person_name(text: str) -> bool:
#     if not text:
#         return False
#     t = text.strip()
#     bad = {"profiles", "persons", "people", "overview"}
#     if t.lower() in bad:
#         return False
#     return ((" " in t) or ("," in t)) and sum(ch.isalpha() for ch in t) >= 4


# # =========================== LISTING (Stage 1) ===========================
# def scrape_listing_page(driver, page_idx: int) -> List[Dict]:
#     url = f"{BASE_URL}?page={page_idx}"
#     safe_get(driver, url, f"listing-page-{page_idx+1}")
    
#     if DEBUG_CAPTURE and page_idx == 0:
#         _maybe_screenshot(driver, "listing-first")
#         _maybe_dump_html(driver, "listing-first")
    
#     accept_cookies_if_present(driver)
    
#     # Wait for results to load
#     try:
#         WebDriverWait(driver, 15).until(
#             lambda d: d.find_elements(By.CSS_SELECTOR, ".result-container h3.title a")
#             or "No results" in d.page_source
#         )
#     except TimeoutException:
#         print(f"[LISTING] Timeout waiting for results on page {page_idx+1}")
#         pass
    
#     rows = []
#     for c in driver.find_elements(By.CLASS_NAME, "result-container"):
#         try:
#             a = c.find_element(By.CSS_SELECTOR, "h3.title a")
#             title = a.text.strip()
#             link = a.get_attribute("href")
#             if title and link:
#                 rows.append({"title": title, "link": link})
#         except Exception:
#             continue
    
#     return rows


# def scrape_single_listing_page(
#     page_idx: int, headless: bool = True, legacy_headless: bool = False
# ) -> List[Dict]:
#     """Single page scraper for parallel execution"""
#     driver = make_driver(headless, legacy_headless)
#     try:
#         return scrape_listing_page(driver, page_idx)
#     finally:
#         try:
#             driver.quit()
#         except Exception:
#             pass


# def gather_all_listing_links(
#     max_pages: int,
#     headless_listing: bool = False,
#     legacy_headless: bool = False,
#     list_workers: int = 2,  # Reduced default
# ) -> List[Dict]:
#     """Collect listing links with reduced parallelism"""
#     print(
#         f"[STAGE 1] Collecting links from {max_pages} pages with {list_workers} workers..."
#     )
#     print(f"[STAGE 1] Running in {'headless' if headless_listing else 'visible'} mode")

#     all_rows: List[Dict] = []

#     # Use parallel processing for listing pages
#     with ThreadPoolExecutor(max_workers=list_workers) as executor:
#         future_to_page = {
#             executor.submit(
#                 scrape_single_listing_page, i, headless_listing, legacy_headless
#             ): i
#             for i in range(max_pages)
#         }

#         completed = 0
#         for future in as_completed(future_to_page):
#             page_idx = future_to_page[future]
#             try:
#                 rows = future.result()
#                 if rows:
#                     all_rows.extend(rows)
#                     print(f"[LIST] Page {page_idx+1}/{max_pages} → {len(rows)} items")
#                 else:
#                     print(f"[LIST] Page {page_idx+1}/{max_pages} → empty")
#                 completed += 1
#             except Exception as e:
#                 print(f"[LIST] Page {page_idx+1} failed: {e}")

#     uniq = {}
#     for r in all_rows:
#         uniq[r["link"]] = r
#     return list(uniq.values())


# # =========================== DETAIL (Stage 2) ===========================
# def _maybe_expand_authors(driver):
#     try:
#         for b in driver.find_elements(
#             By.XPATH,
#             "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'show') or "
#             "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'more')]",
#         )[:2]:
#             try:
#                 driver.execute_script(
#                     "arguments[0].scrollIntoView({block:'center'});", b
#                 )
#                 time.sleep(0.1)
#                 b.click()
#                 time.sleep(0.2)
#             except Exception:
#                 continue
#     except Exception:
#         pass


# def _authors_from_header_anchors(driver) -> List[Dict]:
#     """
#     Grab /en/persons/<slug> anchors ABOVE the tab bar (Overview etc.),
#     reject directory link 'Profiles' and other nav chrome.
#     """
#     # Find Y threshold of tab bar
#     tabs_y = None
#     for xp in [
#         "//a[normalize-space()='Overview']",
#         "//nav[contains(@class,'tabbed-navigation')]",
#         "//div[contains(@class,'navigation') and .//a[contains(.,'Overview')]]",
#     ]:
#         try:
#             el = driver.find_element(By.XPATH, xp)
#             tabs_y = el.location.get("y", None)
#             if tabs_y:
#                 break
#         except Exception:
#             continue
#     if tabs_y is None:
#         tabs_y = 900

#     candidates: List[Dict[str, Optional[str]]] = []
#     seen = set()
#     for a in driver.find_elements(By.CSS_SELECTOR, "a[href*='/en/persons/']"):
#         try:
#             y = a.location.get("y", 99999)
#             if y >= tabs_y:
#                 continue
#             href = (a.get_attribute("href") or "").strip()
#             if not _is_person_profile_url(href):
#                 continue
#             try:
#                 name = a.find_element(By.CSS_SELECTOR, "span").text.strip()
#             except NoSuchElementException:
#                 name = (a.text or "").strip()
#             if not _looks_like_person_name(name):
#                 continue
#             key = (name, href)
#             if key in seen:
#                 continue
#             seen.add(key)
#             candidates.append(
#                 {"name": name, "profile": urljoin(driver.current_url, href)}
#             )
#         except Exception:
#             continue

#     return _uniq_authors(candidates)


# def _get_meta_list(driver, names_or_props: List[str]) -> List[str]:
#     vals = []
#     for nm in names_or_props:
#         for el in driver.find_elements(
#             By.CSS_SELECTOR, f'meta[name="{nm}"], meta[property="{nm}"]'
#         ):
#             c = (el.get_attribute("content") or "").strip()
#             if c:
#                 vals.append(c)
#     return _uniq_str(vals)


# def _extract_authors_jsonld(driver) -> List[str]:
#     import json as _json

#     names = []
#     for s in driver.find_elements(
#         By.CSS_SELECTOR, 'script[type="application/ld+json"]'
#     ):
#         txt = (s.get_attribute("textContent") or "").strip()
#         if not txt:
#             continue
#         try:
#             data = _json.loads(txt)
#         except Exception:
#             continue
#         objs = data if isinstance(data, list) else [data]
#         for obj in objs:
#             auth = obj.get("author")
#             if not auth:
#                 continue
#             if isinstance(auth, list):
#                 for a in auth:
#                     n = a.get("name") if isinstance(a, dict) else str(a)
#                     if n:
#                         names.append(n)
#             elif isinstance(auth, dict):
#                 n = auth.get("name")
#                 if n:
#                     names.append(n)
#             elif isinstance(auth, str):
#                 names.append(auth)
#     return _uniq_str(names)


# def _authors_from_subtitle_simple(driver, title_text: str) -> List[str]:
#     """
#     Use the subtitle line containing authors + date:
#     strip title, cut before first digit (date), parse 'Surname, Initials' pairs.
#     """
#     try:
#         date_el = driver.find_element(By.CSS_SELECTOR, "span.date")
#     except NoSuchElementException:
#         return []
#     try:
#         subtitle = date_el.find_element(
#             By.XPATH, "ancestor::*[contains(@class,'subtitle')][1]"
#         )
#     except Exception:
#         try:
#             subtitle = date_el.find_element(By.XPATH, "..")
#         except Exception:
#             subtitle = None
#     line = subtitle.text if subtitle else ""
#     if title_text and title_text in line:
#         line = line.replace(title_text, "")
#     line = " ".join(line.split()).strip()
#     m = FIRST_DIGIT.search(line)
#     pre_date = line[: m.start()].strip(" -—–·•,;|") if m else line
#     pre_date = pre_date.replace(" & ", ", ").replace(" and ", ", ")
#     pairs = NAME_PAIR.findall(pre_date)
#     return _uniq_str(pairs)


# def _wrap_names_as_objs(names: List[str]) -> List[Dict]:
#     return _uniq_authors([{"name": n, "profile": None} for n in names])


# def extract_detail_for_link(driver, link: str, title_hint: str) -> Dict:
#     """Extract publication details with Cloudflare handling"""
#     safe_get(driver, link, "detail")

#     # Accept cookies
#     accept_cookies_if_present(driver)

#     # Wait for page to load
#     try:
#         WebDriverWait(driver, 10).until(
#             EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
#         )
#     except TimeoutException:
#         print("[DETAIL] Timeout waiting for h1")
#         time.sleep(2)

#     # Extract title
#     try:
#         title = driver.find_element(By.CSS_SELECTOR, "h1").text.strip()
#     except NoSuchElementException:
#         title = title_hint or ""

#     # Expand author lists
#     _maybe_expand_authors(driver)

#     # AUTHORS: Try main methods efficiently
#     author_objs: List[Dict[str, Optional[str]]] = []

#     # Method 1: Header anchors (most reliable)
#     try:
#         author_objs = _authors_from_header_anchors(driver)
#         author_objs = [
#             a
#             for a in author_objs
#             if _looks_like_person_name(a.get("name", ""))
#             and _is_person_profile_url(a.get("profile", ""))
#         ]
#     except:
#         pass

#     # Method 2: If no authors found, try subtitle quickly
#     if not author_objs:
#         try:
#             names = _authors_from_subtitle_simple(driver, title)
#             author_objs = _wrap_names_as_objs(names)
#         except:
#             pass

#     # Method 3: Quick meta check if still no authors
#     if not author_objs:
#         try:
#             names = _get_meta_list(driver, ["citation_author"])
#             author_objs = _wrap_names_as_objs(names)
#         except:
#             pass

#     # FAST DATE EXTRACTION with fallback
#     published_date = None
#     for sel in ["span.date", "time[datetime]", "time"]:
#         try:
#             el = driver.find_element(By.CSS_SELECTOR, sel)
#             published_date = el.get_attribute("datetime") or el.text.strip()
#             if published_date:
#                 break
#         except:
#             continue

#     # ABSTRACT EXTRACTION
#     abstract_txt = ""

#     # Method 1: Try standard abstract selectors
#     abstract_selectors = [
#         "section#abstract .textblock",
#         "section.abstract .textblock",
#         "div.abstract .textblock",
#         "div#abstract .textblock",
#         "section#abstract",
#         "div#abstract",
#         "[data-section='abstract'] .textblock",
#         ".abstract .textblock",
#         ".abstract p",
#         ".abstract div",
#         "div.textblock",
#     ]

#     for sel in abstract_selectors:
#         try:
#             elements = driver.find_elements(By.CSS_SELECTOR, sel)
#             for el in elements:
#                 txt = el.text.strip()
#                 if len(txt) > 30:
#                     abstract_txt = txt
#                     break
#             if abstract_txt:
#                 break
#         except:
#             continue

#     # Method 2: Look for heading with "Abstract"
#     if not abstract_txt:
#         try:
#             abstract_headings = driver.find_elements(
#                 By.XPATH,
#                 "//h1[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'abstract')] | //h2[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'abstract')] | //h3[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'abstract')] | //h4[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'abstract')]",
#             )

#             for h in abstract_headings:
#                 for xpath in [
#                     "./following-sibling::div[1]",
#                     "./following-sibling::p[1]",
#                     "./following-sibling::section[1]",
#                     "./following-sibling::*[1]",
#                     "../following-sibling::div[1]",
#                     "./parent::*/following-sibling::div[1]",
#                 ]:
#                     try:
#                         next_el = h.find_element(By.XPATH, xpath)
#                         txt = next_el.text.strip()
#                         if len(txt) > 30:
#                             abstract_txt = txt
#                             break
#                     except:
#                         continue
#                 if abstract_txt:
#                     break
#         except:
#             pass

#     # Method 3: Meta tags
#     if not abstract_txt:
#         try:
#             meta_selectors = [
#                 'meta[name="description"]',
#                 'meta[name="abstract"]',
#                 'meta[property="og:description"]',
#                 'meta[name="citation_abstract"]',
#             ]
#             for sel in meta_selectors:
#                 try:
#                     meta = driver.find_element(By.CSS_SELECTOR, sel)
#                     content = meta.get_attribute("content")
#                     if content and len(content.strip()) > 30:
#                         abstract_txt = content.strip()
#                         break
#                 except:
#                     continue
#         except:
#             pass

#     return {
#         "title": title,
#         "link": link,
#         "authors": _uniq_authors(author_objs),
#         "published_date": published_date,
#         "abstract": abstract_txt,
#     }


# # =========================== Workers ===========================
# def worker_detail_batch(
#     batch: List[Dict], headless: bool, legacy_headless: bool
# ) -> List[Dict]:
#     """Process a batch of detail pages"""
#     driver = make_driver(headless=headless, legacy_headless=legacy_headless)
#     out: List[Dict] = []
#     try:
#         for i, it in enumerate(batch, 1):
#             try:
#                 print(f"[WORKER] Processing {i}/{len(batch)}: {it.get('title', '')[:50]}")
#                 rec = extract_detail_for_link(driver, it["link"], it.get("title", ""))
#                 out.append(rec)
                
#                 # Random delay between items
#                 if i < len(batch):
#                     delay = random.uniform(2, 4)
#                     print(f"[WORKER] Waiting {delay:.1f}s before next item...")
#                     time.sleep(delay)
                    
#             except Exception as e:
#                 print(f"[WORKER] ERR {it['link']}: {str(e)[:100]}")
#                 # Add minimal record to avoid data loss
#                 out.append(
#                     {
#                         "title": it.get("title", ""),
#                         "link": it["link"],
#                         "authors": [],
#                         "published_date": None,
#                         "abstract": "",
#                     }
#                 )
#                 continue
#     finally:
#         try:
#             driver.quit()
#         except Exception:
#             pass
#     return out


# def chunk(items: List[Dict], n: int) -> List[List[Dict]]:
#     """Create chunks for parallel processing"""
#     if n <= 1:
#         return [items]
#     # Create smaller chunks for better parallelism
#     size = max(2, ceil(len(items) / (n * 2)))
#     return [items[i : i + size] for i in range(0, len(items), size)]


# # =========================== Orchestrator ===========================
# def main():
#     global PORTAL_ROOT, BASE_URL, RETRIES, RETRY_DELAY, SCREENSHOT_DIR, DEBUG_CAPTURE
    
#     ap = argparse.ArgumentParser(
#         description="Cloudflare-resistant Coventry PurePortal scraper with undetected-chromedriver"
#     )
#     ap.add_argument("--outdir", default="../data", help="Output directory for JSON files")
#     ap.add_argument(
#         "--portal-root",
#         default=DEFAULT_PORTAL_ROOT,
#         help="Base portal root (env: PORTAL_ROOT).",
#     )
#     ap.add_argument(
#         "--base-url",
#         default=DEFAULT_BASE_URL,
#         help="Listing base URL (env: BASE_URL).",
#     )
#     ap.add_argument(
#         "--max-pages", type=int, default=10, help="Max listing pages to scan (reduced default for safety)"
#     )
#     ap.add_argument(
#         "--workers",
#         type=int,
#         default=3,
#         help="Parallel headless browsers for detail pages (reduced for Cloudflare)",
#     )
#     ap.add_argument(
#         "--list-workers",
#         type=int,
#         default=2,
#         help="Parallel workers for listing pages (reduced for Cloudflare)",
#     )
#     ap.add_argument(
#         "--listing-headless", action="store_true", help="Run listing in headless mode (not recommended initially)"
#     )
#     ap.add_argument(
#         "--legacy-headless", action="store_true", help="Use legacy --headless flag"
#     )
#     ap.add_argument(
#         "--retries",
#         type=int,
#         default=RETRIES,
#         help="Retries for page loads (env: CRAWLER_RETRIES)",
#     )
#     ap.add_argument(
#         "--retry-delay",
#         type=float,
#         default=RETRY_DELAY,
#         help="Base delay between retries in seconds (env: CRAWLER_RETRY_DELAY)",
#     )
#     ap.add_argument(
#         "--screenshot-dir",
#         default=None,
#         help="Save screenshots/HTML on failures to this directory (useful for debugging)",
#     )
#     ap.add_argument(
#         "--debug-capture",
#         action="store_true",
#         help="Always save first listing page HTML + screenshot",
#     )
#     ap.add_argument(
#         "--use-regular-selenium",
#         action="store_true",
#         help="Force use of regular Selenium instead of undetected-chromedriver (for Mac compatibility)",
#     )
    
#     args = ap.parse_args()
    
#     # Force regular Selenium if requested
#     if args.use_regular_selenium:
#         global USE_UNDETECTED
#         USE_UNDETECTED = False
#         print("[INFO] Forcing regular Selenium mode (--use-regular-selenium)")
    
#     # Update globals
#     PORTAL_ROOT = args.portal_root
#     BASE_URL = args.base_url
#     RETRIES = max(0, args.retries)
#     RETRY_DELAY = max(0.1, args.retry_delay)
#     SCREENSHOT_DIR = args.screenshot_dir
#     DEBUG_CAPTURE = args.debug_capture
    
#     # Validate worker counts
#     if args.list_workers > args.max_pages:
#         args.list_workers = max(1, args.max_pages)
    
#     # Warn about aggressive settings
#     if args.workers > 5:
#         print(f"[WARNING] Using {args.workers} workers may trigger Cloudflare. Consider --workers 3")
#     if args.list_workers > 3:
#         print(f"[WARNING] Using {args.list_workers} list workers may trigger Cloudflare. Consider --list-workers 2")
    
#     # Check for undetected-chromedriver
#     if not USE_UNDETECTED:
#         print("[WARNING] Running without undetected-chromedriver - high risk of Cloudflare blocks")
#         print("[WARNING] Install with: pip install undetected-chromedriver")
#         response = input("Continue anyway? (y/N): ")
#         if response.lower() != 'y':
#             print("Exiting. Please install undetected-chromedriver first.")
#             return

#     outdir = Path(args.outdir)
#     outdir.mkdir(parents=True, exist_ok=True)

#     start_time = time.time()
    
#     print("\n" + "="*60)
#     print("CLOUDFLARE-RESISTANT WEB SCRAPER")
#     print("="*60)
#     print(f"Mode: {'Undetected ChromeDriver' if USE_UNDETECTED else 'Regular Selenium (RISKY)'}")
#     print(f"Workers: {args.workers} detail, {args.list_workers} listing")
#     print(f"Max pages: {args.max_pages}")
#     print(f"Headless listing: {args.listing_headless}")
#     print(f"Output: {outdir}")
#     print("="*60 + "\n")

#     # -------- Stage 1: Listing collection
#     print(f"[STAGE 1] Collecting publication links...")
#     listing = gather_all_listing_links(
#         args.max_pages,
#         headless_listing=args.listing_headless,
#         legacy_headless=args.legacy_headless,
#         list_workers=args.list_workers,
#     )
#     stage1_time = time.time() - start_time
#     print(f"[STAGE 1] ✓ Collected {len(listing)} unique links in {stage1_time:.1f}s")

#     if not listing:
#         print("[ERROR] No publications found. Possible Cloudflare block. Try:")
#         print("  1. Run without --listing-headless flag")
#         print("  2. Install undetected-chromedriver: pip install undetected-chromedriver")
#         print("  3. Reduce workers: --list-workers 1")
#         print("  4. Check screenshots if --screenshot-dir was set")
#         return

#     # Save listing
#     (outdir / "publications_links.json").write_text(
#         json.dumps(listing, indent=2), encoding="utf-8"
#     )
#     print(f"[STAGE 1] Saved links to {outdir}/publications_links.json\n")

#     # -------- Stage 2: Detail scraping
#     detail_workers = max(1, min(args.workers, len(listing)))
#     print(f"[STAGE 2] Scraping {len(listing)} publication details...")
#     print(f"[STAGE 2] Using {detail_workers} parallel workers (headless mode)")
    
#     stage2_start = time.time()
#     batches = chunk(listing, detail_workers)
#     results: List[Dict] = []
    
#     with ThreadPoolExecutor(max_workers=detail_workers) as ex:
#         futs = [
#             ex.submit(worker_detail_batch, batch, True, args.legacy_headless)
#             for batch in batches
#         ]
#         done = 0
#         for fut in as_completed(futs):
#             part = fut.result() or []
#             results.extend(part)
#             done += 1
#             print(
#                 f"[STAGE 2] ✓ Completed {done}/{len(batches)} batches (+{len(part)} items)"
#             )

#     stage2_time = time.time() - stage2_start
#     total_time = time.time() - start_time

#     # -------- Merge and save final results
#     by_link: Dict[str, Dict] = {}
#     for it in listing:
#         by_link[it["link"]] = {"title": it["title"], "link": it["link"]}
#     for rec in results:
#         by_link[rec["link"]] = rec

#     final_rows = list(by_link.values())
#     out_path = outdir / "publications.json"
#     out_path.write_text(
#         json.dumps(final_rows, ensure_ascii=False, indent=2), encoding="utf-8"
#     )

#     # Performance summary
#     print(f"\n{'='*60}")
#     print(f"[PERFORMANCE SUMMARY]")
#     print(f"{'='*60}")
#     print(f"Total items processed: {len(final_rows)}")
#     print(f"Stage 1 (listing): {stage1_time:.1f}s")
#     print(f"Stage 2 (details): {stage2_time:.1f}s")
#     print(f"Total time: {total_time:.1f}s")
#     print(f"Average time per item: {total_time/len(final_rows):.2f}s")
#     print(f"Items per minute: {(len(final_rows) * 60 / total_time):.1f}")
    
#     # Calculate success rate
#     successful = sum(1 for r in final_rows if r.get('authors') or r.get('abstract'))
#     success_rate = (successful / len(final_rows) * 100) if final_rows else 0
#     print(f"Success rate: {success_rate:.1f}% ({successful}/{len(final_rows)} with data)")
    
#     print(f"\n[DONE] ✓ Saved {len(final_rows)} records → {out_path}")
#     print(f"{'='*60}\n")


# if __name__ == "__main__":
#     main()
