#!/usr/bin/env python3
"""
Script: p4_01e_add_compat_features.py
Phase: 4 - Compilation
Purpose: Add N1904-compatible features for full word-level parity

Input:  data/intermediate/tr_complete.parquet
Output: data/intermediate/tr_complete.parquet (updated in place)

Features added:
- bookshort: Abbreviated book name (MAT, MRK, etc.)
- text: Surface word form (alias for unicode)
- normalized: Unicode NFC normalized form
- trailer: Material after word (alias for after)
- num: Word position in verse (1-based)
- ref: Reference string (e.g., "MAT 1:1!1")
- id: Unique word identifier (e.g., "n40001001001")
- cls: Word class (noun, verb, adj, etc.)

Usage:
    python -m scripts.phase4.p4_01e_add_compat_features
    python -m scripts.phase4.p4_01e_add_compat_features --dry-run
"""

import argparse
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils.config import load_config
from scripts.utils.logging import ScriptLogger, get_logger


# Book number mapping for ID generation (matches N1904 numbering)
BOOK_NUM = {
    "MAT": 40, "MAR": 41, "LUK": 42, "JHN": 43, "ACT": 44,
    "ROM": 45, "1CO": 46, "2CO": 47, "GAL": 48, "EPH": 49,
    "PHP": 50, "COL": 51, "1TH": 52, "2TH": 53, "1TI": 54,
    "2TI": 55, "TIT": 56, "PHM": 57, "HEB": 58, "JAS": 59,
    "1PE": 60, "2PE": 61, "1JN": 62, "2JN": 63, "3JN": 64,
    "JUD": 65, "REV": 66,
}

# SP to CLS mapping (based on N1904 patterns)
SP_TO_CLS = {
    # Direct mappings from N1904
    "verb": "verb",
    "subs": "noun",
    "art": "det",
    "conj": "conj",
    "pron": "pron",
    "prep": "prep",
    "adjv": "adj",
    "advb": "adv",
    "intj": "ptcl",  # Most interjections map to ptcl in N1904
    "num": "num",
    # TR-specific sp values (from NLP or variants)
    "noun": "noun",
    "adj": "adj",
    "adv": "adv",
    "punct": "punct",
    "det": "det",
    "ptcl": "ptcl",
}


def normalize_unicode(text: str) -> str:
    """Apply Unicode NFC normalization."""
    if not text:
        return text
    return unicodedata.normalize('NFC', text)


def generate_word_id(book: str, chapter: int, verse: int, num: int) -> str:
    """
    Generate unique word ID in N1904 format.

    Format: n{book_num:02d}{chapter:03d}{verse:03d}{num:03d}
    Example: n40001001001 (Matthew 1:1 word 1)
    """
    book_num = BOOK_NUM.get(book, 0)
    return f"n{book_num:02d}{chapter:03d}{verse:03d}{num:03d}"


def generate_ref(book: str, chapter: int, verse: int, num: int) -> str:
    """
    Generate reference string in N1904 format.

    Format: {book} {chapter}:{verse}!{num}
    Example: MAT 1:1!1
    """
    return f"{book} {chapter}:{verse}!{num}"


def map_sp_to_cls(sp: str) -> str:
    """Map sp (part of speech) to cls (word class)."""
    if not sp:
        return None
    return SP_TO_CLS.get(sp, sp)  # Return original if no mapping


def add_compat_features(df, logger):
    """
    Add N1904-compatible features to the dataframe.
    """
    import pandas as pd

    logger.info("Adding bookshort feature...")
    # Book is already abbreviated in our data
    df['bookshort'] = df['book']

    logger.info("Adding text feature...")
    # text is same as word (surface form)
    df['text'] = df['word']

    logger.info("Adding normalized feature...")
    df['normalized'] = df['word'].apply(normalize_unicode)

    logger.info("Adding trailer feature...")
    # trailer is same as after
    df['trailer'] = df['after']

    logger.info("Adding num feature...")
    # num is word position in verse (1-based)
    df['num'] = df['word_rank']

    logger.info("Adding ref feature...")
    df['ref'] = df.apply(
        lambda row: generate_ref(
            row['book'],
            int(row['chapter']),
            int(row['verse']),
            int(row['word_rank'])
        ),
        axis=1
    )

    logger.info("Adding id feature...")
    df['id'] = df.apply(
        lambda row: generate_word_id(
            row['book'],
            int(row['chapter']),
            int(row['verse']),
            int(row['word_rank'])
        ),
        axis=1
    )

    logger.info("Adding cls feature...")
    df['cls'] = df['sp'].apply(map_sp_to_cls)

    return df


def main(config: dict = None, dry_run: bool = False) -> bool:
    """Main entry point."""
    if config is None:
        config = load_config()

    logger = get_logger(__name__)

    complete_path = Path(config["paths"]["data"]["intermediate"]) / "tr_complete.parquet"

    if dry_run:
        logger.info("[DRY RUN] Would add compat features: bookshort, text, normalized, trailer, num, ref, id, cls")
        return True

    import pandas as pd

    # Check input
    if not complete_path.exists():
        logger.error(f"Input not found: {complete_path}")
        return False

    # Load data
    logger.info(f"Loading data from: {complete_path}")
    df = pd.read_parquet(complete_path)
    logger.info(f"Loaded {len(df)} words")

    # Check if features already exist
    new_features = ['bookshort', 'text', 'normalized', 'trailer', 'num', 'ref', 'id', 'cls']
    existing = [f for f in new_features if f in df.columns]
    if existing:
        logger.info(f"Features already exist (will be overwritten): {existing}")

    # Add features
    df = add_compat_features(df, logger)

    # Save
    logger.info(f"Saving to: {complete_path}")
    df.to_parquet(complete_path, index=False)

    # Report
    logger.info("\nFeature summary:")
    for feat in new_features:
        non_null = df[feat].notna().sum()
        logger.info(f"  {feat}: {non_null}/{len(df)} ({non_null/len(df)*100:.1f}%)")

    # Show sample
    logger.info("\nSample (first 3 rows):")
    sample_cols = ['word', 'bookshort', 'text', 'normalized', 'num', 'ref', 'id', 'cls']
    for idx, row in df.head(3).iterrows():
        logger.info(f"  {row['ref']}: {row['word']} -> cls={row['cls']}, id={row['id']}")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    with ScriptLogger("p4_01e_add_compat_features") as logger:
        config = load_config()
        success = main(config, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
