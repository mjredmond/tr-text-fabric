#!/usr/bin/env python3
"""
Phase 4 Step 8f: Integrate Structure into TF Dataset

Updates otype.tf and oslots.tf to include clause, phrase, and wg nodes.
"""

import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.utils.logging import ScriptLogger
from scripts.utils.config import load_config


def update_otype_file(complete_df: pd.DataFrame, containers_df: pd.DataFrame,
                      structure_df: pd.DataFrame, output_dir: Path) -> dict:
    """
    Regenerate otype.tf to include all node types with contiguous ranges.

    Returns:
        Node ID mapping: {old_id: new_id} for renumbering
    """
    otype_path = output_dir / 'otype.tf'

    max_word = len(complete_df)
    node_map = {}  # old_id -> new_id

    # Count nodes by type
    num_verses = len(containers_df[containers_df['otype'] == 'verse'])
    num_chapters = len(containers_df[containers_df['otype'] == 'chapter'])
    num_books = len(containers_df[containers_df['otype'] == 'book'])
    num_clauses = len(structure_df[structure_df['otype'] == 'clause'])
    num_phrases = len(structure_df[structure_df['otype'] == 'phrase'])
    num_wgs = len(structure_df[structure_df['otype'] == 'wg'])

    # Assign contiguous ranges
    # TF otype order: slots first, then larger containers
    # Words (slots): 1 to max_word
    word_start, word_end = 1, max_word

    # Section containers (in order: verse, chapter, book)
    verse_start = max_word + 1
    verse_end = verse_start + num_verses - 1

    chapter_start = verse_end + 1
    chapter_end = chapter_start + num_chapters - 1

    book_start = chapter_end + 1
    book_end = book_start + num_books - 1

    # Structure containers
    clause_start = book_end + 1
    clause_end = clause_start + num_clauses - 1

    phrase_start = clause_end + 1
    phrase_end = phrase_start + num_phrases - 1

    wg_start = phrase_end + 1
    wg_end = wg_start + num_wgs - 1

    # Build node mapping
    # Map container nodes
    next_verse = verse_start
    next_chapter = chapter_start
    next_book = book_start

    for _, row in containers_df.sort_values(['otype', 'node_id']).iterrows():
        old_id = row['node_id']
        if row['otype'] == 'verse':
            node_map[old_id] = next_verse
            next_verse += 1
        elif row['otype'] == 'chapter':
            node_map[old_id] = next_chapter
            next_chapter += 1
        elif row['otype'] == 'book':
            node_map[old_id] = next_book
            next_book += 1

    # Map structure nodes
    next_clause = clause_start
    next_phrase = phrase_start
    next_wg = wg_start

    for _, row in structure_df.sort_values(['otype', 'node_id']).iterrows():
        old_id = row['node_id']
        if row['otype'] == 'clause':
            node_map[old_id] = next_clause
            next_clause += 1
        elif row['otype'] == 'phrase':
            node_map[old_id] = next_phrase
            next_phrase += 1
        elif row['otype'] == 'wg':
            node_map[old_id] = next_wg
            next_wg += 1

    # Write otype.tf
    with open(otype_path, 'w', encoding='utf-8') as f:
        f.write("@node\n")
        f.write("@description=node type assignment\n")
        f.write("@valueType=str\n")
        f.write("\n")

        f.write(f"{word_start}-{word_end}\tw\n")
        if num_verses > 0:
            f.write(f"{verse_start}-{verse_end}\tverse\n")
        if num_chapters > 0:
            f.write(f"{chapter_start}-{chapter_end}\tchapter\n")
        if num_books > 0:
            f.write(f"{book_start}-{book_end}\tbook\n")
        if num_clauses > 0:
            f.write(f"{clause_start}-{clause_end}\tclause\n")
        if num_phrases > 0:
            f.write(f"{phrase_start}-{phrase_end}\tphrase\n")
        if num_wgs > 0:
            f.write(f"{wg_start}-{wg_end}\twg\n")

    return node_map


