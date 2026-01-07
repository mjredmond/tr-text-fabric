#!/usr/bin/env python3
"""
Phase 4 Step 8a: Prepare Structure Classification Data

Classifies each TR word as:
- aligned: Direct N1904 match (structure can be transplanted)
- inferable: Word form exists in N1904 (position differs, can infer)
- unknown: Spelling variant or TR-only (needs lookup table)

Also builds verse-level statistics to determine transplant strategy.
"""

import pandas as pd
import unicodedata
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.utils.logging import ScriptLogger

def normalize_word(s: str) -> str:
    """Normalize Greek word for comparison."""
    if not s or pd.isna(s):
        return ''
    return unicodedata.normalize('NFC', str(s).lower())


def load_data(config: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load TR and N1904 data."""
    intermediate_dir = Path(config.get('intermediate_dir', 'data/intermediate'))

    tr_path = intermediate_dir / 'tr_transplanted.parquet'
    n1904_path = intermediate_dir / 'n1904_words.parquet'

    print(f"Loading TR data from {tr_path}")
    tr = pd.read_parquet(tr_path)

    print(f"Loading N1904 data from {n1904_path}")
    n1904 = pd.read_parquet(n1904_path)

    return tr, n1904


def build_n1904_word_index(n1904: pd.DataFrame) -> dict:
    """Build index of N1904 words by normalized form."""
    word_index = {}

    for _, row in n1904.iterrows():
        word_norm = normalize_word(row.get('word') or row.get('unicode', ''))
        if word_norm:
            if word_norm not in word_index:
                word_index[word_norm] = []
            word_index[word_norm].append({
                'node_id': row['node_id'],
                'sp': row.get('sp'),
                'function': row.get('function'),
                'role': row.get('role'),
                'clause_id': row.get('clause_id'),
                'phrase_id': row.get('phrase_id')
            })

    return word_index


def classify_words(tr: pd.DataFrame, n1904_word_index: dict) -> pd.DataFrame:
    """Classify each TR word by alignment status."""

    # Normalize TR words
    tr['word_normalized'] = tr['word'].apply(normalize_word)

    # Classify
    def get_status(row):
        if pd.notna(row['n1904_node_id']):
            return 'aligned'
        elif row['word_normalized'] in n1904_word_index:
            return 'inferable'
        else:
            return 'unknown'

    tr['structure_status'] = tr.apply(get_status, axis=1)

    return tr


def compute_verse_stats(tr: pd.DataFrame) -> pd.DataFrame:
    """Compute verse-level alignment statistics."""

    verse_groups = tr.groupby(['book', 'chapter', 'verse'])

    stats = []
    for (book, chapter, verse), group in verse_groups:
        total = len(group)
        aligned = (group['structure_status'] == 'aligned').sum()
        inferable = (group['structure_status'] == 'inferable').sum()
        unknown = (group['structure_status'] == 'unknown').sum()

        # Determine verse category
        if aligned == total:
            category = 'direct_transplant'
        elif unknown == 0:
            category = 'transplant_infer'
        else:
            category = 'has_unknowns'

        stats.append({
            'book': book,
            'chapter': chapter,
            'verse': verse,
            'total_words': total,
            'aligned_words': aligned,
            'inferable_words': inferable,
            'unknown_words': unknown,
            'pct_aligned': aligned / total * 100,
            'category': category
        })

    return pd.DataFrame(stats)


def extract_unknown_words(tr: pd.DataFrame) -> pd.DataFrame:
    """Extract unique unknown word forms for lookup table creation."""

    unknown = tr[tr['structure_status'] == 'unknown']

    # Group by word form and Strong's number
    unknown_forms = unknown.groupby(['word', 'strong']).agg({
        'word_id': 'count',
        'book': lambda x: x.iloc[0],
        'chapter': lambda x: x.iloc[0],
        'verse': lambda x: x.iloc[0]
    }).reset_index()

    unknown_forms.columns = ['word', 'strong', 'count', 'example_book', 'example_chapter', 'example_verse']
    unknown_forms = unknown_forms.sort_values('count', ascending=False)

    return unknown_forms


def main(config=None):
    """Main entry point."""
    config = {
        'intermediate_dir': 'data/intermediate',
        'output_dir': 'data/intermediate'
    }

    with ScriptLogger('p4_08a_prepare_structure_data') as logger:
        # Load data
        logger.info("Loading data...")
        tr, n1904 = load_data(config)
        logger.info(f"  TR words: {len(tr):,}")
        logger.info(f"  N1904 words: {len(n1904):,}")

        # Build N1904 word index
        logger.info("Building N1904 word index...")
        n1904_word_index = build_n1904_word_index(n1904)
        logger.info(f"  Unique word forms: {len(n1904_word_index):,}")

        # Classify TR words
        logger.info("Classifying TR words...")
        tr = classify_words(tr, n1904_word_index)

        status_counts = tr['structure_status'].value_counts()
        logger.info("Word classification:")
        for status, count in status_counts.items():
            logger.info(f"  {status}: {count:,} ({count/len(tr)*100:.1f}%)")

        # Compute verse statistics
        logger.info("Computing verse statistics...")
        verse_stats = compute_verse_stats(tr)

        category_counts = verse_stats['category'].value_counts()
        logger.info("Verse categories:")
        for cat, count in category_counts.items():
            words = verse_stats[verse_stats['category'] == cat]['total_words'].sum()
            logger.info(f"  {cat}: {count:,} verses ({words:,} words)")

        # Extract unknown words
        logger.info("Extracting unknown word forms...")
        unknown_forms = extract_unknown_words(tr)
        logger.info(f"  Unique unknown forms: {len(unknown_forms):,}")

        # Save outputs
        output_dir = Path(config['output_dir'])

        logger.info("Saving outputs...")

        # Save classified TR data
        tr_output = output_dir / 'tr_structure_classified.parquet'
        tr.to_parquet(tr_output, index=False)
        logger.info(f"  Saved: {tr_output}")

        # Save verse statistics
        verse_output = output_dir / 'verse_structure_stats.parquet'
        verse_stats.to_parquet(verse_output, index=False)
        logger.info(f"  Saved: {verse_output}")

        # Save unknown words (CSV for easy manual review)
        unknown_output = output_dir / 'unknown_word_forms.csv'
        unknown_forms.to_csv(unknown_output, index=False)
        logger.info(f"  Saved: {unknown_output}")

        # Summary
        logger.info("=" * 60)
        logger.info("STRUCTURE CLASSIFICATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Word-level:")
        logger.info(f"  Aligned:   {status_counts.get('aligned', 0):,} ({status_counts.get('aligned', 0)/len(tr)*100:.1f}%)")
        logger.info(f"  Inferable: {status_counts.get('inferable', 0):,} ({status_counts.get('inferable', 0)/len(tr)*100:.1f}%)")
        logger.info(f"  Unknown:   {status_counts.get('unknown', 0):,} ({status_counts.get('unknown', 0)/len(tr)*100:.1f}%)")

        logger.info(f"Verse-level:")
        direct = category_counts.get('direct_transplant', 0)
        infer = category_counts.get('transplant_infer', 0)
        unknown_v = category_counts.get('has_unknowns', 0)
        total_v = len(verse_stats)
        logger.info(f"  Direct transplant:  {direct:,} ({direct/total_v*100:.1f}%)")
        logger.info(f"  Transplant + infer: {infer:,} ({infer/total_v*100:.1f}%)")
        logger.info(f"  Has unknowns:       {unknown_v:,} ({unknown_v/total_v*100:.1f}%)")

        logger.info(f"Unknown forms to resolve: {len(unknown_forms):,}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
