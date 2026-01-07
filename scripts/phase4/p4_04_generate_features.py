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

    # Word features - map internal names to N1904-compatible output names
    # Format: (output_name, input_column_name)
    word_feature_map = [
        ("unicode", "word"),      # N1904 uses 'unicode' for word text
        ("lemma", "lemma"),
        ("strong", "strong"),
        ("morph", "morph"),
        ("sp", "sp"),
        ("function", "function"),
        ("role", "role"),         # N1904-compatible syntactic role (s/o/io/v/adv)
        ("case", "case"),
        ("gender", "gn"),         # N1904 uses 'gender' not 'gn'
        ("number", "nu"),         # N1904 uses 'number' not 'nu'
        ("person", "ps"),         # N1904 uses 'person' not 'ps'
        ("tense", "tense"),
        ("voice", "voice"),
        ("mood", "mood"),
        ("gloss", "gloss"),
        ("source", "source"),
        # Text features (added for N1904 compatibility)
        ("translit", "translit"),         # Transliteration of word
        ("lemmatranslit", "lemmatranslit"), # Transliteration of lemma
        ("unaccent", "unaccent"),         # Word without diacritics
        ("after", "after"),               # Trailing punctuation/space
        ("ln", "ln"),                     # Louw-Nida semantic domains
        # Additional N1904-compatible features
        ("bookshort", "bookshort"),       # Abbreviated book name
        ("text", "text"),                 # Surface form (alias for unicode)
        ("normalized", "normalized"),     # Unicode NFC normalized
        ("trailer", "trailer"),           # Trailing material (alias for after)
        ("num", "num"),                   # Word position in verse
        ("ref", "ref"),                   # Reference string (MAT 1:1!1)
        ("id", "id"),                     # Unique word ID
        ("cls", "cls"),                   # Word class (noun/verb/etc)
    ]

    for output_name, input_col in word_feature_map:
        if input_col in complete_df.columns:
            node_features[output_name] = {}
            for _, row in complete_df.iterrows():
                slot = slot_map[row["word_id"]]
                val = row.get(input_col)
                if val is not None and str(val) != "nan" and val != "":
                    node_features[output_name][slot] = str(val)

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

    # Book name mapping: abbreviated -> full name (matching N1904)
    book_name_map = {
        "MAT": "Matthew", "MAR": "Mark", "LUK": "Luke", "JHN": "John",
        "ACT": "Acts", "ROM": "Romans", "1CO": "I_Corinthians", "2CO": "II_Corinthians",
        "GAL": "Galatians", "EPH": "Ephesians", "PHP": "Philippians", "COL": "Colossians",
        "1TH": "I_Thessalonians", "2TH": "II_Thessalonians", "1TI": "I_Timothy",
        "2TI": "II_Timothy", "TIT": "Titus", "PHM": "Philemon", "HEB": "Hebrews",
        "JAS": "James", "1PE": "I_Peter", "2PE": "II_Peter", "1JN": "I_John",
        "2JN": "II_John", "3JN": "III_John", "JUD": "Jude", "REV": "Revelation",
    }

    # Add section features for BOTH word nodes AND container nodes
    # This is required for TF's section navigation (T.nodeFromSection) to work
    node_features["book"] = {}
    node_features["chapter"] = {}
    node_features["verse"] = {}

    # Add section features to word nodes
    for _, row in complete_df.iterrows():
        slot = slot_map[row["word_id"]]
        book_abbrev = str(row["book"])
        book_full = book_name_map.get(book_abbrev, book_abbrev)
        node_features["book"][slot] = book_full
        node_features["chapter"][slot] = int(row["chapter"])
        node_features["verse"][slot] = int(row["verse"])

    # Add section features to container nodes
    for _, container in containers_df.iterrows():
        new_id = container_node_map[container["node_id"]]
        otype = container["otype"]

        if otype == "verse":
            node_features["verse"][new_id] = int(container["verse"])
        elif otype == "chapter":
            node_features["chapter"][new_id] = int(container["chapter"])
        elif otype == "book":
            book_abbrev = str(container["name"])
            book_full = book_name_map.get(book_abbrev, book_abbrev)
            node_features["book"][new_id] = book_full

    logger.info(f"Built oslots for {len(oslots)} containers")

    # Build otext configuration (matching N1904 structure)
    otext = {
        "fmt:text-orig-full": "{unicode} ",
        "sectionTypes": "book,chapter,verse",
        "sectionFeatures": "book,chapter,verse",
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

    # Add feature metadata with valueType
    # Section features (on all nodes for navigation)
    section_features = {
        "book": ("str", "book name (full)"),
        "chapter": ("int", "chapter number"),
        "verse": ("int", "verse number"),
    }

    for feat in node_features:
        if feat in section_features:
            value_type, desc = section_features[feat]
            metadata[feat] = {
                "description": desc,
                "valueType": value_type
            }
        else:
            metadata[feat] = {
                "description": f"{feat} word feature",
                "valueType": "str"
            }

    # Use TF's walker to create the dataset
    TF = Fabric(locations=str(output_dir), silent="deep")

    # Prepare node feature data in TF format
    # TF expects: {node: value} for each feature
    feature_data = node_features

    # Add otype feature
    otype_data = {}
    for slot in range(1, max_slot + 1):
        otype_data[slot] = "w"  # N1904-compatible
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

        # Feature name is now the filename directly
        file_name = feat_name + ".tf"
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
        f.write("@valueType=str\n")
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
