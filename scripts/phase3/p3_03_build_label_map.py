#!/usr/bin/env python3
"""
Script: p3_03_build_label_map.py
Phase: 3 - Delta Patching
Purpose: Create UD to N1904 label mapping ("Rosetta Stone")

Input:  config.yaml (label_mapping section)
Output: data/intermediate/label_map.json

Usage:
    python -m scripts.phase3.p3_03_build_label_map
    python -m scripts.phase3.p3_03_build_label_map --dry-run
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils.config import load_config
from scripts.utils.logging import ScriptLogger, get_logger


# Complete UD to N1904/Lowfat label mapping
# Based on Universal Dependencies annotation guidelines and N1904/OpenText schema
UD_TO_N1904_DEPREL = {
    # Core arguments
    "nsubj": "Subject",
    "nsubj:pass": "Subject",
    "nsubj:outer": "Subject",
    "obj": "Object",
    "iobj": "IndirectObject",
    "csubj": "Subject",
    "csubj:pass": "Subject",
    "ccomp": "Complement",
    "xcomp": "Complement",

    # Oblique arguments and adjuncts
    "obl": "Adjunct",
    "obl:agent": "Adjunct",
    "obl:arg": "Adjunct",
    "vocative": "Vocative",
    "expl": "Expletive",
    "dislocated": "Supplement",

    # Nominal dependents
    "nmod": "Modifier",
    "appos": "Apposition",
    "nummod": "Modifier",

    # Clausal dependents
    "acl": "Modifier",
    "acl:relcl": "Modifier",
    "advcl": "Adjunct",

    # Modifier words
    "advmod": "Adverb",
    "amod": "Adjective",
    "discourse": "Discourse",

    # Function words
    "aux": "Auxiliary",
    "aux:pass": "Auxiliary",
    "cop": "Copula",
    "mark": "Subordinator",
    "det": "Determiner",
    "clf": "Classifier",
    "case": "CaseMarker",

    # Coordination
    "cc": "Conjunction",
    "conj": "Conjunct",

    # MWE and special
    "fixed": "Fixed",
    "flat": "Flat",
    "flat:name": "Flat",
    "compound": "Compound",
    "list": "List",
    "parataxis": "Parataxis",

    # Loose joining
    "orphan": "Orphan",
    "goeswith": "GoesWith",
    "reparandum": "Reparandum",

    # Special relations
    "punct": "Punctuation",
    "root": "Predicate",
    "dep": "Dependent",
}

# UD POS to N1904 part of speech mapping
UD_TO_N1904_POS = {
    "ADJ": "adj",
    "ADP": "prep",
    "ADV": "adv",
    "AUX": "verb",
    "CCONJ": "conj",
    "DET": "det",
    "INTJ": "intj",
    "NOUN": "noun",
    "NUM": "num",
    "PART": "ptcl",
    "PRON": "pron",
    "PROPN": "noun",
    "PUNCT": "punct",
    "SCONJ": "conj",
    "SYM": "sym",
    "VERB": "verb",
    "X": "x",
}


def build_label_map(config: dict) -> dict:
    """
    Build complete label mapping from UD to N1904 schema.

    Args:
        config: Pipeline config

    Returns:
        Complete label mapping dictionary
    """
    logger = get_logger(__name__)

    # Start with config-based mappings (if any)
    config_deprel = config.get("label_mapping", {}).get("deprel", {})

    # Merge with complete mapping (config takes precedence)
    deprel_map = UD_TO_N1904_DEPREL.copy()
    deprel_map.update(config_deprel)

    label_map = {
        "deprel": deprel_map,
        "pos": UD_TO_N1904_POS,
        "unmapped_strategy": "use_ud_label",  # Fallback for unmapped labels
        "version": "1.0",
        "description": "Universal Dependencies to N1904/Lowfat label mapping",
    }

    logger.info(f"Deprel mappings: {len(deprel_map)}")
    logger.info(f"POS mappings: {len(UD_TO_N1904_POS)}")

    return label_map


def validate_mapping(label_map: dict) -> bool:
    """Validate label mapping for completeness."""
    logger = get_logger(__name__)

    # Common UD deprels that must be mapped
    required_deprels = [
        "nsubj", "obj", "iobj", "obl", "advmod", "amod",
        "det", "case", "mark", "cc", "conj", "root"
    ]

    missing = []
    for deprel in required_deprels:
        if deprel not in label_map["deprel"]:
            missing.append(deprel)

    if missing:
        logger.warning(f"Missing required deprel mappings: {missing}")
        return False

    logger.info("Label mapping validation passed")
    return True


def main(config: dict = None, dry_run: bool = False) -> bool:
    """Main entry point."""
    if config is None:
        config = load_config()

    logger = get_logger(__name__)

    output_path = Path(config["paths"]["data"]["intermediate"]) / "label_map.json"

    if dry_run:
        logger.info("[DRY RUN] Would create UD to N1904 label mapping")
        logger.info(f"[DRY RUN] Output: {output_path}")
        return True

    # Build mapping
    label_map = build_label_map(config)

    # Validate
    if not validate_mapping(label_map):
        logger.error("Label mapping validation failed")
        return False

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(label_map, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved label map to: {output_path}")

    # Summary
    logger.info("\nLabel Mapping Summary:")
    logger.info("-" * 40)
    logger.info("Sample deprel mappings:")
    for ud, n1904 in list(label_map["deprel"].items())[:10]:
        logger.info(f"  {ud:15} -> {n1904}")
    logger.info("...")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    with ScriptLogger("p3_03_build_label_map") as logger:
        config = load_config()
        success = main(config, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
