#!/usr/bin/env python3
"""
Script: p3_05_convert_parses.py
Phase: 3 - Delta Patching
Purpose: Convert Stanza parses to N1904-compatible format and merge with gap words

Input:  data/intermediate/gap_parses.parquet, data/intermediate/gap_spans.parquet,
        data/intermediate/label_map.json, data/intermediate/gaps.csv
Output: data/intermediate/gap_syntax.parquet

Usage:
    python -m scripts.phase3.p3_05_convert_parses
    python -m scripts.phase3.p3_05_convert_parses --dry-run
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils.config import load_config
from scripts.utils.logging import ScriptLogger, get_logger


def load_label_map(config: dict) -> Dict:
    """Load UD to N1904 label mapping."""
    map_path = Path(config["paths"]["data"]["intermediate"]) / "label_map.json"
    with open(map_path, "r", encoding="utf-8") as f:
        return json.load(f)


def convert_deprel(ud_deprel: str, label_map: Dict) -> str:
    """Convert UD dependency relation to N1904 function label."""
    deprel_map = label_map.get("deprel", {})
    return deprel_map.get(ud_deprel, ud_deprel)  # Fallback to original


def convert_pos(ud_pos: str, label_map: Dict) -> str:
    """Convert UD POS tag to N1904 part of speech."""
    pos_map = label_map.get("pos", {})
    return pos_map.get(ud_pos, ud_pos.lower())  # Fallback to lowercase


def extract_morphology(feats: str) -> Dict[str, str]:
    """
    Extract morphological features from Stanza feats string.

    Args:
        feats: Stanza feature string like "Case=Nom|Gender=Masc|Number=Sing"

    Returns:
        Dict of morphological features
    """
    if not feats or feats == "_":
        return {}

    morph = {}
    for feat in feats.split("|"):
        if "=" in feat:
            key, value = feat.split("=", 1)
            # Map to N1904 abbreviations
            if key == "Case":
                morph["case"] = value[:3].lower()  # Nom -> nom
            elif key == "Gender":
                morph["gn"] = value[0].lower()  # Masc -> m
            elif key == "Number":
                morph["nu"] = value[0].lower()  # Sing -> s
            elif key == "Person":
                morph["ps"] = value  # 1, 2, 3
            elif key == "Tense":
                morph["tense"] = value[:4].lower()  # Present -> pres
            elif key == "Voice":
                morph["voice"] = value[:3].lower()  # Active -> act
            elif key == "Mood":
                morph["mood"] = value[:3].lower()  # Indicative -> ind

    return morph


def align_parses_to_gaps(parses_df, spans_df, gaps_df, label_map: Dict) -> "pd.DataFrame":
    """
    Align Stanza parses back to original gap word IDs.

    This is tricky because Stanza may tokenize differently than the TR source.
    We use a best-effort positional alignment.

    Args:
        parses_df: Stanza parse output
        spans_df: Gap span metadata with word_ids
        gaps_df: Original gap words with word_id
        label_map: UD to N1904 mapping

    Returns:
        DataFrame of gap syntax ready for merging
    """
    import pandas as pd
    import ast

    logger = get_logger(__name__)

    # Convert word_ids from various representations to list
    def parse_word_ids(x):
        import numpy as np
        if isinstance(x, list):
            return x
        if isinstance(x, np.ndarray):
            return x.tolist()
        try:
            return ast.literal_eval(str(x))
        except:
            return []

    spans_df = spans_df.copy()
    spans_df["word_ids"] = spans_df["word_ids"].apply(parse_word_ids)

    syntax_records = []

    # Process each span
    for _, span in spans_df.iterrows():
        span_id = span["span_id"]
        word_ids = span["word_ids"]

        # Get parses for this span
        span_parses = parses_df[parses_df["span_id"] == span_id].sort_values("word_idx")

        if len(span_parses) == 0:
            logger.warning(f"No parses for span {span_id}")
            continue

        # Align by position (best effort)
        # If parse count matches gap count, align 1:1
        # Otherwise, distribute as best we can
        parse_list = span_parses.to_dict("records")

        for i, word_id in enumerate(word_ids):
            if i < len(parse_list):
                parse = parse_list[i]

                # Convert labels
                function = convert_deprel(parse["deprel"], label_map)
                sp = convert_pos(parse["upos"], label_map)

                # Extract morphology
                morph = extract_morphology(parse.get("feats", ""))

                # Calculate parent word_id
                head_idx = parse.get("head_in_span", -1)
                if head_idx >= 0 and head_idx < len(word_ids):
                    parent_word_id = word_ids[head_idx]
                else:
                    parent_word_id = None  # Root or external

                syntax_records.append({
                    "word_id": word_id,
                    "lemma": parse["lemma"],
                    "sp": sp,
                    "function": function,
                    "parent": parent_word_id,
                    "stanza_deprel": parse["deprel"],
                    "stanza_upos": parse["upos"],
                    **morph,
                })
            else:
                # More gap words than parses - use minimal info
                syntax_records.append({
                    "word_id": word_id,
                    "lemma": None,
                    "sp": None,
                    "function": "Unknown",
                    "parent": None,
                })

    return pd.DataFrame(syntax_records)


def main(config: dict = None, dry_run: bool = False) -> bool:
    """Main entry point."""
    if config is None:
        config = load_config()

    logger = get_logger(__name__)

    parses_path = Path(config["paths"]["data"]["intermediate"]) / "gap_parses.parquet"
    spans_path = Path(config["paths"]["data"]["intermediate"]) / "gap_spans.parquet"
    gaps_path = Path(config["paths"]["data"]["intermediate"]) / "gaps.csv"
    label_map_path = Path(config["paths"]["data"]["intermediate"]) / "label_map.json"
    output_path = Path(config["paths"]["data"]["intermediate"]) / "gap_syntax.parquet"

    if dry_run:
        logger.info("[DRY RUN] Would convert Stanza parses to N1904 format")
        return True

    import pandas as pd

    # Check inputs
    for path in [parses_path, spans_path, gaps_path, label_map_path]:
        if not path.exists():
            logger.error(f"Input not found: {path}")
            return False

    # Load data
    logger.info("Loading data...")
    parses_df = pd.read_parquet(parses_path)
    spans_df = pd.read_parquet(spans_path)
    gaps_df = pd.read_csv(gaps_path)
    label_map = load_label_map(config)

    logger.info(f"Parses: {len(parses_df)}")
    logger.info(f"Spans: {len(spans_df)}")
    logger.info(f"Gap words: {len(gaps_df)}")

    # Convert and align
    logger.info("Aligning parses to gap words...")
    syntax_df = align_parses_to_gaps(parses_df, spans_df, gaps_df, label_map)

    logger.info(f"Generated syntax for {len(syntax_df)} words")

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    syntax_df.to_parquet(output_path, index=False)
    logger.info(f"Saved to: {output_path}")

    # Summary
    logger.info("\nConversion Summary:")
    logger.info("-" * 40)
    logger.info(f"Words with syntax: {len(syntax_df)}")
    if len(syntax_df) > 0:
        logger.info(f"\nFunction distribution:")
        func_counts = syntax_df["function"].value_counts().head(10)
        for func, count in func_counts.items():
            logger.info(f"  {func}: {count}")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    with ScriptLogger("p3_05_convert_parses") as logger:
        config = load_config()
        success = main(config, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
