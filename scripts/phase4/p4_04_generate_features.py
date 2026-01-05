#!/usr/bin/env python3
"""
Script: p4_04_generate_features.py
Phase: 4 - Compilation
Purpose: Generate Text-Fabric dataset using TF's API

Input:  data/intermediate/tr_complete.parquet, data/intermediate/tr_containers.parquet
Output: data/output/tf/ directory with .tf files

Usage:
    python -m scripts.phase4.p4_04_generate_features
    python -m scripts.phase4.p4_04_generate_features --dry-run
"""

import argparse
import sys
from pathlib import Path
from collections import OrderedDict

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils.config import load_config
from scripts.utils.logging import ScriptLogger, get_logger


def build_tf_data(complete_df, containers_df, config: dict) -> tuple:
    """
    Build data structures for Text-Fabric dataset creation.

    Returns:
        Tuple of (node_features, edge_features, otext_config)
    """
    import pandas as pd

    logger = get_logger(__name__)

    # Sort words by position to ensure sequential slot assignment
    complete_df = complete_df.sort_values(
        ["book", "chapter", "verse", "word_rank"]
    ).reset_index(drop=True)

    # Create slot mapping: original word_id -> sequential slot number
    slot_map = {row["word_id"]: idx + 1 for idx, row in complete_df.iterrows()}

    # Node features dictionary: feature_name -> {node_id: value}
    node_features = {}

    # Word features
    word_feature_names = ["word", "lemma", "sp", "function", "case", "gn", "nu",
                          "ps", "tense", "voice", "mood", "gloss", "source"]

    for feat in word_feature_names:
        if feat in complete_df.columns:
            node_features[feat] = {}
            for _, row in complete_df.iterrows():
                slot = slot_map[row["word_id"]]
                val = row.get(feat)
                if val is not None and str(val) != "nan" and val != "":
                    node_features[feat][slot] = str(val)

    logger.info(f"Built {len(node_features)} word features")

    # Build oslots: container_node -> set of slots
    oslots = {}
    max_slot = len(complete_df)

    # Renumber container nodes starting after slots
    container_node_map = {}  # old node_id -> new node_id
    next_node = max_slot + 1

    # Process containers by type (verse, chapter, book) for proper ordering
    for otype in ["verse", "chapter", "book"]:
        type_containers = containers_df[containers_df["otype"] == otype]
        for _, container in type_containers.iterrows():
            old_id = container["node_id"]
            new_id = next_node
            container_node_map[old_id] = new_id
            next_node += 1

            # Map slot range
            first_slot = slot_map.get(container["first_slot"], container["first_slot"])
            last_slot = slot_map.get(container["last_slot"], container["last_slot"])
            oslots[new_id] = set(range(first_slot, last_slot + 1))

    # Add container features (book name, chapter number, verse number)
    node_features["book@verse"] = {}
    node_features["chapter@verse"] = {}
    node_features["verse@verse"] = {}
    node_features["book@chapter"] = {}
    node_features["chapter@chapter"] = {}
    node_features["book@book"] = {}

    for _, container in containers_df.iterrows():
        new_id = container_node_map[container["node_id"]]
        otype = container["otype"]

        if otype == "verse":
            node_features["book@verse"][new_id] = str(container["book"])
            node_features["chapter@verse"][new_id] = int(container["chapter"])
            node_features["verse@verse"][new_id] = int(container["verse"])
        elif otype == "chapter":
            node_features["book@chapter"][new_id] = str(container["book"])
            node_features["chapter@chapter"][new_id] = int(container["chapter"])
        elif otype == "book":
            node_features["book@book"][new_id] = str(container["name"])

    logger.info(f"Built oslots for {len(oslots)} containers")

    # Build otext configuration
    otext = {
        "fmt:text-orig-full": "{word} ",
        "sectionTypes": "book,chapter,verse",
        "sectionFeatures": "book@book,chapter@chapter,verse@verse",
    }

    return node_features, oslots, otext, max_slot


