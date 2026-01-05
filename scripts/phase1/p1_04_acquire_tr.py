#!/usr/bin/env python3
"""
Script: p1_04_acquire_tr.py
Phase: 1 - Reconnaissance
Purpose: Download and prepare TR source text with morphology

Input:  None (downloads from configured URL)
Output: data/source/tr_raw.csv

Usage:
    python -m scripts.phase1.p1_04_acquire_tr
    python -m scripts.phase1.p1_04_acquire_tr --dry-run
"""

import argparse
import io
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils.config import load_config
from scripts.utils.logging import ScriptLogger, get_logger


def download_and_extract(url: str, target_pattern: str, output_path: Path) -> bool:
    """
    Download a ZIP file and extract matching files, combining CSVs.

    Args:
        url: URL to download
        target_pattern: Path pattern within ZIP to match
        output_path: Where to save the combined output

    Returns:
        True if successful
    """
    logger = get_logger(__name__)

    try:
        import requests
        import pandas as pd
    except ImportError as e:
        logger.error(f"Required library not installed: {e}")
        return False

    logger.info(f"Downloading from: {url}")

    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return False

    logger.info(f"Downloaded {len(response.content):,} bytes")

    # Extract from ZIP
    logger.info(f"Looking for pattern: {target_pattern}")
    try:
        all_dfs = []
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            names = zf.namelist()
            # Find CSV files matching the pattern
            matching = [n for n in names if target_pattern in n and n.endswith('.csv')]

            if not matching:
                logger.error(f"No CSV files found matching: {target_pattern}")
                logger.info(f"Available files: {names[:20]}...")
                return False

            logger.info(f"Found {len(matching)} CSV files")

            # Read and combine all CSV files
            for csv_file in sorted(matching):
                with zf.open(csv_file) as src:
                    try:
                        df = pd.read_csv(src)
                        # Add book name from filename if not present
                        book_name = Path(csv_file).stem
                        if 'book' not in df.columns and 'Book' not in df.columns:
                            df['book'] = book_name
                        all_dfs.append(df)
                        logger.info(f"  Loaded {csv_file}: {len(df)} rows")
                    except Exception as e:
                        logger.warning(f"  Skipping {csv_file}: {e}")

        if not all_dfs:
            logger.error("No valid CSV files found")
            return False

        # Combine all DataFrames
        combined = pd.concat(all_dfs, ignore_index=True)
        logger.info(f"Combined: {len(combined):,} total rows")

        # Save combined file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        combined.to_csv(output_path, index=False)

    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

    logger.info(f"Saved to: {output_path}")
    return True


def main(config: dict = None, dry_run: bool = False) -> bool:
    """Main entry point."""
    if config is None:
        config = load_config()

    logger = get_logger(__name__)

    # Get TR source config
    tr_config = config["sources"]["tr"]
    output_path = Path(config["paths"]["data"]["source"]) / "tr_raw.csv"

    # Check if local path is specified
    local_path = tr_config.get("local_path")
    if local_path and Path(local_path).exists():
        logger.info(f"Using local TR file: {local_path}")
        if dry_run:
            logger.info("[DRY RUN] Would copy local file")
            return True
        # Copy local file
        import shutil
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(local_path, output_path)
        logger.info(f"Copied to: {output_path}")
        return True

    # Need to download
    url = tr_config.get("download_url")
    target_file = tr_config.get("source_file", "csv/bgnt.csv")

    if not url:
        logger.error("No download URL configured and no local file found")
        logger.error("Set sources.tr.local_path or sources.tr.download_url in config.yaml")
        return False

    if dry_run:
        logger.info(f"[DRY RUN] Would download from: {url}")
        logger.info(f"[DRY RUN] Would extract: {target_file}")
        logger.info(f"[DRY RUN] Would save to: {output_path}")
        return True

    # Check if already exists
    if output_path.exists():
        logger.info(f"TR data already exists: {output_path}")
        logger.info("Delete the file to re-download")
        return True

    return download_and_extract(url, target_file, output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    with ScriptLogger("p1_04_acquire_tr") as logger:
        config = load_config()
        success = main(config, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
