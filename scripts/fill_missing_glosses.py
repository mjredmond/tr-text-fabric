#!/usr/bin/env python3
"""
Fill missing glosses for NLP-sourced words.

Strategy:
1. First, try to fill from N1904 (for lemmas that appear there)
2. Then, fetch from Blue Letter Bible lexicon for remaining words

Usage:
    python scripts/fill_missing_glosses.py
    python scripts/fill_missing_glosses.py --dry-run
    python scripts/fill_missing_glosses.py --skip-blb  # Only use N1904
"""

import argparse
import sys
import time
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import requests
from bs4 import BeautifulSoup

from scripts.utils.config import load_config


def load_data():
    """Load TR and N1904 datasets."""
    config = load_config()
    intermediate_dir = Path(config["paths"]["data"]["intermediate"])

    tr_df = pd.read_parquet(intermediate_dir / "tr_complete.parquet")
    n1904_df = pd.read_parquet(intermediate_dir / "n1904_words.parquet")

    return tr_df, n1904_df, intermediate_dir


def build_n1904_gloss_map(n1904_df):
    """Build lemma -> gloss lookup from N1904."""
    # Get first gloss for each lemma (they should be consistent)
    gloss_map = (
        n1904_df[n1904_df["gloss"].notna() & (n1904_df["gloss"] != "")]
        .groupby("lemma")["gloss"]
        .first()
        .to_dict()
    )
    return gloss_map


def fill_from_n1904(tr_df, n1904_gloss_map):
    """
    Step 1: Fill glosses from N1904 for matching lemmas.

    Returns:
        Updated dataframe and count of filled glosses
    """
    print("\n" + "=" * 60)
    print("STEP 1: FILL GLOSSES FROM N1904")
    print("=" * 60)

    # Find words without gloss
    no_gloss_mask = tr_df["gloss"].isna() | (tr_df["gloss"] == "")
    no_gloss_count = no_gloss_mask.sum()
    print(f"  Words without gloss: {no_gloss_count:,}")

    # Fill from N1904 where lemma matches
    filled_count = 0
    for idx in tr_df[no_gloss_mask].index:
        lemma = tr_df.at[idx, "lemma"]
        if lemma in n1904_gloss_map:
            tr_df.at[idx, "gloss"] = n1904_gloss_map[lemma]
            filled_count += 1

    print(f"  Filled from N1904: {filled_count:,}")

    # Check remaining
    still_missing = (tr_df["gloss"].isna() | (tr_df["gloss"] == "")).sum()
    print(f"  Still missing: {still_missing:,}")

    return tr_df, filled_count, still_missing


def fetch_blb_gloss(word, lemma):
    """
    Fetch gloss from Blue Letter Bible lexicon.

    Tries to find the word in BLB's Greek lexicon and extract the definition.
    """
    # Clean the lemma for URL
    search_term = lemma if lemma else word

    # BLB search URL
    url = f"https://www.blueletterbible.org/lexicon/{search_term}/kjv/tr/"

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # Try to find the definition/gloss
        # BLB structure varies, try multiple selectors

        # Look for outline of biblical usage
        outline = soup.find("div", class_="lexicon-outline")
        if outline:
            # Get first definition
            first_def = outline.find("li")
            if first_def:
                text = first_def.get_text(strip=True)
                # Clean up the text
                text = re.sub(r'\s+', ' ', text)
                if len(text) > 100:
                    text = text[:100] + "..."
                return text

        # Look for short definition
        short_def = soup.find("span", class_="lexicon-short-definition")
        if short_def:
            return short_def.get_text(strip=True)

        # Look for any definition content
        def_div = soup.find("div", class_="definition")
        if def_div:
            text = def_div.get_text(strip=True)[:100]
            return text

        return None

    except Exception as e:
        print(f"    Error fetching {search_term}: {e}")
        return None


def fill_from_blb(tr_df, batch_size=50):
    """
    Step 2: Fill remaining glosses from Blue Letter Bible.

    Returns:
        Updated dataframe and count of filled glosses
    """
    print("\n" + "=" * 60)
    print("STEP 2: FILL GLOSSES FROM BLUE LETTER BIBLE")
    print("=" * 60)

    # Find words still without gloss
    no_gloss_mask = tr_df["gloss"].isna() | (tr_df["gloss"] == "")
    no_gloss = tr_df[no_gloss_mask]

    if len(no_gloss) == 0:
        print("  No missing glosses - skipping BLB fetch")
        return tr_df, 0

    # Get unique lemmas that need glosses
    missing_lemmas = no_gloss["lemma"].unique()
    print(f"  Unique lemmas needing glosses: {len(missing_lemmas)}")

    # Fetch glosses for unique lemmas
    blb_gloss_map = {}
    fetched = 0
    failed = 0

    print(f"  Fetching from BLB (this may take a while)...")

    for i, lemma in enumerate(missing_lemmas):
        if pd.isna(lemma):
            continue

        # Progress update
        if (i + 1) % 10 == 0:
            print(f"    Progress: {i+1}/{len(missing_lemmas)} ({fetched} found, {failed} failed)")

        # Fetch from BLB
        gloss = fetch_blb_gloss(None, lemma)

        if gloss:
            blb_gloss_map[lemma] = gloss
            fetched += 1
        else:
            failed += 1

        # Rate limiting - be nice to BLB
        time.sleep(0.5)

        # Optional: stop after batch_size for testing
        if batch_size and i >= batch_size - 1:
            print(f"    Stopping after {batch_size} (use --no-limit for all)")
            break

    print(f"  Fetched {fetched} glosses from BLB")

    # Apply BLB glosses
    filled_count = 0
    for idx in no_gloss.index:
        lemma = tr_df.at[idx, "lemma"]
        if lemma in blb_gloss_map:
            tr_df.at[idx, "gloss"] = blb_gloss_map[lemma]
            filled_count += 1

    print(f"  Applied to {filled_count:,} words")

    # Save BLB gloss map for reuse
    if blb_gloss_map:
        config = load_config()
        cache_path = Path(config["paths"]["data"]["intermediate"]) / "blb_gloss_cache.json"
        import json

        # Load existing cache if present
        existing = {}
        if cache_path.exists():
            with open(cache_path) as f:
                existing = json.load(f)

        # Merge and save
        existing.update(blb_gloss_map)
        with open(cache_path, "w") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        print(f"  Cached {len(existing)} glosses to {cache_path}")

    return tr_df, filled_count


