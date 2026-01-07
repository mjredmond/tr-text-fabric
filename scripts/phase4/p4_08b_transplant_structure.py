#!/usr/bin/env python3
"""
Phase 4 Step 8b: Direct Structure Transplant

For verses with 100% word alignment, copy the clause/phrase/wg structure
directly from N1904, remapping node IDs to TR space.
"""

import pandas as pd
from pathlib import Path
import sys
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.utils.logging import ScriptLogger
from scripts.utils.config import load_config
from scripts.utils.tf_helpers import load_n1904


def get_verse_structure(api, book: str, chapter: int, verse: int) -> dict:
    """
    Extract all structural nodes (clause, phrase, wg, etc.) for a verse.

    Returns dict with:
    - words: list of word node IDs
    - clauses: list of clause info dicts
    - phrases: list of phrase info dicts
    - wgs: list of word group info dicts
    - sentences: list of sentence info dicts
    """
    # Get verse node
    verse_node = api.T.nodeFromSection((book, chapter, verse))
    if verse_node is None:
        return None

    # Get all words in verse
    words = list(api.L.d(verse_node, otype='word'))
    word_set = set(words)

    structure = {
        'words': words,
        'clauses': [],
        'phrases': [],
        'wgs': [],
        'subphrases': [],
        'sentences': [],
        'groups': []
    }

    # For each word, find containing structures
    seen_nodes = set()

    for word in words:
        # Get all containing nodes
        for otype in ['clause', 'phrase', 'wg', 'subphrase', 'sentence', 'group']:
            containers = api.L.u(word, otype=otype)
            for container in containers:
                if container in seen_nodes:
                    continue
                seen_nodes.add(container)

                # Get all words in this container
                container_words = list(api.L.d(container, otype='word'))

                # Check if container is fully within this verse
                if not all(w in word_set for w in container_words):
                    # Container spans multiple verses - skip for now
                    continue

                # Extract features
                info = {
                    'node_id': container,
                    'otype': otype,
                    'word_nodes': container_words,
                    'word_indices': [words.index(w) for w in container_words],
                }

                # Add type-specific features
                if otype == 'clause':
                    info['clausetype'] = api.F.clausetype.v(container) if hasattr(api.F, 'clausetype') else None
                    info['cltype'] = api.F.cltype.v(container) if hasattr(api.F, 'cltype') else None
                    info['typ'] = api.F.typ.v(container) if hasattr(api.F, 'typ') else None
                    structure['clauses'].append(info)

                elif otype == 'phrase':
                    info['typ'] = api.F.typ.v(container) if hasattr(api.F, 'typ') else None
                    info['function'] = api.F.function.v(container) if hasattr(api.F, 'function') else None
                    info['rela'] = api.F.rela.v(container) if hasattr(api.F, 'rela') else None
                    structure['phrases'].append(info)

                elif otype == 'wg':
                    info['typ'] = api.F.typ.v(container) if hasattr(api.F, 'typ') else None
                    info['function'] = api.F.function.v(container) if hasattr(api.F, 'function') else None
                    info['rela'] = api.F.rela.v(container) if hasattr(api.F, 'rela') else None
                    info['rule'] = api.F.rule.v(container) if hasattr(api.F, 'rule') else None
                    structure['wgs'].append(info)

                elif otype == 'subphrase':
                    info['typ'] = api.F.typ.v(container) if hasattr(api.F, 'typ') else None
                    info['rela'] = api.F.rela.v(container) if hasattr(api.F, 'rela') else None
                    structure['subphrases'].append(info)

                elif otype == 'sentence':
                    structure['sentences'].append(info)

                elif otype == 'group':
                    info['typ'] = api.F.typ.v(container) if hasattr(api.F, 'typ') else None
                    structure['groups'].append(info)

    return structure


def transplant_verse_structure(
    verse_structure: dict,
    n1904_to_tr_map: dict,
    tr_word_ids: list
) -> dict:
    """
    Remap N1904 structure to TR word space.

    Args:
        verse_structure: Structure from get_verse_structure()
        n1904_to_tr_map: Dict mapping N1904 word node -> TR word_id
        tr_word_ids: List of TR word IDs in verse order

    Returns:
        Transplanted structure with TR word references
    """
    transplanted = {
        'clauses': [],
        'phrases': [],
        'wgs': [],
        'subphrases': [],
        'sentences': [],
        'groups': [],
        'source': 'n1904_direct',
        'confidence': 1.0
    }

    for otype in ['clauses', 'phrases', 'wgs', 'subphrases', 'sentences', 'groups']:
        for item in verse_structure.get(otype, []):
            # Map N1904 word nodes to TR word IDs
            tr_words = []
            for n1904_word in item['word_nodes']:
                if n1904_word in n1904_to_tr_map:
                    tr_words.append(n1904_to_tr_map[n1904_word])

            if not tr_words:
                continue

            # Create transplanted item
            new_item = {
                'n1904_node_id': item['node_id'],
                'otype': item['otype'],
                'tr_word_ids': tr_words,
                'source': 'n1904_direct',
                'confidence': 1.0
            }

            # Copy features
            for key in ['clausetype', 'cltype', 'typ', 'function', 'rela', 'rule']:
                if key in item:
                    new_item[key] = item[key]

            transplanted[otype].append(new_item)

    return transplanted


