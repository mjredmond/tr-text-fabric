#!/usr/bin/env python3
"""
Phase 4 Step 8c: Infer Structure for Known Words

For verses where all words exist in N1904 but positions differ,
infer structure by:
1. Transplanting aligned portions
2. Inferring phrase placement for mispositioned words using:
   - N1904 usage patterns
   - POS-based heuristics
   - Adjacent word context
"""

import pandas as pd
import json
from pathlib import Path
import sys
from collections import defaultdict, Counter

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.utils.logging import ScriptLogger
from scripts.utils.config import load_config
from scripts.utils.tf_helpers import load_n1904


def build_word_patterns(api, n1904: pd.DataFrame) -> dict:
    """
    Build usage patterns for each word form from N1904.

    Returns dict mapping normalized word -> {
        'phrase_types': Counter of phrase types this word appears in,
        'functions': Counter of syntactic functions,
        'typical_phrase_type': most common phrase type,
        'sp': most common part of speech
    }
    """
    patterns = defaultdict(lambda: {
        'phrase_types': Counter(),
        'functions': Counter(),
        'sp': Counter()
    })

    for _, row in n1904.iterrows():
        word = row.get('word', '').lower()
        if not word:
            continue

        sp = row.get('sp')
        function = row.get('function')

        if sp:
            patterns[word]['sp'][sp] += 1
        if function:
            patterns[word]['functions'][function] += 1

    # Compute typical values
    for word, data in patterns.items():
        if data['sp']:
            data['typical_sp'] = data['sp'].most_common(1)[0][0]
        if data['functions']:
            data['typical_function'] = data['functions'].most_common(1)[0][0]

    return dict(patterns)


def infer_phrase_type(word: str, sp: str, patterns: dict, context: dict) -> tuple:
    """
    Infer the likely phrase type and function for a word.

    Returns (phrase_type, function, confidence)
    """
    word_lower = word.lower()

    # Check patterns from N1904
    if word_lower in patterns:
        pattern = patterns[word_lower]
        typical_sp = pattern.get('typical_sp')
        typical_func = pattern.get('typical_function')

        # Higher confidence if we have good data
        confidence = 0.85
        return (None, typical_func, confidence)

    # Fall back to POS-based heuristics
    if sp:
        sp_lower = sp.lower() if sp else ''

        # Articles typically in NP
        if sp_lower in ['art', 'det']:
            return ('NP', None, 0.8)

        # Prepositions start PP
        if sp_lower in ['prep', 'adp']:
            return ('PP', 'Cmpl', 0.8)

        # Nouns in NP
        if sp_lower in ['noun', 'n']:
            return ('NP', None, 0.75)

        # Verbs in VP or predicate
        if sp_lower in ['verb', 'v']:
            return (None, 'Pred', 0.75)

        # Adjectives
        if sp_lower in ['adj', 'a']:
            return ('AdjP', None, 0.7)

        # Adverbs
        if sp_lower in ['adv']:
            return ('AdvP', 'Cmpl', 0.7)

        # Conjunctions often at clause boundaries
        if sp_lower in ['conj', 'cconj', 'sconj']:
            return (None, None, 0.6)

    return (None, None, 0.5)


def process_infer_verse(
    tr_verse: pd.DataFrame,
    n1904_structure: dict,
    n1904_to_tr: dict,
    word_patterns: dict
) -> dict:
    """
    Process a verse that needs inference for some words.

    Args:
        tr_verse: DataFrame of TR words for this verse
        n1904_structure: Structure data from direct transplant (or None)
        n1904_to_tr: N1904 node -> TR word_id mapping
        word_patterns: Word usage patterns from N1904

    Returns:
        Structure dict for this verse
    """
    result = {
        'clauses': [],
        'phrases': [],
        'wgs': [],
        'word_assignments': {},  # TR word_id -> phrase assignment
        'source': 'n1904_inferred',
        'confidence': 0.0
    }

    aligned_words = []
    inferable_words = []

    for _, row in tr_verse.iterrows():
        word_id = row['word_id']
        if pd.notna(row.get('n1904_node_id')):
            aligned_words.append({
                'word_id': word_id,
                'n1904_node': int(row['n1904_node_id']),
                'word': row['word'],
                'sp': row.get('sp')
            })
        else:
            inferable_words.append({
                'word_id': word_id,
                'word': row['word'],
                'sp': row.get('sp'),
                'status': row.get('structure_status')
            })

    # If we have N1904 structure for aligned words, use it as base
    if n1904_structure:
        result['clauses'] = n1904_structure.get('clauses', [])
        result['phrases'] = n1904_structure.get('phrases', [])
        result['wgs'] = n1904_structure.get('wgs', [])

    # For inferable words, determine placement
    total_confidence = 0
    for inf_word in inferable_words:
        phrase_type, function, conf = infer_phrase_type(
            inf_word['word'],
            inf_word['sp'],
            word_patterns,
            {'aligned': aligned_words}
        )

        result['word_assignments'][inf_word['word_id']] = {
            'inferred_phrase_type': phrase_type,
            'inferred_function': function,
            'confidence': conf,
            'source': 'inference'
        }
        total_confidence += conf

    # Calculate average confidence
    if inferable_words:
        result['confidence'] = total_confidence / len(inferable_words)
    else:
        result['confidence'] = 1.0

    return result