def load_blb_cache():
    """Load cached BLB glosses if available."""
    config = load_config()
    cache_path = Path(config["paths"]["data"]["intermediate"]) / "blb_gloss_cache.json"

    if cache_path.exists():
        import json
        with open(cache_path) as f:
            return json.load(f)
    return {}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--skip-blb", action="store_true", help="Only use N1904, skip BLB")
    parser.add_argument("--no-limit", action="store_true", help="Fetch all from BLB (slow)")
    parser.add_argument("--batch-size", type=int, default=50, help="BLB fetch batch size")
    args = parser.parse_args()

    print("=" * 60)
    print("FILL MISSING GLOSSES")
    print("=" * 60)

    # Load data
    print("\nLoading data...")
    tr_df, n1904_df, intermediate_dir = load_data()

    initial_missing = (tr_df["gloss"].isna() | (tr_df["gloss"] == "")).sum()
    print(f"  TR words: {len(tr_df):,}")
    print(f"  Words without gloss: {initial_missing:,}")

    if args.dry_run:
        print("\n[DRY RUN MODE]")

        # Check N1904 coverage
        n1904_gloss_map = build_n1904_gloss_map(n1904_df)
        no_gloss = tr_df[tr_df["gloss"].isna() | (tr_df["gloss"] == "")]
        can_fill = no_gloss[no_gloss["lemma"].isin(n1904_gloss_map.keys())]

        print(f"\n  N1904 gloss map entries: {len(n1904_gloss_map):,}")
        print(f"  Words fillable from N1904: {len(can_fill):,}")
        print(f"  Would need BLB for: {len(no_gloss) - len(can_fill):,}")
        return

    # Step 1: Fill from N1904
    n1904_gloss_map = build_n1904_gloss_map(n1904_df)
    print(f"\n  N1904 gloss map entries: {len(n1904_gloss_map):,}")

    tr_df, n1904_filled, still_missing = fill_from_n1904(tr_df, n1904_gloss_map)

    # Step 2: Fill from BLB (if needed and not skipped)
    blb_filled = 0
    if still_missing > 0 and not args.skip_blb:
        # First try cache
        blb_cache = load_blb_cache()
        if blb_cache:
            print(f"\n  Found {len(blb_cache)} cached BLB glosses")
            cache_filled = 0
            no_gloss_mask = tr_df["gloss"].isna() | (tr_df["gloss"] == "")
            for idx in tr_df[no_gloss_mask].index:
                lemma = tr_df.at[idx, "lemma"]
                if lemma in blb_cache:
                    tr_df.at[idx, "gloss"] = blb_cache[lemma]
                    cache_filled += 1
            print(f"  Filled {cache_filled:,} from cache")
            blb_filled += cache_filled

        # Check if we still need more
        still_missing = (tr_df["gloss"].isna() | (tr_df["gloss"] == "")).sum()
        if still_missing > 0:
            batch = None if args.no_limit else args.batch_size
            tr_df, fetch_filled = fill_from_blb(tr_df, batch_size=batch)
            blb_filled += fetch_filled
    elif still_missing > 0:
        print("\n  Skipping BLB fetch (--skip-blb)")

    # Summary
    final_missing = (tr_df["gloss"].isna() | (tr_df["gloss"] == "")).sum()
    total_filled = initial_missing - final_missing

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Initial missing: {initial_missing:,}")
    print(f"  Filled from N1904: {n1904_filled:,}")
    print(f"  Filled from BLB: {blb_filled:,}")
    print(f"  Total filled: {total_filled:,}")
    print(f"  Still missing: {final_missing:,}")
    print(f"  Coverage: {(len(tr_df) - final_missing) / len(tr_df) * 100:.1f}%")

    # Save updated data
    if total_filled > 0:
        output_path = intermediate_dir / "tr_complete.parquet"
        tr_df.to_parquet(output_path)
        print(f"\n  Saved to {output_path}")

    print("=" * 60)


if __name__ == "__main__":
    main()
