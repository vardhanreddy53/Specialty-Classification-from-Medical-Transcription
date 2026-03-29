
import re
import csv
import json
import time
import logging
import argparse
from pathlib import Path

import requests
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm

# ─────────────────────────── Config ──────────────────────────────────────────

BASE_URL       = "https://www.mtsamples.com"
BROWSE_URL     = BASE_URL + "/site/pages/browse.asp"
SAMPLE_URL     = BASE_URL + "/site/pages/sample.asp"

OUTPUT_CSV     = "mtsamples_scraped.csv"
CHECKPOINT     = "scraper_checkpoint.json"
LOG_FILE       = "scraper.log"

DEFAULT_DELAY  = 1.0      # seconds between requests
MAX_RETRIES    = 3
TIMEOUT        = 15       # seconds per request

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# 40 specialties — (type_id, display_name)  extracted from mtsamples.com homepage
SPECIALTIES = [
    ("3",   "Allergy / Immunology"),
    ("94",  "Autopsy"),
    ("5",   "Bariatrics"),
    ("6",   "Cardiovascular / Pulmonary"),
    ("99",  "Chiropractic"),
    ("97",  "Consult - History and Phy."),
    ("70",  "Cosmetic / Plastic Surgery"),
    ("17",  "Dentistry"),
    ("18",  "Dermatology"),
    ("44",  "Diets and Nutritions"),
    ("89",  "Discharge Summary"),
    ("93",  "Emergency Room Reports"),
    ("21",  "Endocrinology"),
    ("100", "ENT - Otolaryngology"),
    ("24",  "Gastroenterology"),
    ("98",  "General Medicine"),
    ("96",  "Hematology - Oncology"),
    ("34",  "Hospice - Palliative Care"),
    ("90",  "IME-QME-Work Comp etc."),
    ("92",  "Lab Medicine - Pathology"),
    ("86",  "Letters"),
    ("41",  "Nephrology"),
    ("42",  "Neurology"),
    ("43",  "Neurosurgery"),
    ("45",  "Obstetrics / Gynecology"),
    ("87",  "Office Notes"),
    ("46",  "Ophthalmology"),
    ("49",  "Orthopedic"),
    ("105", "Pain Management"),
    ("66",  "Pediatrics - Neonatal"),
    ("68",  "Physical Medicine - Rehab"),
    ("71",  "Podiatry"),
    ("72",  "Psychiatry / Psychology"),
    ("95",  "Radiology"),
    ("77",  "Rheumatology"),
    ("78",  "Sleep Medicine"),
    ("91",  "SOAP / Chart / Progress Notes"),
    ("106", "Speech - Language"),
    ("85",  "Surgery"),
    ("82",  "Urology"),
]

# ─────────────────────────── Logging ─────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

# ─────────────────────────── HTTP helpers ────────────────────────────────────

session = requests.Session()
session.headers.update(HEADERS)


def fetch(url: str, retries: int = MAX_RETRIES, delay: float = DEFAULT_DELAY) -> BeautifulSoup | None:
    """
    GET a URL and return BeautifulSoup.
    Retries with exponential back-off; returns None on permanent failure.
    """
    for attempt in range(1, retries + 1):
        try:
            resp = session.get(url, timeout=TIMEOUT)
            resp.raise_for_status()
            time.sleep(delay)
            return BeautifulSoup(resp.text, "html.parser")
        except requests.HTTPError as e:
            log.warning(f"HTTP {e.response.status_code} on attempt {attempt}/{retries}: {url}")
            if e.response.status_code in (403, 404):
                return None          # don't retry client errors
        except requests.RequestException as e:
            log.warning(f"Request error attempt {attempt}/{retries}: {e} — {url}")

        if attempt < retries:
            wait = 2 ** attempt      # 2s, 4s, 8s …
            log.info(f"  Waiting {wait}s before retry…")
            time.sleep(wait)

    log.error(f"Giving up after {retries} attempts: {url}")
    return None


# ─────────────────────────── Checkpoint helpers ───────────────────────────────

def load_checkpoint() -> dict:
    if Path(CHECKPOINT).exists():
        with open(CHECKPOINT, encoding="utf-8") as f:
            return json.load(f)
    return {"done_specialties": [], "records": []}


