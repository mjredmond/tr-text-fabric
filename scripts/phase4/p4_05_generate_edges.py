#!/usr/bin/env python3
"""
Script: p4_05_generate_edges
Phase: 4 - Compilation
Purpose: Write edge feature .tf files (parent relationships)

Input:  data/intermediate/tr_complete.parquet
Output: data/output/tf/parent.tf

Usage:
    python -m scripts.phase4.p4_05_generate_edges
    python -m scripts.phase4.p4_05_generate_edges --dry-run
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils.config import load_config
from scripts.utils.logging import ScriptLogger, get_logger


def build_parent_edges(complete_df) -> dict:
    """
    Build parent edge relationships from word data.

    In dependency parsing, each word has a parent (head) word,
    except for root words which have no parent.

    Returns:
        dict: {child_slot: parent_slot} mapping
    """
    logger = get_logger(__name__)

    # Sort and create slot mapping
    complete_df = complete_df.sort_values(
        ["book", "chapter", "verse", "word_rank"]
    ).reset_index(drop=True)

    slot_map = {row["word_id"]: idx + 1 for idx, row in complete_df.iterrows()}

    edges = {}
    root_count = 0
    missing_parent_count = 0

    for _, row in complete_df.iterrows():
        child_slot = slot_map[row["word_id"]]
        parent_id = row.get("parent")

        # Skip if no parent (root word or missing)
        if parent_id is None or str(parent_id) == "nan" or parent_id == "":
            root_count += 1
            continue

        # Handle numeric parent IDs
        try:
            parent_id = int(float(parent_id))
        except (ValueError, TypeError):
            missing_parent_count += 1
            continue

        # Map parent to slot
        if parent_id in slot_map:
            parent_slot = slot_map[parent_id]
            edges[child_slot] = parent_slot
        else:
            missing_parent_count += 1

    logger.info(f"Built {len(edges)} parent edges")
    logger.info(f"Root words (no parent): {root_count}")
    if missing_parent_count > 0:
        logger.warning(f"Missing parent references: {missing_parent_count}")

    return edges


def write_edge_file(edges: dict, output_path: Path):
    """Write edge feature to TF format file."""
    logger = get_logger(__name__)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("@edge\n")
        f.write("@description=parent (head) word in dependency tree\n")
        f.write("@valueType=int\n")
        f.write("\n")

        # Write edges sorted by child node
        for child in sorted(edges.keys()):
            parent = edges[child]
            f.write(f"{child}\t{parent}\n")

    logger.info(f"Wrote {len(edges)} edges to {output_path}")


def main(config: dict = None, dry_run: bool = False) -> bool:
    """Main entry point."""
    if config is None:
        config = load_config()

    logger = get_logger(__name__)

    complete_path = Path(config["paths"]["data"]["intermediate"]) / "tr_complete.parquet"
    output_dir = Path(config["paths"]["data"]["output"]) / "tf"
    parent_path = output_dir / "parent.tf"

    if dry_run:
        logger.info("[DRY RUN] Would generate edge feature files")
        logger.info(f"[DRY RUN] Output: {parent_path}")
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

    # Build parent edges
    logger.info("Building parent edges...")
    edges = build_parent_edges(complete_df)

    # Write edge file
    write_edge_file(edges, parent_path)

    logger.info(f"\nEdge Summary:")
    logger.info("-" * 40)
    logger.info(f"Parent edges written: {len(edges)}")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    with ScriptLogger("p4_05_generate_edges") as logger:
        config = load_config()
        success = main(config, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
