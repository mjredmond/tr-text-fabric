#!/usr/bin/env python3
"""
Script: p2_01_extract_n1904.py
Phase: 2 - Alignment
Purpose: Extract all N1904 words with their syntax features into DataFrame

Input:  N1904 Text-Fabric dataset
Output: data/intermediate/n1904_words.parquet

Usage:
    python -m scripts.phase2.p2_01_extract_n1904
    python -m scripts.phase2.p2_01_extract_n1904 --dry-run
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils.config import load_config
from scripts.utils.logging import ScriptLogger, get_logger
from scripts.utils.tf_helpers import load_n1904


def normalize_greek_word(word: str) -> str:
    """
    Normalize a Greek word by stripping whitespace and punctuation.

    Args:
        word: Raw word text from Text-Fabric

    Returns:
        Cleaned word with only Greek characters
    """
    import re
    if not word:
        return ""
    # Strip whitespace
    word = word.strip()
    # Remove trailing punctuation (keep only Greek characters)
    # Greek Unicode ranges: \u0370-\u03FF (Greek and Coptic), \u1F00-\u1FFF (Extended Greek)
    match = re.match(r'^[\u0370-\u03FF\u1F00-\u1FFF]+', word)
    if match:
        return match.group(0)
    return word


def extract_words_with_features(api: Any, config: dict) -> "pd.DataFrame":
    """
    Extract all words from N1904 with their features.

    Args:
        api: Text-Fabric API
        config: Pipeline config

    Returns:
        DataFrame with all word data
    """
    import pandas as pd
    from tqdm import tqdm

    logger = get_logger(__name__)

    # Features to extract from config
    word_features = config["tf_output"]["word_features"]
    syntax_features = config["tf_output"]["syntax_features"]
    all_features = word_features + syntax_features

    logger.info(f"Extracting features: {all_features}")

    records = []
    words = list(api.F.otype.s("word"))
    logger.info(f"Processing {len(words):,} words...")

    for word_node in tqdm(words, desc="Extracting words"):
        # Get section info
        section = api.T.sectionFromNode(word_node)
        if not section or len(section) < 3:
            continue

        book, chapter, verse = section

        # Get the surface word form and normalize it
        word_text = api.T.text(word_node)
        word_normalized = normalize_greek_word(word_text)

        record = {
            "node_id": word_node,
            "book": book,
            "chapter": chapter,
            "verse": verse,
            "word": word_normalized,  # Normalized surface form
            "word_raw": word_text,    # Keep raw form for reference
        }

        # Get word rank within verse
        verse_node = api.L.u(word_node, otype="verse")
        if verse_node:
            verse_words = list(api.L.d(verse_node[0], otype="word"))
            record["word_rank"] = verse_words.index(word_node) + 1

        # Extract each feature
        for feature_name in all_features:
            feature = getattr(api.F, feature_name, None)
            if feature:
                try:
                    record[feature_name] = feature.v(word_node)
                except Exception:
                    record[feature_name] = None

        # Get parent relationship if exists
        if hasattr(api.E, "parent"):
            parents = api.E.parent.t(word_node)
            record["parent"] = parents[0] if parents else None

        # Get containing clause/phrase
        clauses = api.L.u(word_node, otype="clause")
        phrases = api.L.u(word_node, otype="phrase")

        record["clause_id"] = clauses[0] if clauses else None
        record["phrase_id"] = phrases[0] if phrases else None

        records.append(record)

    df = pd.DataFrame(records)
    return df


def main(config: dict = None, dry_run: bool = False) -> bool:
    """Main entry point."""
    if config is None:
        config = load_config()

    logger = get_logger(__name__)
    output_path = Path(config["paths"]["data"]["intermediate"]) / "n1904_words.parquet"

    if dry_run:
        logger.info("[DRY RUN] Would extract N1904 words with features")
        logger.info(f"[DRY RUN] Would write to: {output_path}")
        return True

    try:
        import pandas as pd
    except ImportError:
        logger.error("pandas not installed")
        return False

    # Load N1904
    logger.info("Loading N1904...")
    try:
        A = load_n1904(config)
        api = A.api
    except Exception as e:
        logger.error(f"Failed to load N1904: {e}")
        return False

    # Extract words
    df = extract_words_with_features(api, config)

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)

    logger.info(f"Extracted {len(df):,} words")
    logger.info(f"Columns: {list(df.columns)}")
    logger.info(f"Saved to: {output_path}")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    with ScriptLogger("p2_01_extract_n1904") as logger:
        config = load_config()
        success = main(config, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
