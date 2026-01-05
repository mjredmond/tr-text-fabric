#!/usr/bin/env python3
"""
Script: p2_05_build_id_map.py
Phase: 2 - Alignment
Purpose: Create node ID translation table (N1904 -> TR)

Input:  data/intermediate/alignment_map.parquet
Output: data/intermediate/id_translation.parquet

Usage:
    python -m scripts.phase2.p2_05_build_id_map
    python -m scripts.phase2.p2_05_build_id_map --dry-run
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils.config import load_config
from scripts.utils.logging import ScriptLogger, get_logger


def build_id_translation(alignment_df, n1904_df) -> "pd.DataFrame":
    """
    Build ID translation table from N1904 node IDs to TR word IDs.

    Args:
        alignment_df: Alignment map DataFrame
        n1904_df: N1904 words DataFrame with clause/phrase IDs

    Returns:
        DataFrame with ID mappings
    """
    import pandas as pd

    logger = get_logger(__name__)

    # Start with word-level mappings
    word_map = alignment_df[["n1904_node_id", "tr_word_id"]].copy()
    word_map = word_map.rename(columns={
        "n1904_node_id": "n1904_id",
        "tr_word_id": "tr_id"
    })
    word_map["node_type"] = "word"

    logger.info(f"Word mappings: {len(word_map):,}")

    # Get unique clause and phrase mappings from aligned words
    # For each aligned word, we know its clause_id and phrase_id in N1904
    # We'll assign new TR IDs to these containers

    # Merge alignment with N1904 to get container IDs
    aligned_with_containers = alignment_df.merge(
        n1904_df[["node_id", "clause_id", "phrase_id"]],
        left_on="n1904_node_id",
        right_on="node_id",
        how="left"
    )

    # Create clause ID mapping
    # Each unique N1904 clause_id gets a new TR clause ID
    unique_clauses = aligned_with_containers["clause_id"].dropna().unique()
    clause_map = pd.DataFrame({
        "n1904_id": unique_clauses,
        "tr_id": range(1000000, 1000000 + len(unique_clauses)),  # Offset to avoid word ID collision
        "node_type": "clause"
    })
    logger.info(f"Clause mappings: {len(clause_map):,}")

    # Create phrase ID mapping
    unique_phrases = aligned_with_containers["phrase_id"].dropna().unique()
    phrase_map = pd.DataFrame({
        "n1904_id": unique_phrases,
        "tr_id": range(2000000, 2000000 + len(unique_phrases)),  # Different offset
        "node_type": "phrase"
    })
    logger.info(f"Phrase mappings: {len(phrase_map):,}")

    # Combine all mappings
    id_translation = pd.concat([word_map, clause_map, phrase_map], ignore_index=True)

    # Ensure IDs are integers
    id_translation["n1904_id"] = id_translation["n1904_id"].astype("Int64")
    id_translation["tr_id"] = id_translation["tr_id"].astype("Int64")

    return id_translation


def main(config: dict = None, dry_run: bool = False) -> bool:
    """Main entry point."""
    if config is None:
        config = load_config()

    logger = get_logger(__name__)

    alignment_path = Path(config["paths"]["data"]["intermediate"]) / "alignment_map.parquet"
    n1904_path = Path(config["paths"]["data"]["intermediate"]) / "n1904_words.parquet"
    output_path = Path(config["paths"]["data"]["intermediate"]) / "id_translation.parquet"

    if dry_run:
        logger.info("[DRY RUN] Would build ID translation table")
        return True

    import pandas as pd

    # Check inputs
    if not alignment_path.exists():
        logger.error(f"Alignment map not found: {alignment_path}")
        return False

    if not n1904_path.exists():
        logger.error(f"N1904 data not found: {n1904_path}")
        return False

    # Load data
    logger.info("Loading alignment map...")
    alignment_df = pd.read_parquet(alignment_path)
    logger.info(f"Alignments: {len(alignment_df):,}")

    logger.info("Loading N1904 data...")
    n1904_df = pd.read_parquet(n1904_path)

    # Build translation table
    logger.info("Building ID translation table...")
    id_translation = build_id_translation(alignment_df, n1904_df)

    # Save
    id_translation.to_parquet(output_path, index=False)
    logger.info(f"Saved {len(id_translation):,} mappings to {output_path}")

    # Summary by type
    type_counts = id_translation["node_type"].value_counts()
    for node_type, count in type_counts.items():
        logger.info(f"  {node_type}: {count:,}")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    with ScriptLogger("p2_05_build_id_map") as logger:
        config = load_config()
        success = main(config, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
