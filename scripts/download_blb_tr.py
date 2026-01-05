#!/usr/bin/env python3
"""
Download the complete Stephanus 1550 Textus Receptus from Blue Letter Bible.
Outputs in the same format as tr_raw.csv: chapter,verse,text,book
"""

import requests
import re
import csv
import sys
import time
from pathlib import Path
from bs4 import BeautifulSoup

# Get project root (parent of scripts directory)
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent

sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils.config import load_config

# NT books with their BLB abbreviations and number of chapters
NT_BOOKS = [
    ("mat", "MAT", 28),
    ("mar", "MAR", 16),
    ("luk", "LUK", 24),
    ("jhn", "JHN", 21),
    ("act", "ACT", 28),
    ("rom", "ROM", 16),
    ("1co", "1CO", 16),
    ("2co", "2CO", 13),
    ("gal", "GAL", 6),
    ("eph", "EPH", 6),
    ("php", "PHP", 4),
    ("col", "COL", 4),
    ("1th", "1TH", 5),
    ("2th", "2TH", 3),
    ("1ti", "1TI", 6),
    ("2ti", "2TI", 4),
    ("tit", "TIT", 3),
    ("phm", "PHM", 1),
    ("heb", "HEB", 13),
    ("jas", "JAS", 5),
    ("1pe", "1PE", 5),
    ("2pe", "2PE", 3),
    ("1jn", "1JN", 5),
    ("2jn", "2JN", 1),
    ("3jn", "3JN", 1),
    ("jud", "JUD", 1),
    ("rev", "REV", 22),
]


def fetch_chapter(blb_book: str, chapter: int) -> str:
    """Fetch a chapter page from BLB."""
    url = f"https://www.blueletterbible.org/tr/{blb_book}/{chapter}/1/"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text


def extract_verses(html: str, book_code: str, chapter: int) -> list:
    """Extract verses from BLB HTML page."""
    soup = BeautifulSoup(html, "html.parser")
    verses = []

    # Find all verse divs - they have class "GkBibleText scriptureText"
    verse_divs = soup.find_all("div", class_="GkBibleText")

    for verse_div in verse_divs:
        # Get verse number from data-print-verse-prefix attribute
        verse_num = verse_div.get("data-print-verse-prefix")
        if not verse_num:
            continue

        try:
            verse_num = int(verse_num)
        except ValueError:
            continue

        # Get all word-phrase spans
        word_spans = verse_div.find_all("span", class_="word-phrase")
        words = []

        for span in word_spans:
            # Get the text content (first text node, before the <sup> tag)
            text = ""
            for content in span.contents:
                if isinstance(content, str):
                    text = content.strip()
                    break
                elif content.name != "sup":
                    text = content.get_text(strip=True)
                    break

            if not text:
                # Fallback: get all text and remove Strong's references
                text = span.get_text(strip=True)
                # Remove Strong's numbers like G1234
                text = re.sub(r'\s*G\d+', '', text)

            if text:
                words.append(text)

        if words:
            # Join words with spaces
            verse_text = " ".join(words)
            verses.append({
                "chapter": chapter,
                "verse": verse_num,
                "text": verse_text,
                "book": book_code
            })

    return verses


def download_all():
    """Download all NT books from BLB."""
    config = load_config()
    source_dir = Path(config["paths"]["data"]["source"])
    output_path = source_dir / "tr_blb.csv"
    all_verses = []

    total_chapters = sum(c[2] for c in NT_BOOKS)
    completed_chapters = 0

    for blb_book, book_code, num_chapters in NT_BOOKS:
        print(f"\n{book_code}:")
        book_verses = []

        for chapter in range(1, num_chapters + 1):
            completed_chapters += 1
            progress = completed_chapters / total_chapters * 100
            print(f"  Ch {chapter:2d}/{num_chapters} ({progress:5.1f}% total)", end="\r")

            try:
                html = fetch_chapter(blb_book, chapter)
                verses = extract_verses(html, book_code, chapter)

                if not verses:
                    print(f"\n  WARNING: No verses found for {book_code} {chapter}")
                else:
                    book_verses.extend(verses)
                    all_verses.extend(verses)

                # Be nice to the server
                time.sleep(0.3)

            except Exception as e:
                print(f"\n  ERROR: {book_code} {chapter}: {e}")

        print(f"  {book_code}: {len(book_verses)} verses                    ")

    # Write to CSV
    print(f"\nWriting {len(all_verses)} verses to {output_path}")
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["chapter", "verse", "text", "book"])
        writer.writeheader()
        writer.writerows(all_verses)

    print("Done!")
    return output_path


def test_single_chapter(html_file: str = None):
    """Test extraction on a saved HTML file (e.g., Acts 8).

    Args:
        html_file: Path to saved HTML file. If None, fetches Acts 8 from BLB directly.
    """
    print("Testing Acts 8...")

    if html_file:
        with open(html_file, "r") as f:
            html = f.read()
    else:
        # Fetch directly from BLB
        html = fetch_chapter("act", 8)

    verses = extract_verses(html, "ACT", 8)

    print(f"Found {len(verses)} verses")
    for v in verses[35:40]:  # Show around verse 37
        print(f"  {v['verse']}: {v['text'][:50]}...")

    # Check specifically for verse 37
    v37 = [v for v in verses if v["verse"] == 37]
    if v37:
        print(f"\nVerse 37 found:")
        print(f"  {v37[0]['text']}")
    else:
        print("\n  WARNING: Verse 37 NOT found!")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Optional: pass HTML file path as second argument
        html_file = sys.argv[2] if len(sys.argv) > 2 else None
        test_single_chapter(html_file)
    else:
        download_all()
