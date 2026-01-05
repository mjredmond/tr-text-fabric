#!/usr/bin/env python3
"""
Script: p5_05_spot_check_variants
Phase: 5 - QA
Purpose: Manual verification of high-profile variants

Input:  tf/ directory
Output: qa_variant_reviews/

Usage:
    python -m scripts.phase5.p5_05_spot_check_variants
    python -m scripts.phase5.p5_05_spot_check_variants --dry-run
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils.config import load_config
from scripts.utils.logging import ScriptLogger, get_logger


HIGH_PROFILE_VARIANTS = [
    {
        "name": "Comma Johanneum",
        "ref": "1 John 5:7-8",
        "book": "1JN",  # BLB format
        "chapter": 5,
        "verses": [7, 8],
        "description": "Three heavenly witnesses passage",
    },
    {
        "name": "Eunuch's Confession",
        "ref": "Acts 8:37",
        "book": "ACT",
        "chapter": 8,
        "verses": [37],
        "description": "Philip and the Ethiopian eunuch",
    },
    {
        "name": "Pericope Adulterae",
        "ref": "John 7:53-8:11",
        "book": "JHN",  # BLB format
        "chapter": 8,
        "verses": list(range(1, 12)),  # 8:1-11
        "description": "Woman caught in adultery",
    },
    {
        "name": "Longer Ending of Mark",
        "ref": "Mark 16:9-20",
        "book": "MAR",
        "chapter": 16,
        "verses": list(range(9, 21)),
        "description": "Extended ending of Mark's Gospel",
    },
    {
        "name": "Lord's Prayer Doxology",
        "ref": "Matthew 6:13",
        "book": "MAT",
        "chapter": 6,
        "verses": [13],
        "description": "For thine is the kingdom...",
    },
]


def main(config: dict = None, dry_run: bool = False) -> bool:
    """Main entry point."""
    if config is None:
        config = load_config()

    logger = get_logger(__name__)

    intermediate_dir = Path(config["paths"]["data"]["intermediate"])

    if dry_run:
        logger.info("[DRY RUN] Would spot check high-profile variants")
        return True

    import pandas as pd

    # Load data
    complete_path = intermediate_dir / "tr_complete.parquet"
    complete_df = pd.read_parquet(complete_path)

    logger.info("Spot Checking High-Profile Variants")
    logger.info("=" * 50)

    all_found = True

    for variant in HIGH_PROFILE_VARIANTS:
        logger.info(f"\n{variant['name']} ({variant['ref']})")
        logger.info("-" * 40)

        # Find verses for this variant
        mask = (
            (complete_df["book"] == variant["book"]) &
            (complete_df["chapter"] == variant["chapter"]) &
            (complete_df["verse"].isin(variant["verses"]))
        )
        words = complete_df[mask]

        if len(words) == 0:
            logger.warning(f"  NOT FOUND!")
            all_found = False
        else:
            logger.info(f"  Words found: {len(words)}")
            logger.info(f"  Verses: {sorted(words['verse'].unique())}")

            # Show sample words
            sample = words.head(5)
            word_sample = " ".join(sample["word"].tolist())
            logger.info(f"  Sample: {word_sample}...")

            # Check syntax coverage
            with_syntax = (words["source"] == "n1904").sum()
            from_nlp = (words["source"] == "nlp").sum()
            logger.info(f"  From N1904: {with_syntax}, From NLP: {from_nlp}")

    logger.info("\n" + "=" * 50)
    if all_found:
        logger.info("PASSED: All high-profile variants found")
    else:
        logger.warning("WARNING: Some variants not found")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    with ScriptLogger("p5_05_spot_check_variants") as logger:
        config = load_config()
        success = main(config, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
