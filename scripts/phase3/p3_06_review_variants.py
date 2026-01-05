#!/usr/bin/env python3
"""
Script: p3_06_review_variants.py
Phase: 3 - Delta Patching
Purpose: Generate review documentation for high-profile textual variants

Input:  data/intermediate/gap_syntax.parquet, data/intermediate/gap_spans.parquet,
        config.yaml (variants.priority_verses)
Output: reviews/*.md

Usage:
    python -m scripts.phase3.p3_06_review_variants
    python -m scripts.phase3.p3_06_review_variants --dry-run
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils.config import load_config
from scripts.utils.logging import ScriptLogger, get_logger


def get_priority_verses(config: dict) -> List[Dict]:
    """Get list of priority verses from config."""
    return config.get("variants", {}).get("priority_verses", [])


def find_variant_spans(spans_df, priority_verses: List[Dict], book_map: Dict) -> List[Dict]:
    """
    Find spans that correspond to priority variants.

    Args:
        spans_df: Gap spans DataFrame
        priority_verses: List of priority verse configs
        book_map: TR book code to config book name mapping

    Returns:
        List of matching spans with variant metadata
    """
    from scripts.phase2.p2_04_full_alignment import BOOK_NAME_MAP

    logger = get_logger(__name__)

    # Create reverse mapping (N1904 name -> TR code)
    reverse_map = {v: k for k, v in BOOK_NAME_MAP.items()}

    matched_spans = []

    for variant in priority_verses:
        book = variant["book"]
        chapter = variant["chapter"]
        verses = variant["verses"]
        name = variant["name"]

        # Find TR book code
        tr_book = reverse_map.get(book, book)
        # Try common variations
        if tr_book == book:
            for tr_code, n1904_name in BOOK_NAME_MAP.items():
                if book.lower().replace("_", "") in n1904_name.lower().replace("_", ""):
                    tr_book = tr_code
                    break

        # Find matching spans
        for verse in verses:
            matching = spans_df[
                (spans_df["book"] == tr_book) &
                (spans_df["chapter"] == chapter) &
                (spans_df["verse"] == verse)
            ]

            for _, span in matching.iterrows():
                matched_spans.append({
                    "variant_name": name,
                    "book": book,
                    "chapter": chapter,
                    "verse": verse,
                    "span_id": span["span_id"],
                    "text": span["text"],
                    "word_count": span["word_count"],
                    "category": span["category"],
                })

    return matched_spans


def generate_variant_review(variant_spans: List[Dict], syntax_df, spans_df, output_dir: Path) -> None:
    """
    Generate review documentation for each variant.

    Args:
        variant_spans: List of variant span metadata
        syntax_df: Gap syntax DataFrame
        spans_df: Gap spans DataFrame
        output_dir: Directory for review files
    """
    import ast

    logger = get_logger(__name__)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Group spans by variant name
    variants = {}
    for span in variant_spans:
        name = span["variant_name"]
        if name not in variants:
            variants[name] = []
        variants[name].append(span)

    for name, spans in variants.items():
        # Create filename from variant name (sanitize for filesystem)
        filename = name.lower().replace(" ", "_").replace("'", "").replace("/", "_") + ".md"
        filepath = output_dir / filename

        lines = [
            f"# Variant Review: {name}",
            "",
            "## Overview",
            "",
            f"This document reviews the NLP-generated syntax for the {name} variant.",
            "",
            "## Verses",
            "",
        ]

        for span in spans:
            lines.extend([
                f"### {span['book']} {span['chapter']}:{span['verse']}",
                "",
                f"**Greek Text:** {span['text']}",
                "",
                f"**Word Count:** {span['word_count']}",
                "",
                f"**Category:** {span['category']}",
                "",
            ])

            # Get syntax for this span's words
            span_id = span["span_id"]
            span_data = spans_df[spans_df["span_id"] == span_id]

            if len(span_data) > 0:
                word_ids = span_data.iloc[0]["word_ids"]
                if isinstance(word_ids, str):
                    try:
                        word_ids = ast.literal_eval(word_ids)
                    except:
                        word_ids = []

                # Convert numpy array to list if needed
                import numpy as np
                if isinstance(word_ids, np.ndarray):
                    word_ids = word_ids.tolist()
                if word_ids and len(word_ids) > 0:
                    span_syntax = syntax_df[syntax_df["word_id"].isin(word_ids)]

                    if len(span_syntax) > 0:
                        lines.extend([
                            "**Generated Syntax:**",
                            "",
                            "| Word ID | Lemma | POS | Function | Parent |",
                            "|---------|-------|-----|----------|--------|",
                        ])

                        for _, row in span_syntax.iterrows():
                            lemma = row.get("lemma", "?") or "?"
                            sp = row.get("sp", "?") or "?"
                            func = row.get("function", "?") or "?"
                            parent = row.get("parent", "-") or "-"
                            lines.append(f"| {row['word_id']} | {lemma} | {sp} | {func} | {parent} |")

                        lines.append("")

            lines.extend([
                "#### Review Checklist",
                "",
                "- [ ] Subject-predicate agreement is correct",
                "- [ ] Case function assignments are appropriate",
                "- [ ] Clause boundaries are correct",
                "- [ ] No grammatical anomalies",
                "",
                "#### Notes",
                "",
                "_Add review notes here_",
                "",
                "---",
                "",
            ])

        lines.extend([
            "## Summary",
            "",
            f"**Total spans reviewed:** {len(spans)}",
            "",
            "**Reviewer:** _Not yet reviewed_",
            "",
            "**Status:** Pending Review",
            "",
        ])

        filepath.write_text("\n".join(lines))
        logger.info(f"Generated review: {filepath}")


def main(config: dict = None, dry_run: bool = False) -> bool:
    """Main entry point."""
    if config is None:
        config = load_config()

    logger = get_logger(__name__)

    syntax_path = Path(config["paths"]["data"]["intermediate"]) / "gap_syntax.parquet"
    spans_path = Path(config["paths"]["data"]["intermediate"]) / "gap_spans.parquet"
    reviews_dir = Path(config["paths"]["root"]) / "reviews"

    if dry_run:
        logger.info("[DRY RUN] Would generate variant review documentation")
        logger.info(f"[DRY RUN] Output: {reviews_dir}")
        return True

    import pandas as pd

    # Check inputs
    if not syntax_path.exists():
        logger.error(f"Gap syntax not found: {syntax_path}")
        return False
    if not spans_path.exists():
        logger.error(f"Gap spans not found: {spans_path}")
        return False

    # Load data
    logger.info("Loading data...")
    syntax_df = pd.read_parquet(syntax_path)
    spans_df = pd.read_parquet(spans_path)

    # Get priority verses
    priority_verses = get_priority_verses(config)
    logger.info(f"Priority variants: {len(priority_verses)}")

    if not priority_verses:
        logger.warning("No priority verses configured")
        logger.info("Add variants to config.yaml under 'variants.priority_verses'")
        return True

    # Find matching spans
    from scripts.phase2.p2_04_full_alignment import BOOK_NAME_MAP
    variant_spans = find_variant_spans(spans_df, priority_verses, BOOK_NAME_MAP)

    logger.info(f"Found {len(variant_spans)} variant spans")

    if not variant_spans:
        logger.warning("No variant spans found in gaps")
        logger.info("This may mean the variants aligned with N1904")
        return True

    # Generate reviews
    generate_variant_review(variant_spans, syntax_df, spans_df, reviews_dir)

    logger.info(f"\nReview files generated in: {reviews_dir}")
    logger.info("Please review and update the generated documentation")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    with ScriptLogger("p3_06_review_variants") as logger:
        config = load_config()
        success = main(config, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
