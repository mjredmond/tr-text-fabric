#!/usr/bin/env python3
"""
Script: p4_07_verify_build
Phase: 4 - Compilation
Purpose: Test that TF dataset loads correctly

Input:  data/output/tf/ directory
Output: verification log

Usage:
    python -m scripts.phase4.p4_07_verify_build
    python -m scripts.phase4.p4_07_verify_build --dry-run
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils.config import load_config
from scripts.utils.logging import ScriptLogger, get_logger


def verify_file_structure(tf_dir: Path) -> bool:
    """Verify all expected TF files exist."""
    logger = get_logger(__name__)

    # Feature names now match N1904 convention
    required_files = [
        "otext.tf",
        "otype.tf",
        "oslots.tf",
        "unicode.tf",   # N1904-compatible name for word text
        "lemma.tf",
    ]

    optional_files = [
        "sp.tf",
        "function.tf",
        "case.tf",
        "gender.tf",    # N1904-compatible name (was gn)
        "number.tf",    # N1904-compatible name (was nu)
        "person.tf",    # N1904-compatible name (was ps)
        "tense.tf",
        "voice.tf",
        "mood.tf",
        "gloss.tf",
        "source.tf",
        "parent.tf",
        "strong.tf",
        "morph.tf",
        "book.tf",
        "chapter.tf",
        "verse.tf",
    ]

    all_ok = True

    logger.info("Checking required files...")
    for fname in required_files:
        fpath = tf_dir / fname
        if fpath.exists():
            size = fpath.stat().st_size
            logger.info(f"  {fname}: {size:,} bytes")
        else:
            logger.error(f"  {fname}: MISSING")
            all_ok = False

    logger.info("Checking optional files...")
    for fname in optional_files:
        fpath = tf_dir / fname
        # Handle @-escaped filenames
        alt_fname = fname.replace("@", "_at_")
        alt_fpath = tf_dir / alt_fname

        if fpath.exists():
            size = fpath.stat().st_size
            logger.info(f"  {fname}: {size:,} bytes")
        elif alt_fpath.exists():
            size = alt_fpath.stat().st_size
            logger.info(f"  {alt_fname}: {size:,} bytes")
        else:
            logger.info(f"  {fname}: not present (optional)")

    return all_ok


def verify_file_format(tf_dir: Path) -> bool:
    """Verify TF file format is correct."""
    logger = get_logger(__name__)

    all_ok = True

    # Check otext.tf format
    otext_path = tf_dir / "otext.tf"
    if otext_path.exists():
        with open(otext_path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
            if first_line == "@config":
                logger.info("otext.tf: valid config format")
            else:
                logger.error(f"otext.tf: invalid format (expected @config, got {first_line})")
                all_ok = False

    # Check otype.tf format
    otype_path = tf_dir / "otype.tf"
    if otype_path.exists():
        with open(otype_path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
            if first_line == "@node":
                logger.info("otype.tf: valid node format")
            else:
                logger.error(f"otype.tf: invalid format (expected @node, got {first_line})")
                all_ok = False

    # Check oslots.tf format
    oslots_path = tf_dir / "oslots.tf"
    if oslots_path.exists():
        with open(oslots_path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
            if first_line == "@edge":
                logger.info("oslots.tf: valid edge format")
            else:
                logger.error(f"oslots.tf: invalid format (expected @edge, got {first_line})")
                all_ok = False

    return all_ok


def count_nodes(tf_dir: Path) -> dict:
    """Count nodes by type from otype.tf."""
    logger = get_logger(__name__)

    otype_path = tf_dir / "otype.tf"
    if not otype_path.exists():
        return {}

    counts = {}
    with open(otype_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("@"):
                continue

            parts = line.split("\t")
            if len(parts) == 2:
                node_type = parts[1]
                counts[node_type] = counts.get(node_type, 0) + 1

    return counts


def sample_data(tf_dir: Path, n: int = 5) -> bool:
    """Sample some data from word.tf."""
    logger = get_logger(__name__)

    word_path = tf_dir / "word.tf"
    if not word_path.exists():
        logger.error("Cannot sample: word.tf not found")
        return False

    logger.info(f"Sample of first {n} words:")
    with open(word_path, "r", encoding="utf-8") as f:
        count = 0
        for line in f:
            line = line.strip()
            if not line or line.startswith("@"):
                continue

            parts = line.split("\t")
            if len(parts) == 2:
                node_id, word = parts
                logger.info(f"  Node {node_id}: {word}")
                count += 1
                if count >= n:
                    break

    return True


def main(config: dict = None, dry_run: bool = False) -> bool:
    """Main entry point."""
    if config is None:
        config = load_config()

    logger = get_logger(__name__)

    tf_dir = Path(config["paths"]["data"]["output"]) / "tf"

    if dry_run:
        logger.info("[DRY RUN] Would verify TF dataset build")
        logger.info(f"[DRY RUN] Location: {tf_dir}")
        return True

    # Check TF directory exists
    if not tf_dir.exists():
        logger.error(f"TF directory not found: {tf_dir}")
        return False

    logger.info(f"Verifying TF dataset at: {tf_dir}")
    logger.info("=" * 50)

    # 1. Verify file structure
    logger.info("\n1. File Structure Check")
    logger.info("-" * 40)
    files_ok = verify_file_structure(tf_dir)

    # 2. Verify file format
    logger.info("\n2. File Format Check")
    logger.info("-" * 40)
    format_ok = verify_file_format(tf_dir)

    # 3. Count nodes
    logger.info("\n3. Node Counts")
    logger.info("-" * 40)
    counts = count_nodes(tf_dir)
    total = 0
    for node_type, count in sorted(counts.items()):
        logger.info(f"  {node_type}: {count:,}")
        total += count
    logger.info(f"  TOTAL: {total:,}")

    # 4. Sample data
    logger.info("\n4. Data Sample")
    logger.info("-" * 40)
    sample_data(tf_dir)

    # Summary
    logger.info("\n" + "=" * 50)
    if files_ok and format_ok:
        logger.info("VERIFICATION PASSED")
        logger.info("TF dataset appears to be valid")
        return True
    else:
        logger.error("VERIFICATION FAILED")
        if not files_ok:
            logger.error("  - Missing required files")
        if not format_ok:
            logger.error("  - Invalid file formats")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    with ScriptLogger("p4_07_verify_build") as logger:
        config = load_config()
        success = main(config, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