def write_tf_dataset(node_features, oslots, otext, max_slot, output_dir: Path, config: dict):
    """Write Text-Fabric dataset files."""
    from tf.fabric import Fabric
    from tf.convert.walker import CV

    logger = get_logger(__name__)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Build metadata
    metadata = {
        "": {
            "name": config["tf_output"]["dataset_name"],
            "version": config["tf_output"]["version"],
            "language": config["tf_output"]["language"],
            "description": config["project"]["description"],
            "source": "TR via graft-and-patch from N1904",
        },
        "otext": otext,
    }

    # Add feature metadata
    for feat in node_features:
        if "@" in feat:
            base_feat = feat.split("@")[0]
            metadata[feat] = {"description": f"{base_feat} feature for section nodes"}
        else:
            metadata[feat] = {"description": f"{feat} word feature"}

    # Use TF's walker to create the dataset
    TF = Fabric(locations=str(output_dir), silent="deep")

    # Prepare node feature data in TF format
    # TF expects: {node: value} for each feature
    feature_data = node_features

    # Add otype feature
    otype_data = {}
    for slot in range(1, max_slot + 1):
        otype_data[slot] = "word"
    for node, slots in oslots.items():
        # Determine otype based on slot count and position
        if node <= max_slot + len([n for n in oslots if len(oslots[n]) < 100]):
            # This is simplified - in reality we track otype separately
            pass

    logger.info(f"Writing TF dataset to: {output_dir}")

    # Write features using TF API
    # First, let's write a simple version using direct file writing

    # Write otext.tf
    otext_path = output_dir / "otext.tf"
    with open(otext_path, "w", encoding="utf-8") as f:
        f.write("@config\n")
        for key, value in otext.items():
            f.write(f"@{key}={value}\n")

    # Write each node feature
    for feat_name, feat_data in node_features.items():
        if not feat_data:
            continue

        # Clean feature name for filename
        file_name = feat_name.replace("@", "_at_") + ".tf"
        feat_path = output_dir / file_name

        with open(feat_path, "w", encoding="utf-8") as f:
            # Write metadata
            f.write(f"@node\n")
            if feat_name in metadata:
                for key, value in metadata[feat_name].items():
                    f.write(f"@{key}={value}\n")
            f.write("\n")

            # Write data - sorted by node ID
            for node in sorted(feat_data.keys()):
                value = feat_data[node]
                # Escape special characters
                if isinstance(value, str):
                    value = value.replace("\\", "\\\\").replace("\n", "\\n").replace("\t", "\\t")
                f.write(f"{node}\t{value}\n")

        logger.info(f"  Wrote {feat_name}: {len(feat_data)} values")

    # Write oslots.tf (slot containment)
    oslots_path = output_dir / "oslots.tf"
    with open(oslots_path, "w", encoding="utf-8") as f:
        f.write("@edge\n")
        f.write("@description=slot containment for non-slot nodes\n")
        f.write("\n")

        for node in sorted(oslots.keys()):
            slots = sorted(oslots[node])
            # Write as ranges for efficiency
            slot_str = ",".join(str(s) for s in slots)
            if len(slots) > 2:
                # Use range notation if contiguous
                if slots == list(range(slots[0], slots[-1] + 1)):
                    slot_str = f"{slots[0]}-{slots[-1]}"
            f.write(f"{node}\t{slot_str}\n")

    logger.info(f"  Wrote oslots: {len(oslots)} containers")

    return True


def main(config: dict = None, dry_run: bool = False) -> bool:
    """Main entry point."""
    if config is None:
        config = load_config()

    logger = get_logger(__name__)

    complete_path = Path(config["paths"]["data"]["intermediate"]) / "tr_complete.parquet"
    containers_path = Path(config["paths"]["data"]["intermediate"]) / "tr_containers.parquet"
    output_dir = Path(config["paths"]["data"]["output"]) / "tf"

    if dry_run:
        logger.info("[DRY RUN] Would generate TF feature files")
        logger.info(f"[DRY RUN] Output: {output_dir}")
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

    logger.info(f"Words: {len(complete_df)}")
    logger.info(f"Containers: {len(containers_df)}")

    # Build TF data structures
    logger.info("Building TF data structures...")
    node_features, oslots, otext, max_slot = build_tf_data(
        complete_df, containers_df, config
    )

    # Write TF dataset
    logger.info("Writing TF dataset...")
    success = write_tf_dataset(node_features, oslots, otext, max_slot, output_dir, config)

    if success:
        logger.info(f"\nTF dataset written to: {output_dir}")

    return success


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    with ScriptLogger("p4_04_generate_features") as logger:
        config = load_config()
        success = main(config, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
