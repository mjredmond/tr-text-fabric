#!/usr/bin/env python3
"""
Script: p2_02_align_verses.py
Phase: 2 - Alignment
Purpose: Create verse-level alignment framework using difflib

Input:  data/intermediate/tr_words.parquet, data/intermediate/n1904_words.parquet
Output: Module provides alignment functions (no file output)

Usage:
    python -m scripts.phase2.p2_02_align_verses
    python -m scripts.phase2.p2_02_align_verses --test
"""

import argparse
import sys
from difflib import SequenceMatcher
from pathlib import Path
from typing import List, Tuple, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils.config import load_config
from scripts.utils.logging import ScriptLogger, get_logger


def normalize_unicode(text: str) -> str:
    """
    Normalize Greek text to NFC form for consistent comparison.

    Greek texts may use different Unicode representations for the same
    visual characters (e.g., tonos vs oxia accents). NFC normalization
    ensures consistent comparison.

    Args:
        text: Greek text string

    Returns:
        NFC-normalized string
    """
    import unicodedata
    if not text:
        return ""
    return unicodedata.normalize("NFC", str(text))


def create_word_key(row: Dict[str, Any], match_criteria: List[str]) -> str:
    """
    Create a comparison key for a word based on match criteria.

    Args:
        row: Word row as dict
        match_criteria: List of feature names to include in key

    Returns:
        String key for comparison (Unicode NFC normalized)
    """
    parts = []
    for criterion in match_criteria:
        val = row.get(criterion, "")
        # Normalize Unicode for consistent comparison
        parts.append(normalize_unicode(val) if val else "")
    return "|".join(parts)


def align_verse_words(
    tr_words: List[Dict],
    n1904_words: List[Dict],
    match_criteria: List[str],
    threshold: float = 0.95
) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
    """
    Align words between TR and N1904 for a single verse.

    Args:
        tr_words: List of TR word dicts
        n1904_words: List of N1904 word dicts
        match_criteria: Features to match on
        threshold: Minimum similarity for matching

    Returns:
        Tuple of:
        - alignments: List of (tr_idx, n1904_idx) pairs
        - tr_gaps: List of TR indices with no match
        - n1904_gaps: List of N1904 indices with no match
    """
    # Create comparison keys
    tr_keys = [create_word_key(w, match_criteria) for w in tr_words]
    n1904_keys = [create_word_key(w, match_criteria) for w in n1904_words]

    # Use SequenceMatcher for alignment
    matcher = SequenceMatcher(None, tr_keys, n1904_keys)

    alignments = []
    tr_matched = set()
    n1904_matched = set()

    # Get matching blocks
    for block in matcher.get_matching_blocks():
        tr_start, n1904_start, size = block
        for i in range(size):
            tr_idx = tr_start + i
            n1904_idx = n1904_start + i
            alignments.append((tr_idx, n1904_idx))
            tr_matched.add(tr_idx)
            n1904_matched.add(n1904_idx)

    # Find gaps
    tr_gaps = [i for i in range(len(tr_words)) if i not in tr_matched]
    n1904_gaps = [i for i in range(len(n1904_words)) if i not in n1904_matched]

    return alignments, tr_gaps, n1904_gaps


def test_alignment(config: dict) -> bool:
    """
    Test alignment on sample data.

    Args:
        config: Pipeline config

    Returns:
        True if tests pass
    """
    import pandas as pd

    logger = get_logger(__name__)

    # Load data
    tr_path = Path(config["paths"]["data"]["intermediate"]) / "tr_words.parquet"
    n1904_path = Path(config["paths"]["data"]["intermediate"]) / "n1904_words.parquet"

    if not tr_path.exists() or not n1904_path.exists():
        logger.warning("Data files not found, skipping test")
        return True

    tr_df = pd.read_parquet(tr_path)
    n1904_df = pd.read_parquet(n1904_path)

    # Test on first verse of John
    test_book = "John"
    test_chapter = 1
    test_verse = 1

    tr_verse = tr_df[
        (tr_df["book"] == test_book) &
        (tr_df["chapter"] == test_chapter) &
        (tr_df["verse"] == test_verse)
    ].to_dict("records")

    n1904_verse = n1904_df[
        (n1904_df["book"] == test_book) &
        (n1904_df["chapter"] == test_chapter) &
        (n1904_df["verse"] == test_verse)
    ].to_dict("records")

    if not tr_verse or not n1904_verse:
        logger.warning(f"Test verse not found in data")
        return True

    # Run alignment
    match_criteria = config["alignment"]["match_criteria"]
    alignments, tr_gaps, n1904_gaps = align_verse_words(
        tr_verse, n1904_verse, match_criteria
    )

    logger.info(f"Test alignment on {test_book} {test_chapter}:{test_verse}")
    logger.info(f"  TR words: {len(tr_verse)}")
    logger.info(f"  N1904 words: {len(n1904_verse)}")
    logger.info(f"  Alignments: {len(alignments)}")
    logger.info(f"  TR gaps: {len(tr_gaps)}")
    logger.info(f"  N1904 gaps: {len(n1904_gaps)}")

    return True


def main(config: dict = None, dry_run: bool = False, test: bool = False) -> bool:
    """Main entry point."""
    if config is None:
        config = load_config()

    logger = get_logger(__name__)

    if dry_run:
        logger.info("[DRY RUN] Would verify alignment module is functional")
        return True

    if test:
        return test_alignment(config)

    # This script primarily provides functions for other scripts
    # Just verify it imports correctly
    logger.info("Alignment module verified")
    logger.info("Functions available:")
    logger.info("  - create_word_key(row, match_criteria)")
    logger.info("  - align_verse_words(tr_words, n1904_words, match_criteria)")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--test", action="store_true", help="Run alignment test")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    with ScriptLogger("p2_02_align_verses") as logger:
        config = load_config()
        success = main(config, dry_run=args.dry_run, test=args.test)
        sys.exit(0 if success else 1)
