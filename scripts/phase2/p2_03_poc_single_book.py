#!/usr/bin/env python3
"""
Script: p2_03_poc_single_book.py
Phase: 2 - Alignment
Purpose: Proof of concept alignment on 3 John (shortest NT book)

Input:  data/intermediate/tr_words.parquet, data/intermediate/n1904_words.parquet
Output: reports/poc_3john_report.md

Usage:
    python -m scripts.phase2.p2_03_poc_single_book
    python -m scripts.phase2.p2_03_poc_single_book --dry-run
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils.config import load_config
from scripts.utils.logging import ScriptLogger, get_logger
from scripts.phase2.p2_02_align_verses import align_verse_words, create_word_key
from scripts.phase2.p2_04_full_alignment import BOOK_NAME_MAP


def run_poc_alignment(tr_df, n1904_df, book: str, config: dict) -> dict:
    """
    Run proof-of-concept alignment on a single book.

    Args:
        tr_df: TR words DataFrame
        n1904_df: N1904 words DataFrame
        book: Book name to align
        config: Pipeline config

    Returns:
        Dict with alignment statistics
    """
    import pandas as pd

    logger = get_logger(__name__)
    match_criteria = config["alignment"]["match_criteria"]

    # Filter to the target book using the name mapping
    # Find the TR book code for this book
    tr_book_code = None
    n1904_book_name = None

    # Check if book is a TR code
    if book in BOOK_NAME_MAP:
        tr_book_code = book
        n1904_book_name = BOOK_NAME_MAP[book]
    else:
        # Check if book is an N1904 name, find corresponding TR code
        for tr_code, n1904_name in BOOK_NAME_MAP.items():
            if n1904_name == book or book.lower() in n1904_name.lower():
                tr_book_code = tr_code
                n1904_book_name = n1904_name
                break

    # Handle common variations
    if book == "3John":
        tr_book_code = "3JN"
        n1904_book_name = "III_John"

    if tr_book_code is None:
        tr_book_code = book
    if n1904_book_name is None:
        n1904_book_name = BOOK_NAME_MAP.get(book, book)

    tr_book = tr_df[tr_df["book"] == tr_book_code]
    n1904_book = n1904_df[n1904_df["book"] == n1904_book_name]

    if len(tr_book) == 0:
        logger.warning(f"No TR data found for book: {book}")
        logger.info(f"Available books in TR: {sorted(tr_df['book'].unique())}")
        return None

    if len(n1904_book) == 0:
        logger.warning(f"No N1904 data found for book: {book}")
        logger.info(f"Available books in N1904: {sorted(n1904_df['book'].unique())}")
        return None

    logger.info(f"Book: {book}")
    logger.info(f"  TR words: {len(tr_book)}")
    logger.info(f"  N1904 words: {len(n1904_book)}")

    # Get unique verses
    tr_verses = set(zip(tr_book["chapter"], tr_book["verse"]))
    n1904_verses = set(zip(n1904_book["chapter"], n1904_book["verse"]))

    common_verses = tr_verses & n1904_verses
    tr_only_verses = tr_verses - n1904_verses
    n1904_only_verses = n1904_verses - tr_verses

    logger.info(f"  Common verses: {len(common_verses)}")
    logger.info(f"  TR-only verses: {len(tr_only_verses)}")
    logger.info(f"  N1904-only verses: {len(n1904_only_verses)}")

    # Align each verse
    total_alignments = 0
    total_tr_gaps = 0
    total_n1904_gaps = 0
    verse_results = []

    for chapter, verse in sorted(common_verses):
        tr_verse = tr_book[
            (tr_book["chapter"] == chapter) & (tr_book["verse"] == verse)
        ].to_dict("records")

        n1904_verse = n1904_book[
            (n1904_book["chapter"] == chapter) & (n1904_book["verse"] == verse)
        ].to_dict("records")

        alignments, tr_gaps, n1904_gaps = align_verse_words(
            tr_verse, n1904_verse, match_criteria
        )

        total_alignments += len(alignments)
        total_tr_gaps += len(tr_gaps)
        total_n1904_gaps += len(n1904_gaps)

        verse_results.append({
            "chapter": chapter,
            "verse": verse,
            "tr_words": len(tr_verse),
            "n1904_words": len(n1904_verse),
            "aligned": len(alignments),
            "tr_gaps": len(tr_gaps),
            "n1904_gaps": len(n1904_gaps),
        })

    # Calculate statistics
    total_tr_words = len(tr_book)
    total_n1904_words = len(n1904_book)
    alignment_rate = total_alignments / total_tr_words * 100 if total_tr_words > 0 else 0

    results = {
        "book": book,
        "tr_words": total_tr_words,
        "n1904_words": total_n1904_words,
        "common_verses": len(common_verses),
        "tr_only_verses": len(tr_only_verses),
        "n1904_only_verses": len(n1904_only_verses),
        "total_alignments": total_alignments,
        "total_tr_gaps": total_tr_gaps,
        "total_n1904_gaps": total_n1904_gaps,
        "alignment_rate": alignment_rate,
        "verse_results": verse_results,
    }

    return results


def generate_report(results: dict, output_path: Path) -> None:
    """Generate markdown report from results."""
    logger = get_logger(__name__)

    lines = [
        f"# Proof of Concept Alignment Report: {results['book']}",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| TR Words | {results['tr_words']:,} |",
        f"| N1904 Words | {results['n1904_words']:,} |",
        f"| Aligned Words | {results['total_alignments']:,} |",
        f"| TR Gaps (unmatched) | {results['total_tr_gaps']:,} |",
        f"| N1904 Gaps (unmatched) | {results['total_n1904_gaps']:,} |",
        f"| **Alignment Rate** | **{results['alignment_rate']:.1f}%** |",
        "",
        "## Verse-Level Details",
        "",
        "| Ch:Vs | TR | N1904 | Aligned | TR Gaps | N1904 Gaps |",
        "|-------|---:|------:|--------:|--------:|-----------:|",
    ]

    for vr in results["verse_results"]:
        lines.append(
            f"| {vr['chapter']}:{vr['verse']} | {vr['tr_words']} | {vr['n1904_words']} | "
            f"{vr['aligned']} | {vr['tr_gaps']} | {vr['n1904_gaps']} |"
        )

    lines.extend([
        "",
        "## Interpretation",
        "",
        f"The alignment rate of {results['alignment_rate']:.1f}% indicates ",
        "the feasibility of the graft-and-patch approach. Gaps represent words ",
        "that need syntax annotation via NLP (Phase 3).",
        "",
        "### Next Steps",
        "",
        "1. Run full alignment on all books (p2_04)",
        "2. Build ID translation table (p2_05)",
        "3. Transplant syntax features (p2_06)",
    ])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines))
    logger.info(f"Report written to: {output_path}")


def main(config: dict = None, dry_run: bool = False) -> bool:
    """Main entry point."""
    if config is None:
        config = load_config()

    logger = get_logger(__name__)

    tr_path = Path(config["paths"]["data"]["intermediate"]) / "tr_words.parquet"
    n1904_path = Path(config["paths"]["data"]["intermediate"]) / "n1904_words.parquet"
    output_path = Path(config["paths"]["reports"]) / "poc_3john_report.md"

    if dry_run:
        logger.info("[DRY RUN] Would run PoC alignment on 3 John")
        return True

    # Check inputs exist
    if not tr_path.exists():
        logger.error(f"TR data not found: {tr_path}")
        return False
    if not n1904_path.exists():
        logger.error(f"N1904 data not found: {n1904_path}")
        return False

    import pandas as pd

    # Load data
    logger.info("Loading data...")
    tr_df = pd.read_parquet(tr_path)
    n1904_df = pd.read_parquet(n1904_path)

    # Run PoC
    poc_book = config["alignment"].get("poc_book", "3John")
    logger.info(f"Running PoC alignment on: {poc_book}")

    results = run_poc_alignment(tr_df, n1904_df, poc_book, config)

    if results is None:
        logger.error("PoC alignment failed - book not found")
        return False

    # Report results
    logger.info(f"\n{'='*50}")
    logger.info(f"PoC Results for {poc_book}")
    logger.info(f"{'='*50}")
    logger.info(f"Alignment Rate: {results['alignment_rate']:.1f}%")
    logger.info(f"Aligned: {results['total_alignments']:,} / {results['tr_words']:,} words")
    logger.info(f"TR Gaps: {results['total_tr_gaps']:,}")
    logger.info(f"N1904 Gaps: {results['total_n1904_gaps']:,}")

    # Generate report
    generate_report(results, output_path)

    # Check if alignment rate meets threshold
    min_rate = config["qa"].get("min_alignment_percent", 95.0)
    if results["alignment_rate"] >= min_rate:
        logger.info(f"SUCCESS: Alignment rate {results['alignment_rate']:.1f}% >= {min_rate}%")
        return True
    else:
        logger.warning(f"Alignment rate {results['alignment_rate']:.1f}% < {min_rate}%")
        logger.warning("This may indicate data format issues")
        return True  # Still continue, just warn


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    with ScriptLogger("p2_03_poc_single_book") as logger:
        config = load_config()
        success = main(config, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