def update_oslots_file(complete_df: pd.DataFrame, containers_df: pd.DataFrame,
                       structure_df: pd.DataFrame, node_map: dict, output_dir: Path):
    """
    Regenerate oslots.tf to include structure node containment with remapped IDs.
    """
    oslots_path = output_dir / 'oslots.tf'

    # Build slot map (word_id to sequential slot)
    complete_df = complete_df.sort_values(
        ['book', 'chapter', 'verse', 'word_rank']
    ).reset_index(drop=True)
    slot_map = {row['word_id']: idx + 1 for idx, row in complete_df.iterrows()}

    # Collect all oslots entries, then sort by new node_id
    oslots_entries = []

    # Containers (verses, chapters, books)
    for _, container in containers_df.iterrows():
        old_id = container['node_id']
        new_id = node_map.get(old_id, old_id)
        first_slot = slot_map.get(container['first_slot'], container['first_slot'])
        last_slot = slot_map.get(container['last_slot'], container['last_slot'])
        oslots_entries.append((new_id, first_slot, last_slot))

    # Structure nodes
    for _, node in structure_df.iterrows():
        old_id = node['node_id']
        new_id = node_map.get(old_id, old_id)
        first_slot = node['first_slot']
        last_slot = node['last_slot']
        oslots_entries.append((new_id, first_slot, last_slot))

    # Sort by new node_id and write
    with open(oslots_path, 'w', encoding='utf-8') as f:
        f.write("@edge\n")
        f.write("@description=slot containment for non-slot nodes\n")
        f.write("@valueType=str\n")
        f.write("\n")

        for new_id, first_slot, last_slot in sorted(oslots_entries):
            if first_slot == last_slot:
                f.write(f"{new_id}\t{first_slot}\n")
            else:
                f.write(f"{new_id}\t{first_slot}-{last_slot}\n")


def regenerate_section_features(complete_df: pd.DataFrame, containers_df: pd.DataFrame,
                                structure_df: pd.DataFrame, node_map: dict, output_dir: Path):
    """
    Regenerate section feature files with remapped node IDs.
    """
    book_name_map = {
        'MAT': 'Matthew', 'MAR': 'Mark', 'LUK': 'Luke', 'JHN': 'John',
        'ACT': 'Acts', 'ROM': 'Romans', '1CO': 'I_Corinthians', '2CO': 'II_Corinthians',
        'GAL': 'Galatians', 'EPH': 'Ephesians', 'PHP': 'Philippians', 'COL': 'Colossians',
        '1TH': 'I_Thessalonians', '2TH': 'II_Thessalonians', '1TI': 'I_Timothy',
        '2TI': 'II_Timothy', 'TIT': 'Titus', 'PHM': 'Philemon', 'HEB': 'Hebrews',
        'JAS': 'James', '1PE': 'I_Peter', '2PE': 'II_Peter', '1JN': 'I_John',
        '2JN': 'II_John', '3JN': 'III_John', 'JUD': 'Jude', 'REV': 'Revelation'
    }

    # Build slot map
    complete_df = complete_df.sort_values(
        ['book', 'chapter', 'verse', 'word_rank']
    ).reset_index(drop=True)

    for feat_name in ['book', 'chapter', 'verse']:
        feat_path = output_dir / f'{feat_name}.tf'
        entries = []

        # Word nodes (slots 1 to max_word)
        for idx, row in complete_df.iterrows():
            slot = idx + 1
            if feat_name == 'book':
                book_abbrev = str(row['book'])
                value = book_name_map.get(book_abbrev, book_abbrev)
            elif feat_name == 'chapter':
                value = int(row['chapter'])
            else:  # verse
                value = int(row['verse'])
            entries.append((slot, value))

        # Container nodes (remapped)
        for _, container in containers_df.iterrows():
            old_id = container['node_id']
            new_id = node_map.get(old_id, old_id)
            otype = container['otype']

            if feat_name == 'book' and otype == 'book':
                book_abbrev = str(container['name'])
                value = book_name_map.get(book_abbrev, book_abbrev)
                entries.append((new_id, value))
            elif feat_name == 'chapter' and otype == 'chapter':
                value = int(container['chapter'])
                entries.append((new_id, value))
            elif feat_name == 'verse' and otype == 'verse':
                value = int(container['verse'])
                entries.append((new_id, value))

        # Structure nodes (remapped)
        for _, node in structure_df.iterrows():
            old_id = node['node_id']
            new_id = node_map.get(old_id, old_id)

            if feat_name == 'book':
                book_abbrev = node['book']
                value = book_name_map.get(book_abbrev, book_abbrev)
            elif feat_name == 'chapter':
                value = int(node['chapter'])
            else:  # verse
                value = int(node['verse'])
            entries.append((new_id, value))

        # Write sorted by node_id
        with open(feat_path, 'w', encoding='utf-8') as f:
            f.write("@node\n")
            if feat_name == 'book':
                f.write("@description=book name (full)\n")
                f.write("@valueType=str\n")
            elif feat_name == 'chapter':
                f.write("@description=chapter number\n")
                f.write("@valueType=int\n")
            else:
                f.write("@description=verse number\n")
                f.write("@valueType=int\n")
            f.write("\n")

            for node_id, value in sorted(entries):
                f.write(f"{node_id}\t{value}\n")