def save_checkpoint(state: dict) -> None:
    with open(CHECKPOINT, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# ─────────────────────────── Scraper logic ───────────────────────────────────

def build_type_param(type_id: str, name: str) -> str:
    """e.g. '18-Dermatology'"""
    return f"{type_id}-{name}"


def get_sample_links(type_id: str, name: str, delay: float) -> list[dict]:
    """
    Fetch the browse page for one specialty.
    Returns a list of dicts: { sample_name, sample_param, description }

    Browse page URL  : /browse.asp?Type=18-Dermatology
    Each table row   : <a href="sample.asp?Type=18-Dermatology&Sample=288-Acne+%2D+SOAP">
                         Acne - SOAP
                       </a>
                       <br>Short description here.
    """
    type_param = build_type_param(type_id, name)
    url = f"{BROWSE_URL}?Type={requests.utils.quote(type_param, safe='')}"
    soup = fetch(url, delay=delay)
    if not soup:
        log.error(f"Failed to load browse page for {name}")
        return []

    results = []
    table = soup.find("table")
    if not table:
        log.warning(f"No table found on browse page for {name}")
        return []

    for row in table.find_all("tr"):
        a = row.find("a", href=True)
        if not a or "Sample=" not in a.get("href", ""):
            continue

        sample_name = a.get_text(strip=True)

        # Short description is the remaining text in the <td> after the link
        td = row.find("td")
        desc = ""
        if td:
            raw = td.get_text(" ", strip=True)
            desc = raw.replace(sample_name, "").strip().lstrip("-–— ").strip()

        # Extract the Sample=... value (URL-encoded) from the href
        m = re.search(r"[?&]Sample=([^&]+)", a["href"])
        if not m:
            continue
        sample_param = m.group(1)   # keep URL-encoding intact for later use

        results.append({
            "sample_name":  sample_name,
            "sample_param": sample_param,
            "type_param":   type_param,
            "description":  desc,
        })

    log.info(f"  {name}: found {len(results)} samples")
    return results


def parse_sample_page(soup: BeautifulSoup) -> dict:
    """
    Extract description, transcription, and keywords from a sample page.

    Page structure (verified from live HTML):
      <h2>Description: Acne with folliculitis. (Medical Transcription…)</h2>
      <hr>
      … transcription body …
      <hr>
      Keywords: dermatology, acne with folliculitis, …
    """
    # ── Description ──────────────────────────────────────────────────────────
    desc = ""
    h2 = soup.find("h2")
    if h2:
        raw = h2.get_text(" ", strip=True)
        # Strip leading "Description:" and trailing "(Medical Transcription…)"
        raw = re.sub(r"^\*{0,2}Description:\*{0,2}\s*", "", raw, flags=re.I)
        raw = re.sub(r"\s*\(Medical Transcription[^)]*\)\s*$", "", raw, flags=re.I)
        desc = raw.strip()

    # ── Transcription ─────────────────────────────────────────────────────────
    # Content sits between the first and second <hr> elements
    transcription = ""
    hrs = soup.find_all("hr")
    if len(hrs) >= 2:
        chunks = []
        node = hrs[0].next_sibling
        while node and node != hrs[1]:
            if hasattr(node, "get_text"):
                t = node.get_text(" ", strip=True)
                if t and not t.startswith("Educational Disclaimer"):
                    chunks.append(t)
            elif isinstance(node, str):
                t = node.strip()
                if t:
                    chunks.append(t)
            node = node.next_sibling
        transcription = "\n".join(chunks).strip()

    # Fallback — grab the largest <p> block if <hr> strategy fails
    if not transcription:
        paras = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
        paras = [p for p in paras if len(p) > 100]
        transcription = "\n".join(paras)

    # ── Keywords ──────────────────────────────────────────────────────────────
    keywords = ""
    # Look for bold "Keywords:" label
    kw_bold = soup.find(string=re.compile(r"^\s*Keywords\s*:?\s*$", re.I))
    if kw_bold and kw_bold.parent:
        # Keywords are often the next sibling text or in the same <p>/<td>
        parent = kw_bold.find_parent(["p", "td", "div"])
        if parent:
            full = parent.get_text(" ", strip=True)
            keywords = re.sub(r"^Keywords\s*:?\s*", "", full, flags=re.I).strip()
    else:
        # Fallback: find any element whose text starts with "Keywords:"
        for elem in soup.find_all(string=re.compile(r"Keywords\s*:", re.I)):
            raw = str(elem)
            keywords = re.sub(r"^.*?Keywords\s*:\s*", "", raw, flags=re.I).strip()
            keywords = BeautifulSoup(keywords, "html.parser").get_text(" ", strip=True)
            if keywords:
                break

    return {
        "description":   desc,
        "transcription": transcription,
        "keywords":      keywords,
    }


def scrape_sample(type_param: str, sample_param: str, delay: float) -> dict:
    """Fetch one sample page and parse it."""
    url = (
        f"{SAMPLE_URL}"
        f"?Type={requests.utils.quote(type_param, safe='')}"
        f"&Sample={sample_param}"
    )
    soup = fetch(url, delay=delay)
    if not soup:
        return {"description": "", "transcription": "", "keywords": ""}
    return parse_sample_page(soup)


# ─────────────────────────── Main ────────────────────────────────────────────

def main(args: argparse.Namespace) -> None:
    delay = args.delay

    # Filter to a single specialty if --specialty passed (for testing)
    specialties = SPECIALTIES
    if args.specialty:
        specialties = [(tid, name) for tid, name in SPECIALTIES if tid == str(args.specialty)]
        if not specialties:
            log.error(f"Unknown specialty id '{args.specialty}'. Check SPECIALTIES list.")
            return
        log.info(f"Single-specialty mode: {specialties[0][1]}")

    # Load checkpoint
    state = {"done_specialties": [], "records": []} if args.fresh else load_checkpoint()
    done = set(state["done_specialties"])
    records = state["records"]

    if done:
        log.info(f"Resuming — {len(done)} specialties already done, "
                 f"{len(records)} records already collected")

    # ── Main loop ─────────────────────────────────────────────────────────────
    for type_id, name in tqdm(specialties, desc="Specialties", unit="spec"):
        if name in done:
            continue

        log.info(f"\n{'─'*50}")
        log.info(f"Specialty: {name}  (id={type_id})")

        sample_links = get_sample_links(type_id, name, delay)
        if not sample_links:
            done.add(name)
            state["done_specialties"] = list(done)
            save_checkpoint(state)
            continue

        for s in tqdm(sample_links, desc=f"  {name[:30]}", leave=False, unit="sample"):
            detail = scrape_sample(s["type_param"], s["sample_param"], delay)

            # Prefer richer description from the sample page
            description = detail["description"] or s["description"]

            records.append({
                "description":       description,
                "medical_specialty": name,
                "sample_name":       s["sample_name"],
                "transcription":     detail["transcription"],
                "keywords":          detail["keywords"],
            })

        # Mark specialty complete and checkpoint
        done.add(name)
        state["done_specialties"] = list(done)
        state["records"] = records
        save_checkpoint(state)
        log.info(f"  ✓ {name} complete  (total records so far: {len(records)})")

    # ── Save final CSV ────────────────────────────────────────────────────────
    df = pd.DataFrame(records, columns=[
        "description", "medical_specialty", "sample_name",
        "transcription", "keywords",
    ])

    # ── Validation pass ───────────────────────────────────────────────────────
    empty_tx = df["transcription"].str.strip().eq("").sum()
    if empty_tx:
        log.warning(f"{empty_tx} rows have empty transcription — check scraper.log")

    df.to_csv(OUTPUT_CSV, index=False, quoting=csv.QUOTE_ALL, encoding="utf-8-sig")

    log.info(f"\n{'═'*50}")
    log.info(f"✅  Saved {len(df)} records → '{OUTPUT_CSV}'")
    log.info(f"   Empty transcriptions : {empty_tx}")
    log.info(f"   Specialties scraped  : {df['medical_specialty'].nunique()}")
    log.info("\nSamples per specialty:")
    log.info("\n" + df["medical_specialty"].value_counts().to_string())

    # Clean up checkpoint on successful full run
    if not args.specialty and Path(CHECKPOINT).exists():
        Path(CHECKPOINT).unlink()
        log.info("Checkpoint file removed.")


# ─────────────────────────── CLI ─────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MTSamples.com web scraper")
    parser.add_argument(
        "--delay", type=float, default=DEFAULT_DELAY,
        help=f"Seconds between requests (default: {DEFAULT_DELAY})"
    )
    parser.add_argument(
        "--fresh", action="store_true",
        help="Ignore existing checkpoint and start over"
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Resume from checkpoint (default behaviour)"
    )
    parser.add_argument(
        "--specialty", type=str, default=None,
        help="Scrape only one specialty by type_id (e.g. --specialty 18 for Dermatology)"
    )
    main(parser.parse_args())