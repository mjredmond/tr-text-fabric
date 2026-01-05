#!/usr/bin/env python3
"""
Script: p4_03_configure_otypes.py
Phase: 4 - Compilation
Purpose: Configure node type hierarchy and slot assignments

Input:  data/intermediate/tr_complete.parquet, data/intermediate/tr_containers.parquet
Output: data/intermediate/tf_config.json

Usage:
    python -m scripts.phase4.p4_03_configure_otypes
    python -m scripts.phase4.p4_03_configure_otypes --dry-run
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils.config import load_config
from scripts.utils.logging import ScriptLogger, get_logger


def configure_otypes(complete_df, containers_df, config: dict) -> dict:
    """
    Configure the Text-Fabric otypes hierarchy.

    In TF:
    - "slots" are the atomic/terminal nodes (words in our case)
    - Other otypes are containers that span ranges of slots

    Args:
        complete_df: Complete word data
        containers_df: Container nodes
        config: Pipeline config

    Returns:
        TF configuration dictionary
    """
    logger = get_logger(__name__)

    # Otypes in order from largest to smallest
    # Word is the slot type (terminal node)
    otypes_order = ["book", "chapter", "verse", "word"]

    # Count nodes per type
    word_count = len(complete_df)
    book_count = len(containers_df[containers_df["otype"] == "book"])
    chapter_count = len(containers_df[containers_df["otype"] == "chapter"])
    verse_count = len(containers_df[containers_df["otype"] == "verse"])

    tf_config = {
        "otypes": otypes_order,
        "slot_type": "word",
        "counts": {
            "word": word_count,
            "verse": verse_count,
            "chapter": chapter_count,
            "book": book_count,
        },
        "node_ranges": {
            "word": (1, word_count),
            "verse": (word_count + 1, word_count + verse_count),
            "chapter": (word_count + verse_count + 1, word_count + verse_count + chapter_count),
            "book": (word_count + verse_count + chapter_count + 1,
                    word_count + verse_count + chapter_count + book_count),
        },
        "features": {
            "word": ["word", "lemma", "sp", "function", "case", "gn", "nu", "ps",
                    "tense", "voice", "mood", "gloss", "source"],
            "verse": ["book", "chapter", "verse"],
            "chapter": ["book", "chapter"],
            "book": ["name"],
        },
        "metadata": {
            "name": config["tf_output"]["dataset_name"],
            "version": config["tf_output"]["version"],
            "language": config["tf_output"]["language"],
        }
    }

    logger.info("OTypes configuration:")
    for otype in otypes_order:
        count = tf_config["counts"].get(otype, 0)
        logger.info(f"  {otype}: {count} nodes")

    return tf_config


def main(config: dict = None, dry_run: bool = False) -> bool:
    """Main entry point."""
    if config is None:
        config = load_config()

    logger = get_logger(__name__)

    complete_path = Path(config["paths"]["data"]["intermediate"]) / "tr_complete.parquet"
    containers_path = Path(config["paths"]["data"]["intermediate"]) / "tr_containers.parquet"
    output_path = Path(config["paths"]["data"]["intermediate"]) / "tf_config.json"

    if dry_run:
        logger.info("[DRY RUN] Would configure otypes hierarchy")
        return True

    import pandas as pd

    # Check inputs
    if not complete_path.exists():
        logger.error(f"Input not found: {complete_path}")
        return False
    if not containers_path.exists():
        logger.error(f"Input not found: {containers_path}")
        return False

    # Load data
    logger.info("Loading data...")
    complete_df = pd.read_parquet(complete_path)
    containers_df = pd.read_parquet(containers_path)

    # Configure otypes
    tf_config = configure_otypes(complete_df, containers_df, config)

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(tf_config, f, indent=2)

    logger.info(f"Saved TF config to: {output_path}")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    with ScriptLogger("p4_03_configure_otypes") as logger:
        config = load_config()
        success = main(config, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
