#!/usr/bin/env python3
"""
Script: p5_03_check_features
Phase: 5 - QA
Purpose: Verify all required features present

Input:  tf/, schema_map.json
Output: qa_feature_check.log

Usage:
    python -m scripts.phase5.p5_03_check_features
    python -m scripts.phase5.p5_03_check_features --dry-run
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils.config import load_config
from scripts.utils.logging import ScriptLogger, get_logger


def count_feature_values(tf_dir: Path, feature_name: str) -> int:
    """Count values in a feature file."""
    # Handle @ in filename
    file_name = feature_name.replace("@", "_at_") + ".tf"
    feat_path = tf_dir / file_name

    if not feat_path.exists():
        # Try without replacement
        feat_path = tf_dir / (feature_name + ".tf")
        if not feat_path.exists():
            return 0

    count = 0
    with open(feat_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("@"):
                count += 1

    return count


def main(config: dict = None, dry_run: bool = False) -> bool:
    """Main entry point."""
    if config is None:
        config = load_config()

    logger = get_logger(__name__)

    tf_dir = Path(config["paths"]["data"]["output"]) / "tf"

    if dry_run:
        logger.info("[DRY RUN] Would verify feature completeness")
        return True

    # Define required features per node type
    required_features = {
        "word": ["word", "lemma", "sp"],  # Core required features
    }

    optional_features = {
        "word": ["function", "case", "gn", "nu", "ps", "tense", "voice", "mood", "gloss", "source"],
    }

    # Load otype to count nodes
    otypes = {}
    otype_path = tf_dir / "otype.tf"
    with open(otype_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("@"):
                continue
            parts = line.split("\t")
            if len(parts) == 2:
                otype = parts[1]
                otypes[otype] = otypes.get(otype, 0) + 1

    logger.info("Node counts by type:")
    for otype, count in sorted(otypes.items()):
        logger.info(f"  {otype}: {count:,}")

    # Check required features
    logger.info("\nChecking required features...")
    all_ok = True

    for node_type, features in required_features.items():
        expected_count = otypes.get(node_type, 0)
        logger.info(f"\n{node_type} (expected: {expected_count:,}):")

        for feat in features:
            actual_count = count_feature_values(tf_dir, feat)
            status = "OK" if actual_count == expected_count else "MISMATCH"
            if actual_count != expected_count:
                all_ok = False
            logger.info(f"  {feat}: {actual_count:,} [{status}]")

    # Check optional features
    logger.info("\nChecking optional features...")
    for node_type, features in optional_features.items():
        expected_count = otypes.get(node_type, 0)
        logger.info(f"\n{node_type} optional features:")

        for feat in features:
            actual_count = count_feature_values(tf_dir, feat)
            coverage = (actual_count / expected_count * 100) if expected_count > 0 else 0
            logger.info(f"  {feat}: {actual_count:,} ({coverage:.1f}%)")

    if all_ok:
        logger.info("\nPASSED: All required features present")
    else:
        logger.error("\nFAILED: Some required features missing")

    return all_ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    with ScriptLogger("p5_03_check_features") as logger:
        config = load_config()
        success = main(config, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
