#!/usr/bin/env python3
"""
Script: p3_01_analyze_gaps.py
Phase: 3 - Delta Patching
Purpose: Categorize and group gap spans for NLP processing

Input:  data/intermediate/gaps.csv, data/intermediate/tr_words.parquet
Output: data/intermediate/gap_spans.parquet, reports/gap_analysis_report.md

Usage:
    python -m scripts.phase3.p3_01_analyze_gaps
    python -m scripts.phase3.p3_01_analyze_gaps --dry-run
"""

import argparse
import sys
from pathlib import Path
from typing import List, Dict, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils.config import load_config
from scripts.utils.logging import ScriptLogger, get_logger


def group_gaps_into_spans(gaps_df, tr_df) -> "pd.DataFrame":
    """
    Group consecutive gap words into contiguous spans.

    A span is a sequence of adjacent gap words within the same verse.
    Adjacent means word_rank differs by 1.

    Args:
        gaps_df: DataFrame of gap words
        tr_df: Full TR words DataFrame (for getting word text)

    Returns:
        DataFrame of gap spans with metadata
    """
    import pandas as pd

    logger = get_logger(__name__)

    # Sort gaps by location
    gaps_sorted = gaps_df.sort_values(
        ["book", "chapter", "verse", "word_rank"]
    ).reset_index(drop=True)

    # Create TR lookup for word text
    tr_lookup = tr_df.set_index("word_id").to_dict("index")

    spans = []
    current_span = None

    for _, row in gaps_sorted.iterrows():
        book = row["book"]
        chapter = row["chapter"]
        verse = row["verse"]
        word_rank = row["word_rank"]
        word_id = row["word_id"]
        word = row["word"]
        gap_type = row["gap_type"]

        # Check if this continues the current span
        if (current_span is not None and
            current_span["book"] == book and
            current_span["chapter"] == chapter and
            current_span["verse"] == verse and
            word_rank == current_span["end_word_rank"] + 1):
            # Extend current span
            current_span["end_word_rank"] = word_rank
            current_span["word_ids"].append(word_id)  # Store actual word_id
            current_span["words"].append(word)
            current_span["word_count"] += 1
        else:
            # Save previous span if exists
            if current_span is not None:
                spans.append(current_span)

            # Start new span
            current_span = {
                "book": book,
                "chapter": chapter,
                "verse": verse,
                "start_word_rank": word_rank,
                "end_word_rank": word_rank,
                "word_ids": [word_id],  # Store actual word_id from gaps.csv
                "words": [word],
                "word_count": 1,
                "gap_type": gap_type,
            }

    # Don't forget the last span
    if current_span is not None:
        spans.append(current_span)

    # Convert to DataFrame and add span IDs
    span_records = []
    for i, span in enumerate(spans):
        span_records.append({
            "span_id": i + 1,
            "book": span["book"],
            "chapter": span["chapter"],
            "verse": span["verse"],
            "start_word_rank": span["start_word_rank"],
            "end_word_rank": span["end_word_rank"],
            "word_count": span["word_count"],
            "text": " ".join(span["words"]),
            "word_ids": span["word_ids"],
            "gap_type": span["gap_type"],
            "category": categorize_span(span),
        })

    return pd.DataFrame(span_records)


def categorize_span(span: dict) -> str:
    """
    Categorize a gap span by its characteristics.

    Categories:
    - single_word: Single word addition/substitution
    - short_phrase: 2-5 words
    - long_phrase: 6+ words
    - full_verse: Entire verse is a gap (TR-only verse)

    Args:
        span: Span dictionary

    Returns:
        Category string
    """
    if span["gap_type"] == "tr_only_verse":
        return "full_verse"
    elif span["word_count"] == 1:
        return "single_word"
    elif span["word_count"] <= 5:
        return "short_phrase"
    else:
        return "long_phrase"


