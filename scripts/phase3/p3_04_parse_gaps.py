#!/usr/bin/env python3
"""
Script: p3_04_parse_gaps.py
Phase: 3 - Delta Patching
Purpose: Run Stanza NLP on all gap spans to generate dependency parses

Input:  data/intermediate/gap_spans.parquet
Output: data/intermediate/gap_parses.parquet

Usage:
    python -m scripts.phase3.p3_04_parse_gaps
    python -m scripts.phase3.p3_04_parse_gaps --dry-run
"""

import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils.config import load_config
from scripts.utils.logging import ScriptLogger, get_logger


def parse_span_with_stanza(nlp, span_text: str, span_id: int) -> List[Dict[str, Any]]:
    """
    Parse a single span using Stanza.

    Args:
        nlp: Stanza pipeline
        span_text: Greek text to parse
        span_id: Span identifier

    Returns:
        List of word parse records
    """
    if not span_text or not span_text.strip():
        return []

    doc = nlp(span_text)

    parse_records = []
    word_idx = 0

    for sent_idx, sent in enumerate(doc.sentences):
        for word in sent.words:
            parse_records.append({
                "span_id": span_id,
                "sentence_idx": sent_idx,
                "word_idx": word_idx,
                "stanza_id": word.id,
                "text": word.text,
                "lemma": word.lemma,
                "upos": word.upos,
                "xpos": word.xpos,
                "feats": word.feats,
                "head": word.head,
                "deprel": word.deprel,
                "head_in_span": word.head + word_idx - word.id if word.head > 0 else -1,
            })
            word_idx += 1

    return parse_records


def parse_all_spans(spans_df, config: dict) -> "pd.DataFrame":
    """
    Parse all gap spans using Stanza.

    Args:
        spans_df: DataFrame of gap spans
        config: Pipeline config

    Returns:
        DataFrame of parse results
    """
    import pandas as pd
    import stanza
    from tqdm import tqdm

    logger = get_logger(__name__)

    # Initialize Stanza pipeline
    logger.info("Initializing Stanza pipeline...")
    nlp = stanza.Pipeline(
        "grc",
        processors="tokenize,pos,lemma,depparse",
        verbose=False,
        tokenize_pretokenized=False,  # Let Stanza tokenize
    )

    all_parses = []
    failed_spans = []

    logger.info(f"Parsing {len(spans_df)} spans...")

    for _, span in tqdm(spans_df.iterrows(), total=len(spans_df), desc="Parsing spans"):
        span_id = span["span_id"]
        span_text = span["text"]

        try:
            parses = parse_span_with_stanza(nlp, span_text, span_id)
            all_parses.extend(parses)
        except Exception as e:
            logger.warning(f"Failed to parse span {span_id}: {e}")
            failed_spans.append(span_id)

    if failed_spans:
        logger.warning(f"Failed spans: {len(failed_spans)}")

    # Create DataFrame
    parses_df = pd.DataFrame(all_parses)

    logger.info(f"Parsed {len(parses_df)} words from {len(spans_df)} spans")

    return parses_df


def main(config: dict = None, dry_run: bool = False) -> bool:
    """Main entry point."""
    if config is None:
        config = load_config()

    logger = get_logger(__name__)

    spans_path = Path(config["paths"]["data"]["intermediate"]) / "gap_spans.parquet"
    output_path = Path(config["paths"]["data"]["intermediate"]) / "gap_parses.parquet"

    if dry_run:
        logger.info("[DRY RUN] Would parse all gap spans with Stanza")
        logger.info(f"[DRY RUN] Input: {spans_path}")
        logger.info(f"[DRY RUN] Output: {output_path}")
        return True

    import pandas as pd

    # Check dependencies
    try:
        import stanza
    except ImportError:
        logger.error("Stanza not installed. Run: pip install stanza")
        return False

    # Check input
    if not spans_path.exists():
        logger.error(f"Gap spans not found: {spans_path}")
        logger.error("Run p3_01_analyze_gaps first")
        return False

    # Load spans
    logger.info("Loading gap spans...")
    spans_df = pd.read_parquet(spans_path)
    logger.info(f"Loaded {len(spans_df)} spans")

    # Parse
    parses_df = parse_all_spans(spans_df, config)

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    parses_df.to_parquet(output_path, index=False)
    logger.info(f"Saved parses to: {output_path}")

    # Summary
    logger.info("\nParsing Summary:")
    logger.info("-" * 40)
    logger.info(f"Total spans: {len(spans_df)}")
    logger.info(f"Total parsed words: {len(parses_df)}")

    if len(parses_df) > 0:
        logger.info(f"\nDependency relation distribution:")
        deprel_counts = parses_df["deprel"].value_counts().head(10)
        for deprel, count in deprel_counts.items():
            logger.info(f"  {deprel}: {count}")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    with ScriptLogger("p3_04_parse_gaps") as logger:
        config = load_config()
        success = main(config, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
