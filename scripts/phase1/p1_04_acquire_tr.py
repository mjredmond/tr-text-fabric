#!/usr/bin/env python3
"""
Script: p1_04_acquire_tr.py
Phase: 1 - Reconnaissance
Purpose: Download Stephanus 1550 TR from Blue Letter Bible

Input:  None (downloads from BLB, uses cache if available)
Output: data/source/tr_blb.csv

The BLB scraper caches HTML pages in data/source/blb_cache/ so subsequent
runs are fast. Use --fresh to bypass cache and re-download.

Usage:
    python -m scripts.phase1.p1_04_acquire_tr
    python -m scripts.phase1.p1_04_acquire_tr --dry-run
    python -m scripts.phase1.p1_04_acquire_tr --fresh
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils.config import load_config
from scripts.utils.logging import ScriptLogger, get_logger


def main(config: dict = None, dry_run: bool = False, fresh: bool = False) -> bool:
    """Main entry point.

    Args:
        config: Pipeline configuration dict
        dry_run: If True, don't actually download
        fresh: If True, bypass cache and re-download from BLB
    """
    if config is None:
        config = load_config()

    logger = get_logger(__name__)

    source_dir = Path(config["paths"]["data"]["source"])
    output_path = source_dir / "tr_blb.csv"

    # Check if already exists (and not forcing fresh download)
    if output_path.exists() and not fresh:
        logger.info(f"TR data already exists: {output_path}")
        logger.info("Use --fresh to re-download from BLB")
        return True

    if dry_run:
        logger.info(f"[DRY RUN] Would download TR from Blue Letter Bible")
        logger.info(f"[DRY RUN] Would save to: {output_path}")
        return True

    # Import and run the BLB downloader
    logger.info("Downloading Stephanus 1550 TR from Blue Letter Bible...")
    logger.info("(HTML pages are cached in data/source/blb_cache/)")

    from scripts.download_blb_tr import download_all

    use_cache = not fresh
    result_path = download_all(use_cache=use_cache)

    if result_path and Path(result_path).exists():
        logger.info(f"TR data saved to: {result_path}")
        return True
    else:
        logger.error("Failed to download TR data")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview without downloading")
    parser.add_argument("--fresh", action="store_true",
                        help="Bypass cache and re-download from BLB")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    with ScriptLogger("p1_04_acquire_tr") as logger:
        config = load_config()
        success = main(config, dry_run=args.dry_run, fresh=args.fresh)
        sys.exit(0 if success else 1)
