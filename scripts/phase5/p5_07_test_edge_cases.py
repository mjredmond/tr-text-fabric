#!/usr/bin/env python3
"""
Script: p5_07_test_edge_cases
Phase: 5 - QA
Purpose: Test unusual grammatical constructions

Input:  tf/ directory
Output: qa_edge_cases.log

Usage:
    python -m scripts.phase5.p5_07_test_edge_cases
    python -m scripts.phase5.p5_07_test_edge_cases --dry-run
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils.config import load_config
from scripts.utils.logging import ScriptLogger, get_logger


def main(config: dict = None, dry_run: bool = False) -> bool:
    """Main entry point."""
    if config is None:
        config = load_config()

    logger = get_logger(__name__)

    intermediate_dir = Path(config["paths"]["data"]["intermediate"])

    if dry_run:
        logger.info("[DRY RUN] Would test edge cases")
        return True

    import pandas as pd

    # Load data
    complete_path = intermediate_dir / "tr_complete.parquet"
    complete_df = pd.read_parquet(complete_path)

    logger.info("Testing Edge Cases")
    logger.info("=" * 50)

    # Test 1: Longest verses
    logger.info("\n1. Longest verses (by word count):")
    verse_lengths = complete_df.groupby(["book", "chapter", "verse"]).size()
    longest = verse_lengths.nlargest(5)
    for (book, ch, vs), count in longest.items():
        logger.info(f"   {book} {ch}:{vs} - {count} words")

    # Test 2: Shortest verses
    logger.info("\n2. Shortest verses:")
    shortest = verse_lengths.nsmallest(5)
    for (book, ch, vs), count in shortest.items():
        words = complete_df[
            (complete_df["book"] == book) &
            (complete_df["chapter"] == ch) &
            (complete_df["verse"] == vs)
        ]["word"].tolist()
        logger.info(f"   {book} {ch}:{vs} - {count} words: {' '.join(words)}")

    # Test 3: Rare parts of speech
    logger.info("\n3. Rare parts of speech:")
    sp_counts = complete_df["sp"].value_counts()
    rare_sp = sp_counts[sp_counts < 100]
    for sp, count in rare_sp.items():
        logger.info(f"   {sp}: {count}")

    # Test 4: Hapax legomena (words appearing only once)
    logger.info("\n4. Hapax legomena (sample):")
    word_counts = complete_df["word"].value_counts()
    hapax = word_counts[word_counts == 1]
    logger.info(f"   Total hapax: {len(hapax)}")
    for word in list(hapax.index)[:5]:
        row = complete_df[complete_df["word"] == word].iloc[0]
        logger.info(f"   {word} ({row['book']} {row['chapter']}:{row['verse']})")

    # Test 5: Words with unusual features
    logger.info("\n5. Optative mood verbs (rare):")
    optatives = complete_df[complete_df["mood"] == "optative"]
    if len(optatives) > 0:
        logger.info(f"   Found {len(optatives)} optative verbs")
        for _, row in optatives.head(3).iterrows():
            logger.info(f"   {row['word']} - {row['book']} {row['chapter']}:{row['verse']}")
    else:
        logger.info("   No optatives found (checking for alternate label...)")
        # Try other possible labels
        for mood_val in complete_df["mood"].unique():
            if mood_val and "opt" in str(mood_val).lower():
                logger.info(f"   Found mood value: {mood_val}")

    logger.info("\n" + "=" * 50)
    logger.info("PASSED: Edge case analysis complete")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    with ScriptLogger("p5_07_test_edge_cases") as logger:
        config = load_config()
        success = main(config, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
