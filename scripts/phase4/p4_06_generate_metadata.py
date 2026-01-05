#!/usr/bin/env python3
"""
Script: p4_06_generate_metadata
Phase: 4 - Compilation
Purpose: Write TF metadata files (otext, otype)

Input:  tr_complete.parquet, tr_containers.parquet, tf_config.json
Output: data/output/tf/otext.tf, data/output/tf/otype.tf

Usage:
    python -m scripts.phase4.p4_06_generate_metadata
    python -m scripts.phase4.p4_06_generate_metadata --dry-run
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils.config import load_config
from scripts.utils.logging import ScriptLogger, get_logger


def write_otext(output_path: Path, config: dict):
    """
    Write otext.tf configuration file.

    The otext feature defines:
    - Section structure (book, chapter, verse)
    - Text display formats
    - Section feature names
    """
    logger = get_logger(__name__)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("@config\n")
        f.write(f"@name={config['tf_output']['dataset_name']}\n")
        f.write(f"@version={config['tf_output']['version']}\n")
        f.write(f"@language={config['tf_output']['language']}\n")
        f.write("@description=Textus Receptus with syntax transplanted from N1904\n")
        f.write("@source=TR via graft-and-patch from N1904\n")
        f.write("\n")
        f.write("@fmt:text-orig-full={word} \n")
        f.write("@sectionTypes=book,chapter,verse\n")
        f.write("@sectionFeatures=book@book,chapter@chapter,verse@verse\n")

    logger.info(f"Wrote otext.tf to {output_path}")


def write_otype(output_path: Path, complete_df, containers_df):
    """
    Write otype.tf feature file.

    The otype feature assigns a node type to each node:
    - Slots 1..max_word are type 'word'
    - Container nodes are 'verse', 'chapter', or 'book'
    """
    logger = get_logger(__name__)

    # Sort complete_df to get correct slot ordering
    complete_df = complete_df.sort_values(
        ["book", "chapter", "verse", "word_rank"]
    ).reset_index(drop=True)

    max_slot = len(complete_df)

    # Build container node mapping
    container_node_map = {}
    next_node = max_slot + 1

    for otype in ["verse", "chapter", "book"]:
        type_containers = containers_df[containers_df["otype"] == otype]
        for _, container in type_containers.iterrows():
            old_id = container["node_id"]
            container_node_map[old_id] = next_node
            next_node += 1

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("@node\n")
        f.write("@description=node type assignment\n")
        f.write("\n")

        # Write slot otypes (all words)
        for slot in range(1, max_slot + 1):
            f.write(f"{slot}\tword\n")

        # Write container otypes
        for otype in ["verse", "chapter", "book"]:
            type_containers = containers_df[containers_df["otype"] == otype]
            for _, container in type_containers.iterrows():
                new_id = container_node_map[container["node_id"]]
                f.write(f"{new_id}\t{otype}\n")

    total_nodes = max_slot + len(container_node_map)
    logger.info(f"Wrote otype.tf with {total_nodes} nodes to {output_path}")

    return total_nodes


def main(config: dict = None, dry_run: bool = False) -> bool:
    """Main entry point."""
    if config is None:
        config = load_config()

    logger = get_logger(__name__)

    intermediate_dir = Path(config["paths"]["data"]["intermediate"])
    complete_path = intermediate_dir / "tr_complete.parquet"
    containers_path = intermediate_dir / "tr_containers.parquet"
    output_dir = Path(config["paths"]["data"]["output"]) / "tf"

    if dry_run:
        logger.info("[DRY RUN] Would generate TF metadata files")
        logger.info(f"[DRY RUN] Output: {output_dir}/otext.tf, otype.tf")
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

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write metadata files
    logger.info("Writing metadata files...")
    write_otext(output_dir / "otext.tf", config)
    total_nodes = write_otype(output_dir / "otype.tf", complete_df, containers_df)

    logger.info(f"\nMetadata Summary:")
    logger.info("-" * 40)
    logger.info(f"Total nodes: {total_nodes}")
    logger.info(f"  Words: {len(complete_df)}")
    logger.info(f"  Containers: {len(containers_df)}")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    with ScriptLogger("p4_06_generate_metadata") as logger:
        config = load_config()
        success = main(config, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
