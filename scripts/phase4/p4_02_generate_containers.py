#!/usr/bin/env python3
"""
Script: p4_02_generate_containers.py
Phase: 4 - Compilation
Purpose: Create book/chapter/verse container nodes from word data

Input:  data/intermediate/tr_complete.parquet
Output: data/intermediate/tr_containers.parquet

Note: For simplicity, we use verse boundaries as our primary containers.
      Clause/phrase containers from N1904 are preserved where available.

Usage:
    python -m scripts.phase4.p4_02_generate_containers
    python -m scripts.phase4.p4_02_generate_containers --dry-run
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils.config import load_config
from scripts.utils.logging import ScriptLogger, get_logger


def generate_section_containers(complete_df):
    """
    Generate book, chapter, and verse container nodes.

    Args:
        complete_df: Complete TR words DataFrame

    Returns:
        DataFrame of container nodes
    """
    import pandas as pd

    logger = get_logger(__name__)

    containers = []

    # Get max word_id to start container IDs after words
    max_word_id = complete_df["word_id"].max()
    next_id = max_word_id + 1

    # Group by book
    for book in complete_df["book"].unique():
        book_df = complete_df[complete_df["book"] == book]
        book_slots = book_df["word_id"].tolist()

        book_node = {
            "node_id": next_id,
            "otype": "book",
            "name": book,
            "first_slot": min(book_slots),
            "last_slot": max(book_slots),
        }
        containers.append(book_node)
        next_id += 1

        # Group by chapter within book
        for chapter in sorted(book_df["chapter"].unique()):
            chapter_df = book_df[book_df["chapter"] == chapter]
            chapter_slots = chapter_df["word_id"].tolist()

            chapter_node = {
                "node_id": next_id,
                "otype": "chapter",
                "book": book,
                "chapter": chapter,
                "first_slot": min(chapter_slots),
                "last_slot": max(chapter_slots),
            }
            containers.append(chapter_node)
            next_id += 1

            # Group by verse within chapter
            for verse in sorted(chapter_df["verse"].unique()):
                verse_df = chapter_df[chapter_df["verse"] == verse]
                verse_slots = verse_df["word_id"].tolist()

                verse_node = {
                    "node_id": next_id,
                    "otype": "verse",
                    "book": book,
                    "chapter": chapter,
                    "verse": verse,
                    "first_slot": min(verse_slots),
                    "last_slot": max(verse_slots),
                }
                containers.append(verse_node)
                next_id += 1

    logger.info(f"Generated {len(containers)} section containers")

    return pd.DataFrame(containers), next_id


def main(config: dict = None, dry_run: bool = False) -> bool:
    """Main entry point."""
    if config is None:
        config = load_config()

    logger = get_logger(__name__)

    complete_path = Path(config["paths"]["data"]["intermediate"]) / "tr_complete.parquet"
    output_path = Path(config["paths"]["data"]["intermediate"]) / "tr_containers.parquet"

    if dry_run:
        logger.info("[DRY RUN] Would generate container nodes")
        return True

    import pandas as pd

    # Check input
    if not complete_path.exists():
        logger.error(f"Input not found: {complete_path}")
        return False

    # Load data
    logger.info("Loading complete data...")
    complete_df = pd.read_parquet(complete_path)
    logger.info(f"Words: {len(complete_df)}")

    # Generate section containers
    containers_df, next_id = generate_section_containers(complete_df)

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    containers_df.to_parquet(output_path, index=False)
    logger.info(f"Saved to: {output_path}")

    # Summary
    otype_counts = containers_df["otype"].value_counts()
    logger.info("\nContainer Summary:")
    logger.info("-" * 40)
    for otype, count in otype_counts.items():
        logger.info(f"  {otype}: {count}")
    logger.info(f"Next available node ID: {next_id}")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    with ScriptLogger("p4_02_generate_containers") as logger:
        config = load_config()
        success = main(config, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