def main(config=None):
    """Main entry point."""
    config = load_config()

    with ScriptLogger('p4_08b_transplant_structure') as logger:
        # Load classified data
        logger.info("Loading classified TR data...")
        tr = pd.read_parquet('data/intermediate/tr_structure_classified.parquet')
        verse_stats = pd.read_parquet('data/intermediate/verse_structure_stats.parquet')

        # Get verses eligible for direct transplant
        direct_verses = verse_stats[verse_stats['category'] == 'direct_transplant']
        logger.info(f"Verses for direct transplant: {len(direct_verses):,}")

        # Load N1904
        logger.info("Loading N1904...")
        TF = load_n1904(config)
        api = TF.api

        # Build N1904 word node to TR word_id mapping for aligned words
        logger.info("Building word mapping...")
        aligned = tr[tr['n1904_node_id'].notna()]
        n1904_to_tr = dict(zip(
            aligned['n1904_node_id'].astype(int),
            aligned['word_id']
        ))
        logger.info(f"  Mapped {len(n1904_to_tr):,} aligned words")

        # Book name mapping (TR uses abbreviations, N1904 uses full names)
        book_map = {
            'MAT': 'Matthew', 'MAR': 'Mark', 'LUK': 'Luke', 'JHN': 'John',
            'ACT': 'Acts', 'ROM': 'Romans', '1CO': 'I_Corinthians', '2CO': 'II_Corinthians',
            'GAL': 'Galatians', 'EPH': 'Ephesians', 'PHP': 'Philippians', 'COL': 'Colossians',
            '1TH': 'I_Thessalonians', '2TH': 'II_Thessalonians', '1TI': 'I_Timothy', '2TI': 'II_Timothy',
            'TIT': 'Titus', 'PHM': 'Philemon', 'HEB': 'Hebrews', 'JAS': 'James',
            '1PE': 'I_Peter', '2PE': 'II_Peter', '1JN': 'I_John', '2JN': 'II_John',
            '3JN': 'III_John', 'JUD': 'Jude', 'REV': 'Revelation'
        }

        # Process each verse
        all_structures = []
        success_count = 0
        skip_count = 0

        logger.info("Transplanting structure...")
        for _, row in direct_verses.iterrows():
            book = row['book']
            chapter = int(row['chapter'])
            verse = int(row['verse'])

            # Get N1904 book name
            n1904_book = book_map.get(book)
            if not n1904_book:
                logger.warning(f"Unknown book: {book}")
                skip_count += 1
                continue

            # Get verse structure from N1904
            structure = get_verse_structure(api, n1904_book, chapter, verse)
            if structure is None:
                skip_count += 1
                continue

            # Get TR word IDs for this verse
            verse_tr = tr[(tr['book'] == book) &
                         (tr['chapter'] == chapter) &
                         (tr['verse'] == verse)]
            tr_word_ids = verse_tr['word_id'].tolist()

            # Build N1904-to-TR map for this verse
            verse_map = {}
            for _, word_row in verse_tr.iterrows():
                if pd.notna(word_row['n1904_node_id']):
                    verse_map[int(word_row['n1904_node_id'])] = word_row['word_id']

            # Transplant structure
            transplanted = transplant_verse_structure(structure, verse_map, tr_word_ids)
            transplanted['book'] = book
            transplanted['chapter'] = chapter
            transplanted['verse'] = verse

            all_structures.append(transplanted)
            success_count += 1

            if success_count % 500 == 0:
                logger.info(f"  Processed {success_count:,} verses...")

        logger.info(f"Transplanted: {success_count:,} verses")
        logger.info(f"Skipped: {skip_count:,} verses")

        # Count structures
        total_clauses = sum(len(s['clauses']) for s in all_structures)
        total_phrases = sum(len(s['phrases']) for s in all_structures)
        total_wgs = sum(len(s['wgs']) for s in all_structures)

        logger.info(f"\nTransplanted structures:")
        logger.info(f"  Clauses: {total_clauses:,}")
        logger.info(f"  Phrases: {total_phrases:,}")
        logger.info(f"  Word groups: {total_wgs:,}")

        # Save results
        output_path = Path('data/intermediate/tr_structure_direct.json')
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_structures, f, indent=2, ensure_ascii=False)
        logger.info(f"\nSaved to: {output_path}")

        # Also save as summary parquet
        summary_rows = []
        for s in all_structures:
            summary_rows.append({
                'book': s['book'],
                'chapter': s['chapter'],
                'verse': s['verse'],
                'num_clauses': len(s['clauses']),
                'num_phrases': len(s['phrases']),
                'num_wgs': len(s['wgs']),
                'source': s['source'],
                'confidence': s['confidence']
            })

        summary_df = pd.DataFrame(summary_rows)
        summary_path = Path('data/intermediate/tr_structure_direct_summary.parquet')
        summary_df.to_parquet(summary_path, index=False)
        logger.info(f"Saved summary to: {summary_path}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