def regenerate_structure_features(structure_df: pd.DataFrame, node_map: dict, output_dir: Path):
    """
    Regenerate structure-specific feature files with remapped node IDs.
    """
    features = {
        'typ': 'syntactic type of phrase/clause',
        'function': 'syntactic function of phrase/word group',
        'rela': 'relation to context',
        'clausetype': 'clause type',
        'rule': 'syntactic rule for word group',
        'structure_source': 'source of structure (direct/inferred/unknown_only)',
        'structure_confidence': 'confidence score for structure inference (0-1)',
    }

    for feat_name, desc in features.items():
        feat_path = output_dir / f'{feat_name}.tf'
        entries = []

        col_name = feat_name
        if col_name not in structure_df.columns:
            continue

        for _, node in structure_df.iterrows():
            old_id = node['node_id']
            new_id = node_map.get(old_id, old_id)
            value = node.get(col_name)

            if pd.notna(value) and value != '':
                entries.append((new_id, value))

        if not entries:
            continue

        with open(feat_path, 'w', encoding='utf-8') as f:
            f.write("@node\n")
            f.write(f"@description={desc}\n")
            if feat_name == 'structure_confidence':
                f.write("@valueType=float\n")
            else:
                f.write("@valueType=str\n")
            f.write("\n")

            for node_id, value in sorted(entries):
                if feat_name == 'structure_confidence':
                    f.write(f"{node_id}\t{float(value):.2f}\n")
                else:
                    f.write(f"{node_id}\t{value}\n")


def main(config=None):
    """Main entry point."""
    config = load_config()

    with ScriptLogger('p4_08f_integrate_structure') as logger:
        # Load data
        logger.info("Loading data...")
        complete = pd.read_parquet('data/intermediate/tr_complete.parquet')
        containers = pd.read_parquet('data/intermediate/tr_containers.parquet')
        structure = pd.read_parquet('data/intermediate/tr_structure_nodes.parquet')

        logger.info(f"  Words: {len(complete):,}")
        logger.info(f"  Containers: {len(containers):,}")
        logger.info(f"  Structure nodes: {len(structure):,}")

        output_dir = Path('data/output/tf')

        # Update otype.tf and get node mapping
        logger.info("Regenerating otype.tf with contiguous ranges...")
        node_map = update_otype_file(complete, containers, structure, output_dir)
        logger.info(f"  Remapped {len(node_map):,} non-slot nodes")

        # Update oslots.tf with remapped IDs
        logger.info("Regenerating oslots.tf...")
        update_oslots_file(complete, containers, structure, node_map, output_dir)

        # Regenerate section features with remapped IDs
        logger.info("Regenerating section features...")
        regenerate_section_features(complete, containers, structure, node_map, output_dir)

        # Regenerate structure-specific features with remapped IDs
        logger.info("Regenerating structure features...")
        regenerate_structure_features(structure, node_map, output_dir)

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("INTEGRATION COMPLETE")
        logger.info("=" * 60)

        # Verify otype counts
        otype_counts = structure['otype'].value_counts()
        logger.info("Structure nodes added:")
        for otype, count in otype_counts.items():
            logger.info(f"  {otype}: {count:,}")

        total_nodes = len(complete) + len(containers) + len(structure)
        logger.info(f"\nTotal TF nodes: {total_nodes:,}")
        logger.info(f"  Words (slots): {len(complete):,}")
        logger.info(f"  Section containers: {len(containers):,}")
        logger.info(f"  Structure nodes: {len(structure):,}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
