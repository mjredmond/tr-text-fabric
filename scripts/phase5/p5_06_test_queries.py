#!/usr/bin/env python3
"""
Script: p5_06_test_queries
Phase: 5 - QA
Purpose: Verify TF queries work correctly

Input:  tf/ directory
Output: qa_query_tests.log

Usage:
    python -m scripts.phase5.p5_06_test_queries
    python -m scripts.phase5.p5_06_test_queries --dry-run
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils.config import load_config
from scripts.utils.logging import ScriptLogger, get_logger


def test_basic_queries(complete_df, logger):
    """Run basic query tests on the dataset."""
    import pandas as pd

    tests_passed = 0
    tests_failed = 0

    # Test 1: Find all verbs
    logger.info("\nTest 1: Find all verbs")
    verbs = complete_df[complete_df["sp"] == "verb"]
    if len(verbs) > 0:
        logger.info(f"  Found {len(verbs):,} verbs")
        tests_passed += 1
    else:
        logger.error("  FAILED: No verbs found")
        tests_failed += 1

    # Test 2: Find all nouns
    logger.info("\nTest 2: Find all nouns")
    nouns = complete_df[complete_df["sp"] == "noun"]
    if len(nouns) > 0:
        logger.info(f"  Found {len(nouns):,} nouns")
        tests_passed += 1
    else:
        logger.error("  FAILED: No nouns found")
        tests_failed += 1

    # Test 3: Find nominative case words
    logger.info("\nTest 3: Find nominative case words")
    nominatives = complete_df[complete_df["case"] == "nominative"]
    if len(nominatives) > 0:
        logger.info(f"  Found {len(nominatives):,} nominative words")
        tests_passed += 1
    else:
        logger.error("  FAILED: No nominatives found")
        tests_failed += 1

    # Test 4: Find words in John 3:16
    logger.info("\nTest 4: Find John 3:16")
    john316 = complete_df[
        (complete_df["book"] == "JHN") &  # BLB format
        (complete_df["chapter"] == 3) &
        (complete_df["verse"] == 16)
    ]
    if len(john316) > 0:
        text = " ".join(john316["word"].tolist())
        logger.info(f"  Found {len(john316)} words: {text[:60]}...")
        tests_passed += 1
    else:
        logger.error("  FAILED: John 3:16 not found")
        tests_failed += 1

    # Test 5: Find words with gloss
    logger.info("\nTest 5: Find words with English gloss")
    with_gloss = complete_df[complete_df["gloss"].notna() & (complete_df["gloss"] != "")]
    if len(with_gloss) > 0:
        logger.info(f"  Found {len(with_gloss):,} words with gloss ({len(with_gloss)/len(complete_df)*100:.1f}%)")
        tests_passed += 1
    else:
        logger.warning("  No words with gloss found")
        tests_failed += 1

    return tests_passed, tests_failed


def main(config: dict = None, dry_run: bool = False) -> bool:
    """Main entry point."""
    if config is None:
        config = load_config()

    logger = get_logger(__name__)

    intermediate_dir = Path(config["paths"]["data"]["intermediate"])

    if dry_run:
        logger.info("[DRY RUN] Would test query functionality")
        return True

    import pandas as pd

    # Load data
    complete_path = intermediate_dir / "tr_complete.parquet"
    complete_df = pd.read_parquet(complete_path)

    logger.info("Testing Query Functionality")
    logger.info("=" * 50)

    passed, failed = test_basic_queries(complete_df, logger)

    logger.info("\n" + "=" * 50)
    logger.info(f"Tests passed: {passed}")
    logger.info(f"Tests failed: {failed}")

    if failed == 0:
        logger.info("PASSED: All query tests passed")
        return True
    else:
        logger.error(f"FAILED: {failed} test(s) failed")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    with ScriptLogger("p5_06_test_queries") as logger:
        config = load_config()
        success = main(config, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
