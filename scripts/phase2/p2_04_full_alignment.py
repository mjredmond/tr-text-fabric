#!/usr/bin/env python3
"""
Script: p2_04_full_alignment.py
Phase: 2 - Alignment
Purpose: Run alignment on entire NT, produce alignment map and gaps file

Input:  data/intermediate/tr_words.parquet, data/intermediate/n1904_words.parquet
Output: data/intermediate/alignment_map.parquet, data/intermediate/gaps.csv

Usage:
    python -m scripts.phase2.p2_04_full_alignment
    python -m scripts.phase2.p2_04_full_alignment --dry-run
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils.config import load_config
from scripts.utils.logging import ScriptLogger, get_logger
from scripts.phase2.p2_02_align_verses import align_verse_words


# Book name mapping between TR and N1904
# N1904 uses underscores and Roman numerals for numbered books
BOOK_NAME_MAP = {
    # TR name (BLB format) -> N1904 name
    "MAT": "Matthew", "MAR": "Mark", "LUK": "Luke", "JHN": "John",
    "ACT": "Acts", "ROM": "Romans",
    "1CO": "I_Corinthians", "2CO": "II_Corinthians",
    "GAL": "Galatians", "EPH": "Ephesians", "PHP": "Philippians",
    "COL": "Colossians", "1TH": "I_Thessalonians", "2TH": "II_Thessalonians",
    "1TI": "I_Timothy", "2TI": "II_Timothy", "TIT": "Titus", "PHM": "Philemon",
    "HEB": "Hebrews", "JAS": "James",
    "1PE": "I_Peter", "2PE": "II_Peter",
    "1JN": "I_John", "2JN": "II_John", "3JN": "III_John",
    "JUD": "Jude", "REV": "Revelation",
    # Legacy mappings for old TR format
    "JOH": "John", "JAM": "James",
    "1JO": "I_John", "2JO": "II_John", "3JO": "III_John",
    "PA": "John",  # Pericope Adulterae - part of John
    "ACT24": "Acts",  # Additional Acts content
}


def normalize_book_name(name: str) -> str:
    """Normalize book name to N1904 format."""
    return BOOK_NAME_MAP.get(name, name)


def run_full_alignment(tr_df, n1904_df, config: dict) -> Tuple[List[Dict], List[Dict], Dict]:
    """
    Run alignment across all books.

    Args:
        tr_df: TR words DataFrame
        n1904_df: N1904 words DataFrame
        config: Pipeline config

    Returns:
        Tuple of (alignment_records, gap_records, statistics)
    """
    import pandas as pd
    from tqdm import tqdm

    logger = get_logger(__name__)
    match_criteria = config["alignment"]["match_criteria"]

    # Add normalized book names to TR
    tr_df = tr_df.copy()
    tr_df["book_normalized"] = tr_df["book"].apply(normalize_book_name)

    alignment_records = []
    gap_records = []
    book_stats = {}

    # Get all unique books from TR
    tr_books = tr_df["book"].unique()
    logger.info(f"Processing {len(tr_books)} books...")

    for tr_book in tqdm(tr_books, desc="Aligning books"):
        n1904_book = normalize_book_name(tr_book)

        # Get words for this book
        tr_book_df = tr_df[tr_df["book"] == tr_book]
        n1904_book_df = n1904_df[n1904_df["book"] == n1904_book]

        if len(n1904_book_df) == 0:
            logger.warning(f"No N1904 data for book: {tr_book} -> {n1904_book}")
            # All TR words in this book are gaps
            for _, row in tr_book_df.iterrows():
                gap_records.append({
                    "word_id": row["word_id"],
                    "book": row["book"],
                    "chapter": row["chapter"],
                    "verse": row["verse"],
                    "word_rank": row["word_rank"],
                    "word": row["word"],
                    "gap_type": "no_n1904_book",
                })
            continue

        # Get verses
        tr_verses = set(zip(tr_book_df["chapter"], tr_book_df["verse"]))
        n1904_verses = set(zip(n1904_book_df["chapter"], n1904_book_df["verse"]))
        common_verses = tr_verses & n1904_verses

        book_alignments = 0
        book_tr_gaps = 0

        # Process common verses
        for chapter, verse in common_verses:
            tr_verse_df = tr_book_df[
                (tr_book_df["chapter"] == chapter) & (tr_book_df["verse"] == verse)
            ]
            n1904_verse_df = n1904_book_df[
                (n1904_book_df["chapter"] == chapter) & (n1904_book_df["verse"] == verse)
            ]

            tr_verse = tr_verse_df.to_dict("records")
            n1904_verse = n1904_verse_df.to_dict("records")

            alignments, tr_gaps, n1904_gaps = align_verse_words(
                tr_verse, n1904_verse, match_criteria
            )

            # Record alignments
            for tr_idx, n1904_idx in alignments:
                tr_word = tr_verse[tr_idx]
                n1904_word = n1904_verse[n1904_idx]
                alignment_records.append({
                    "tr_word_id": tr_word["word_id"],
                    "n1904_node_id": n1904_word.get("node_id"),
                    "book": tr_word["book"],
                    "chapter": tr_word["chapter"],
                    "verse": tr_word["verse"],
                    "tr_word_rank": tr_word["word_rank"],
                    "n1904_word_rank": n1904_word.get("word_rank"),
                    "tr_word": tr_word["word"],
                })
                book_alignments += 1

            # Record TR gaps
            for tr_idx in tr_gaps:
                tr_word = tr_verse[tr_idx]
                gap_records.append({
                    "word_id": tr_word["word_id"],
                    "book": tr_word["book"],
                    "chapter": tr_word["chapter"],
                    "verse": tr_word["verse"],
                    "word_rank": tr_word["word_rank"],
                    "word": tr_word["word"],
                    "gap_type": "unmatched",
                })
                book_tr_gaps += 1

        # Handle TR-only verses (verses in TR but not in N1904)
        tr_only_verses = tr_verses - n1904_verses
        for chapter, verse in tr_only_verses:
            tr_verse_df = tr_book_df[
                (tr_book_df["chapter"] == chapter) & (tr_book_df["verse"] == verse)
            ]
            for _, row in tr_verse_df.iterrows():
                gap_records.append({
                    "word_id": row["word_id"],
                    "book": row["book"],
                    "chapter": row["chapter"],
                    "verse": row["verse"],
                    "word_rank": row["word_rank"],
                    "word": row["word"],
                    "gap_type": "tr_only_verse",
                })
                book_tr_gaps += 1

        # Book statistics
        book_stats[tr_book] = {
            "tr_words": len(tr_book_df),
            "n1904_words": len(n1904_book_df),
            "alignments": book_alignments,
            "gaps": book_tr_gaps,
            "alignment_rate": book_alignments / len(tr_book_df) * 100 if len(tr_book_df) > 0 else 0,
        }

    # Overall statistics
    total_tr = len(tr_df)
    total_aligned = len(alignment_records)
    total_gaps = len(gap_records)

    stats = {
        "total_tr_words": total_tr,
        "total_aligned": total_aligned,
        "total_gaps": total_gaps,
        "alignment_rate": total_aligned / total_tr * 100 if total_tr > 0 else 0,
        "book_stats": book_stats,
    }

    return alignment_records, gap_records, stats


def main(config: dict = None, dry_run: bool = False) -> bool:
    """Main entry point."""
    if config is None:
        config = load_config()

    logger = get_logger(__name__)

    tr_path = Path(config["paths"]["data"]["intermediate"]) / "tr_words.parquet"
    n1904_path = Path(config["paths"]["data"]["intermediate"]) / "n1904_words.parquet"
    alignment_path = Path(config["paths"]["data"]["intermediate"]) / "alignment_map.parquet"
    gaps_path = Path(config["paths"]["data"]["intermediate"]) / "gaps.csv"
    report_path = Path(config["paths"]["reports"]) / "alignment_report.md"

    if dry_run:
        logger.info("[DRY RUN] Would run full NT alignment")
        return True

    import pandas as pd

    # Load data
    logger.info("Loading data...")
    tr_df = pd.read_parquet(tr_path)
    n1904_df = pd.read_parquet(n1904_path)

    logger.info(f"TR words: {len(tr_df):,}")
    logger.info(f"N1904 words: {len(n1904_df):,}")

    # Run alignment
    alignment_records, gap_records, stats = run_full_alignment(tr_df, n1904_df, config)

    # Save results
    logger.info("Saving results...")

    alignment_df = pd.DataFrame(alignment_records)
    alignment_df.to_parquet(alignment_path, index=False)
    logger.info(f"Alignment map: {len(alignment_df):,} records -> {alignment_path}")

    gaps_df = pd.DataFrame(gap_records)
    gaps_df.to_csv(gaps_path, index=False)
    logger.info(f"Gaps: {len(gaps_df):,} records -> {gaps_path}")

    # Generate report
    report_lines = [
        "# Full NT Alignment Report",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total TR Words | {stats['total_tr_words']:,} |",
        f"| Aligned Words | {stats['total_aligned']:,} |",
        f"| Gap Words | {stats['total_gaps']:,} |",
        f"| **Alignment Rate** | **{stats['alignment_rate']:.1f}%** |",
        "",
        "## By Book",
        "",
        "| Book | TR Words | Aligned | Gaps | Rate |",
        "|------|----------|---------|------|------|",
    ]

    for book, bs in sorted(stats["book_stats"].items()):
        report_lines.append(
            f"| {book} | {bs['tr_words']:,} | {bs['alignments']:,} | "
            f"{bs['gaps']:,} | {bs['alignment_rate']:.1f}% |"
        )

    report_lines.extend([
        "",
        "## Gap Types",
        "",
    ])

    if len(gaps_df) > 0:
        gap_types = gaps_df["gap_type"].value_counts()
        for gap_type, count in gap_types.items():
            report_lines.append(f"- **{gap_type}**: {count:,}")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines))
    logger.info(f"Report: {report_path}")

    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("ALIGNMENT COMPLETE")
    logger.info(f"{'='*50}")
    logger.info(f"Alignment Rate: {stats['alignment_rate']:.1f}%")
    logger.info(f"Aligned: {stats['total_aligned']:,} words")
    logger.info(f"Gaps: {stats['total_gaps']:,} words")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    with ScriptLogger("p2_04_full_alignment") as logger:
        config = load_config()
        success = main(config, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
