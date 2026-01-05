#!/usr/bin/env python3
"""
Script: p2_06_transplant_syntax.py
Phase: 2 - Alignment
Purpose: Copy syntax features from N1904 to aligned TR words

Input:  data/intermediate/alignment_map.parquet, data/intermediate/n1904_words.parquet,
        data/intermediate/id_translation.parquet, data/intermediate/tr_words.parquet
Output: data/intermediate/tr_transplanted.parquet

Usage:
    python -m scripts.phase2.p2_06_transplant_syntax
    python -m scripts.phase2.p2_06_transplant_syntax --dry-run
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils.config import load_config
from scripts.utils.logging import ScriptLogger, get_logger


def transplant_syntax(tr_df, n1904_df, alignment_df, id_translation_df, config: dict):
    """
    Transplant syntax features from N1904 to TR for aligned words.

    Args:
        tr_df: TR words DataFrame
        n1904_df: N1904 words DataFrame with syntax features
        alignment_df: Alignment map DataFrame
        id_translation_df: ID translation DataFrame
        config: Pipeline config

    Returns:
        TR DataFrame with transplanted syntax features
    """
    import pandas as pd

    logger = get_logger(__name__)

    # Features to transplant from N1904
    syntax_features = ["lemma", "sp", "case", "tense", "voice", "mood",
                       "function", "role", "parent", "clause_id", "phrase_id", "gloss"]

    # Start with TR words
    result = tr_df.copy()

    # Initialize syntax columns
    for feat in syntax_features:
        if feat not in result.columns:
            result[feat] = None

    # Add alignment status
    result["aligned"] = False
    result["n1904_node_id"] = None

    # Create lookup from alignment
    alignment_lookup = alignment_df.set_index("tr_word_id")["n1904_node_id"].to_dict()

    # Create N1904 feature lookup
    n1904_lookup = n1904_df.set_index("node_id").to_dict("index")

    # Create ID translation lookup
    id_trans_lookup = id_translation_df.set_index("n1904_id")["tr_id"].to_dict()

    logger.info("Transplanting syntax features...")
    transplant_count = 0

    for idx, row in result.iterrows():
        word_id = row["word_id"]

        if word_id in alignment_lookup:
            n1904_id = alignment_lookup[word_id]

            if n1904_id in n1904_lookup:
                n1904_word = n1904_lookup[n1904_id]

                # Copy features
                for feat in syntax_features:
                    if feat in n1904_word:
                        value = n1904_word[feat]

                        # Translate parent ID if it's a node reference
                        if feat == "parent" and value is not None:
                            value = id_trans_lookup.get(value, value)
                        elif feat in ["clause_id", "phrase_id"] and value is not None:
                            value = id_trans_lookup.get(value, value)

                        result.at[idx, feat] = value

                result.at[idx, "aligned"] = True
                result.at[idx, "n1904_node_id"] = n1904_id
                transplant_count += 1

    logger.info(f"Transplanted features for {transplant_count:,} words")
    logger.info(f"Unaligned words: {len(result) - transplant_count:,}")

    return result


def main(config: dict = None, dry_run: bool = False) -> bool:
    """Main entry point."""
    if config is None:
        config = load_config()

    logger = get_logger(__name__)

    tr_path = Path(config["paths"]["data"]["intermediate"]) / "tr_words.parquet"
    n1904_path = Path(config["paths"]["data"]["intermediate"]) / "n1904_words.parquet"
    alignment_path = Path(config["paths"]["data"]["intermediate"]) / "alignment_map.parquet"
    id_trans_path = Path(config["paths"]["data"]["intermediate"]) / "id_translation.parquet"
    output_path = Path(config["paths"]["data"]["intermediate"]) / "tr_transplanted.parquet"

    if dry_run:
        logger.info("[DRY RUN] Would transplant syntax features")
        return True

    import pandas as pd

    # Check inputs
    for path in [tr_path, n1904_path, alignment_path, id_trans_path]:
        if not path.exists():
            logger.error(f"Input not found: {path}")
            return False

    # Load data
    logger.info("Loading data...")
    tr_df = pd.read_parquet(tr_path)
    n1904_df = pd.read_parquet(n1904_path)
    alignment_df = pd.read_parquet(alignment_path)
    id_translation_df = pd.read_parquet(id_trans_path)

    logger.info(f"TR words: {len(tr_df):,}")
    logger.info(f"N1904 words: {len(n1904_df):,}")
    logger.info(f"Alignments: {len(alignment_df):,}")
    logger.info(f"ID translations: {len(id_translation_df):,}")

    # Transplant syntax
    result = transplant_syntax(tr_df, n1904_df, alignment_df, id_translation_df, config)

    # Validate - check for broken parent references
    valid_ids = set(result["word_id"].tolist())
    # Add container IDs from translation table
    container_ids = id_translation_df[id_translation_df["node_type"] != "word"]["tr_id"].tolist()
    valid_ids.update(container_ids)

    broken_refs = 0
    for parent_id in result["parent"].dropna():
        if parent_id not in valid_ids and parent_id != 0:
            broken_refs += 1

    if broken_refs > 0:
        logger.warning(f"Found {broken_refs:,} potentially broken parent references")
    else:
        logger.info("No broken parent references detected")

    # Save
    result.to_parquet(output_path, index=False)
    logger.info(f"Saved to: {output_path}")

    # Summary
    aligned_count = result["aligned"].sum()
    logger.info(f"\n{'='*50}")
    logger.info("TRANSPLANT COMPLETE")
    logger.info(f"{'='*50}")
    logger.info(f"Total words: {len(result):,}")
    logger.info(f"With syntax: {aligned_count:,} ({aligned_count/len(result)*100:.1f}%)")
    logger.info(f"Gaps (need Phase 3): {len(result) - aligned_count:,}")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    with ScriptLogger("p2_06_transplant_syntax") as logger:
        config = load_config()
        success = main(config, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
