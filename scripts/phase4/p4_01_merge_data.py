#!/usr/bin/env python3
"""
Script: p4_01_merge_data.py
Phase: 4 - Compilation
Purpose: Combine transplanted syntax (from N1904) with gap syntax (from NLP)

Input:  data/intermediate/tr_transplanted.parquet, data/intermediate/gap_syntax.parquet
Output: data/intermediate/tr_complete.parquet

Usage:
    python -m scripts.phase4.p4_01_merge_data
    python -m scripts.phase4.p4_01_merge_data --dry-run
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils.config import load_config
from scripts.utils.logging import ScriptLogger, get_logger


def normalize_books(df):
    """
    Normalize book names to standard 27 NT books.

    Fixes:
    - ACT24 → ACT (Acts 24:6-8, Western text variant)
    - PA → JOH (Pericope Adulterae, John 7:53-8:11)
    """
    logger = get_logger(__name__)

    # Track changes
    act24_count = (df["book"] == "ACT24").sum()
    pa_count = (df["book"] == "PA").sum()

    # Normalize ACT24 → ACT
    df.loc[df["book"] == "ACT24", "book"] = "ACT"

    # Normalize PA → JOH (Pericope Adulterae is John 7:53-8:11)
    df.loc[df["book"] == "PA", "book"] = "JOH"

    if act24_count > 0:
        logger.info(f"Normalized ACT24 → ACT: {act24_count} words")
    if pa_count > 0:
        logger.info(f"Normalized PA → JOH: {pa_count} words")

    return df


def merge_syntax_data(transplanted_df, gap_syntax_df, tr_words_df):
    """
    Merge transplanted syntax with NLP-generated gap syntax.

    Args:
        transplanted_df: TR words with transplanted N1904 syntax
        gap_syntax_df: NLP-generated syntax for gap words
        tr_words_df: Original TR words for validation

    Returns:
        Complete DataFrame with all words having syntax
    """
    import pandas as pd

    logger = get_logger(__name__)

    # Start with transplanted data
    complete_df = transplanted_df.copy()

    # Identify gap words (those without syntax)
    gap_word_ids = set(gap_syntax_df["word_id"].tolist())

    logger.info(f"Transplanted words: {len(complete_df)}")
    logger.info(f"Gap syntax words: {len(gap_syntax_df)}")

    # Update gap words with NLP syntax
    gap_syntax_lookup = gap_syntax_df.set_index("word_id").to_dict("index")

    updated_count = 0
    for idx, row in complete_df.iterrows():
        word_id = row["word_id"]
        if word_id in gap_syntax_lookup:
            gap_data = gap_syntax_lookup[word_id]

            # Update syntax fields from NLP
            for col in ["lemma", "sp", "function", "parent"]:
                if col in gap_data and gap_data[col] is not None:
                    complete_df.at[idx, col] = gap_data[col]

            # Update morphology if available
            for col in ["case", "gn", "nu", "ps", "tense", "voice", "mood"]:
                if col in gap_data and gap_data[col] is not None:
                    complete_df.at[idx, col] = gap_data[col]

            # Mark as NLP-generated (not transplanted)
            complete_df.at[idx, "aligned"] = False
            complete_df.at[idx, "source"] = "nlp"
            updated_count += 1

    # Mark transplanted words
    complete_df.loc[complete_df["aligned"] == True, "source"] = "n1904"

    logger.info(f"Updated {updated_count} gap words with NLP syntax")

    # Sort by canonical order
    complete_df = complete_df.sort_values(
        ["book", "chapter", "verse", "word_rank"]
    ).reset_index(drop=True)

    return complete_df


def validate_merge(complete_df, tr_words_df):
    """Validate that merge is complete and correct."""
    logger = get_logger(__name__)

    # Check word count matches
    if len(complete_df) != len(tr_words_df):
        logger.error(f"Word count mismatch: {len(complete_df)} vs {len(tr_words_df)}")
        return False

    # Check all word IDs present
    complete_ids = set(complete_df["word_id"])
    original_ids = set(tr_words_df["word_id"])

    if complete_ids != original_ids:
        missing = original_ids - complete_ids
        extra = complete_ids - original_ids
        if missing:
            logger.error(f"Missing {len(missing)} word IDs")
        if extra:
            logger.error(f"Extra {len(extra)} word IDs")
        return False

    # Check no duplicate word IDs
    if len(complete_df) != len(complete_df["word_id"].unique()):
        logger.error("Duplicate word IDs found")
        return False

    logger.info("Merge validation passed")
    return True


def main(config: dict = None, dry_run: bool = False) -> bool:
    """Main entry point."""
    if config is None:
        config = load_config()

    logger = get_logger(__name__)

    transplanted_path = Path(config["paths"]["data"]["intermediate"]) / "tr_transplanted.parquet"
    gap_syntax_path = Path(config["paths"]["data"]["intermediate"]) / "gap_syntax.parquet"
    tr_words_path = Path(config["paths"]["data"]["intermediate"]) / "tr_words.parquet"
    output_path = Path(config["paths"]["data"]["intermediate"]) / "tr_complete.parquet"

    if dry_run:
        logger.info("[DRY RUN] Would merge transplanted and gap syntax data")
        return True

    import pandas as pd

    # Check inputs
    for path in [transplanted_path, gap_syntax_path, tr_words_path]:
        if not path.exists():
            logger.error(f"Input not found: {path}")
            return False

    # Load data
    logger.info("Loading data...")
    transplanted_df = pd.read_parquet(transplanted_path)
    gap_syntax_df = pd.read_parquet(gap_syntax_path)
    tr_words_df = pd.read_parquet(tr_words_path)

    logger.info(f"Transplanted: {len(transplanted_df)} words")
    logger.info(f"Gap syntax: {len(gap_syntax_df)} words")
    logger.info(f"Original TR: {len(tr_words_df)} words")

    # Merge
    logger.info("Merging data...")
    complete_df = merge_syntax_data(transplanted_df, gap_syntax_df, tr_words_df)

    # Normalize book names (ACT24 → ACT, PA → JOH)
    logger.info("Normalizing book names...")
    complete_df = normalize_books(complete_df)

    # Also normalize tr_words_df for validation comparison
    tr_words_df = normalize_books(tr_words_df.copy())

    # Validate
    if not validate_merge(complete_df, tr_words_df):
        return False

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    complete_df.to_parquet(output_path, index=False)
    logger.info(f"Saved to: {output_path}")

    # Summary
    n1904_count = (complete_df["source"] == "n1904").sum()
    nlp_count = (complete_df["source"] == "nlp").sum()
    other_count = len(complete_df) - n1904_count - nlp_count
    book_count = len(complete_df["book"].unique())

    logger.info("\nMerge Summary:")
    logger.info("-" * 40)
    logger.info(f"Total words: {len(complete_df)}")
    logger.info(f"Total books: {book_count}")
    logger.info(f"From N1904 (transplanted): {n1904_count} ({n1904_count/len(complete_df)*100:.1f}%)")
    logger.info(f"From NLP (generated): {nlp_count} ({nlp_count/len(complete_df)*100:.1f}%)")
    if other_count > 0:
        logger.info(f"Other: {other_count}")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    with ScriptLogger("p4_01_merge_data") as logger:
        config = load_config()
        success = main(config, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