def main():
    """Main entry point."""
    config = load_config()

    with ScriptLogger('p4_08c_infer_structure') as logger:
        # Load data
        logger.info("Loading data...")
        tr = pd.read_parquet('data/intermediate/tr_structure_classified.parquet')
        verse_stats = pd.read_parquet('data/intermediate/verse_structure_stats.parquet')
        n1904 = pd.read_parquet('data/intermediate/n1904_words.parquet')

        # Get verses needing inference (all words known, but not all aligned)
        infer_verses = verse_stats[verse_stats['category'] == 'transplant_infer']
        logger.info(f"Verses needing inference: {len(infer_verses):,}")

        # Build word patterns from N1904
        logger.info("Building word usage patterns from N1904...")
        word_patterns = build_word_patterns(None, n1904)
        logger.info(f"  Patterns for {len(word_patterns):,} unique words")

        # Load N1904 for structure extraction
        logger.info("Loading N1904 for structure...")
        TF = load_n1904(config)
        api = TF.api

        # Book name mapping
        book_map = {
            'MAT': 'Matthew', 'MAR': 'Mark', 'LUK': 'Luke', 'JHN': 'John',
            'ACT': 'Acts', 'ROM': 'Romans', '1CO': 'I_Corinthians', '2CO': 'II_Corinthians',
            'GAL': 'Galatians', 'EPH': 'Ephesians', 'PHP': 'Philippians', 'COL': 'Colossians',
            '1TH': 'I_Thessalonians', '2TH': 'II_Thessalonians', '1TI': 'I_Timothy', '2TI': 'II_Timothy',
            'TIT': 'Titus', 'PHM': 'Philemon', 'HEB': 'Hebrews', 'JAS': 'James',
            '1PE': 'I_Peter', '2PE': 'II_Peter', '1JN': 'I_John', '2JN': 'II_John',
            '3JN': 'III_John', 'JUD': 'Jude', 'REV': 'Revelation'
        }

        # Build N1904 to TR mapping
        aligned = tr[tr['n1904_node_id'].notna()]
        n1904_to_tr = dict(zip(
            aligned['n1904_node_id'].astype(int),
            aligned['word_id']
        ))

        # Process each verse
        all_structures = []
        confidence_sum = 0

        logger.info("Processing verses...")
        for idx, row in infer_verses.iterrows():
            book = row['book']
            chapter = int(row['chapter'])
            verse = int(row['verse'])

            # Get TR words for this verse
            verse_tr = tr[(tr['book'] == book) &
                         (tr['chapter'] == chapter) &
                         (tr['verse'] == verse)]

            # Process verse
            structure = process_infer_verse(
                verse_tr,
                None,  # No pre-existing structure
                n1904_to_tr,
                word_patterns
            )

            structure['book'] = book
            structure['chapter'] = chapter
            structure['verse'] = verse

            all_structures.append(structure)
            confidence_sum += structure['confidence']

            if len(all_structures) % 500 == 0:
                logger.info(f"  Processed {len(all_structures):,} verses...")

        avg_confidence = confidence_sum / len(all_structures) if all_structures else 0
        logger.info(f"\nProcessed {len(all_structures):,} verses")
        logger.info(f"Average confidence: {avg_confidence:.2%}")

        # Count inferred words
        total_inferred = sum(len(s['word_assignments']) for s in all_structures)
        logger.info(f"Total inferred word assignments: {total_inferred:,}")

        # Save results
        output_path = Path('data/intermediate/tr_structure_inferred.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_structures, f, indent=2, ensure_ascii=False)
        logger.info(f"\nSaved to: {output_path}")

        # Summary by confidence level
        high_conf = sum(1 for s in all_structures if s['confidence'] >= 0.8)
        med_conf = sum(1 for s in all_structures if 0.6 <= s['confidence'] < 0.8)
        low_conf = sum(1 for s in all_structures if s['confidence'] < 0.6)

        logger.info(f"\nConfidence distribution:")
        logger.info(f"  High (>=80%): {high_conf:,} verses")
        logger.info(f"  Medium (60-80%): {med_conf:,} verses")
        logger.info(f"  Low (<60%): {low_conf:,} verses")

    return 0


if __name__ == '__main__':
    sys.exit(main())