def generate_report(spans_df, gaps_df, output_path: Path) -> None:
    """Generate gap analysis report."""
    logger = get_logger(__name__)

    lines = [
        "# Gap Analysis Report",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total Gap Words | {len(gaps_df):,} |",
        f"| Total Spans | {len(spans_df):,} |",
        f"| Avg Words per Span | {spans_df['word_count'].mean():.1f} |",
        "",
        "## Gap Types",
        "",
    ]

    gap_types = gaps_df["gap_type"].value_counts()
    for gap_type, count in gap_types.items():
        lines.append(f"- **{gap_type}**: {count:,}")

    lines.extend([
        "",
        "## Span Categories",
        "",
    ])

    categories = spans_df["category"].value_counts()
    for category, count in categories.items():
        avg_words = spans_df[spans_df["category"] == category]["word_count"].mean()
        lines.append(f"- **{category}**: {count:,} spans (avg {avg_words:.1f} words)")

    lines.extend([
        "",
        "## By Book",
        "",
        "| Book | Spans | Words | Avg Size |",
        "|------|-------|-------|----------|",
    ])

    book_stats = spans_df.groupby("book").agg({
        "span_id": "count",
        "word_count": ["sum", "mean"]
    }).reset_index()
    book_stats.columns = ["book", "spans", "words", "avg_size"]

    for _, row in book_stats.iterrows():
        lines.append(f"| {row['book']} | {int(row['spans'])} | {int(row['words'])} | {row['avg_size']:.1f} |")

    lines.extend([
        "",
        "## Longest Spans (by word count)",
        "",
        "| Span ID | Location | Words | Text (truncated) |",
        "|---------|----------|-------|------------------|",
    ])

    longest = spans_df.nlargest(10, "word_count")
    for _, row in longest.iterrows():
        loc = f"{row['book']} {row['chapter']}:{row['verse']}"
        text = row["text"][:50] + "..." if len(row["text"]) > 50 else row["text"]
        lines.append(f"| {row['span_id']} | {loc} | {row['word_count']} | {text} |")

    lines.extend([
        "",
        "## Full Verse Gaps (TR-only verses)",
        "",
        "| Location | Words | Text (truncated) |",
        "|----------|-------|------------------|",
    ])

    full_verses = spans_df[spans_df["category"] == "full_verse"]
    for _, row in full_verses.iterrows():
        loc = f"{row['book']} {row['chapter']}:{row['verse']}"
        text = row["text"][:60] + "..." if len(row["text"]) > 60 else row["text"]
        lines.append(f"| {loc} | {row['word_count']} | {text} |")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines))
    logger.info(f"Report written to: {output_path}")


def main(config: dict = None, dry_run: bool = False) -> bool:
    """Main entry point."""
    if config is None:
        config = load_config()

    logger = get_logger(__name__)

    gaps_path = Path(config["paths"]["data"]["intermediate"]) / "gaps.csv"
    tr_path = Path(config["paths"]["data"]["intermediate"]) / "tr_words.parquet"
    output_path = Path(config["paths"]["data"]["intermediate"]) / "gap_spans.parquet"
    report_path = Path(config["paths"]["reports"]) / "gap_analysis_report.md"

    if dry_run:
        logger.info("[DRY RUN] Would analyze gaps and create spans")
        logger.info(f"[DRY RUN] Input: {gaps_path}")
        logger.info(f"[DRY RUN] Output: {output_path}")
        return True

    import pandas as pd

    # Check inputs
    if not gaps_path.exists():
        logger.error(f"Gaps file not found: {gaps_path}")
        return False
    if not tr_path.exists():
        logger.error(f"TR words file not found: {tr_path}")
        return False

    # Load data
    logger.info("Loading data...")
    gaps_df = pd.read_csv(gaps_path)
    tr_df = pd.read_parquet(tr_path)

    logger.info(f"Gap words: {len(gaps_df):,}")

    # Group into spans
    logger.info("Grouping gaps into contiguous spans...")
    spans_df = group_gaps_into_spans(gaps_df, tr_df)

    logger.info(f"Created {len(spans_df):,} spans")

    # Category breakdown
    categories = spans_df["category"].value_counts()
    for cat, count in categories.items():
        logger.info(f"  {cat}: {count:,}")

    # Save spans
    output_path.parent.mkdir(parents=True, exist_ok=True)
    spans_df.to_parquet(output_path, index=False)
    logger.info(f"Saved spans to: {output_path}")

    # Generate report
    generate_report(spans_df, gaps_df, report_path)

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    with ScriptLogger("p3_01_analyze_gaps") as logger:
        config = load_config()
        success = main(config, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
