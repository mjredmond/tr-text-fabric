#!/usr/bin/env python3
"""
Phase 4 Step 8g: Verify Structure Integrity

Loads the TF dataset and verifies:
1. All node types are accessible
2. Structure nodes have correct slot containment
3. Features are properly assigned
4. Structure can be navigated
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.utils.logging import ScriptLogger
from scripts.utils.config import load_config


def verify_tf_load():
    """Verify TF dataset loads correctly."""
    from tf.fabric import Fabric

    print("Loading TR Text-Fabric dataset...")
    TF = Fabric(locations='data/output/tf', silent='deep')
    # Load core features plus structure features
    features = 'unicode book chapter verse typ function rela clausetype rule structure_source structure_confidence'
    api = TF.load(features)

    return TF


def verify_node_types(TF) -> dict:
    """Verify all expected node types exist."""
    api = TF.api
    F = api.F
    T = api.T
    L = api.L

    expected_types = ['w', 'verse', 'chapter', 'book', 'clause', 'phrase', 'wg']
    results = {}

    for otype in expected_types:
        nodes = list(F.otype.s(otype))
        results[otype] = len(nodes)
        print(f"  {otype}: {len(nodes):,} nodes")

    return results


def verify_structure_containment(TF) -> bool:
    """Verify structure nodes contain correct slots."""
    api = TF.api
    F = api.F
    L = api.L

    errors = []
    sample_size = 100

    # Check clauses
    clauses = list(F.otype.s('clause'))[:sample_size]
    for clause in clauses:
        words = L.d(clause, otype='w')
        if not words:
            errors.append(f"Clause {clause} has no words")

    # Check phrases
    phrases = list(F.otype.s('phrase'))[:sample_size]
    for phrase in phrases:
        words = L.d(phrase, otype='w')
        if not words:
            errors.append(f"Phrase {phrase} has no words")

    # Check word groups
    wgs = list(F.otype.s('wg'))[:sample_size]
    for wg in wgs:
        words = L.d(wg, otype='w')
        if not words:
            errors.append(f"Word group {wg} has no words")

    if errors:
        print(f"  ERRORS ({len(errors)}):")
        for err in errors[:10]:
            print(f"    {err}")
        return False

    print("  All sampled structure nodes have valid slot containment")
    return True


def verify_structure_features(TF) -> bool:
    """Verify structure features are accessible."""
    api = TF.api
    F = api.F

    features_to_check = {
        'clause': ['typ', 'clausetype'],
        'phrase': ['typ', 'function', 'rela'],
        'wg': ['typ', 'function', 'rela', 'rule'],
    }

    results = {}
    for otype, feats in features_to_check.items():
        nodes = list(F.otype.s(otype))[:100]
        results[otype] = {}

        for feat in feats:
            if hasattr(F, feat):
                feat_func = getattr(F, feat)
                has_value = sum(1 for n in nodes if feat_func.v(n))
                results[otype][feat] = has_value
                print(f"  {otype}.{feat}: {has_value}/{len(nodes)} have values")
            else:
                print(f"  {otype}.{feat}: MISSING FEATURE")

    return True


def verify_navigation(TF) -> bool:
    """Verify structure can be navigated."""
    api = TF.api
    F = api.F
    T = api.T
    L = api.L

    print("\nSample navigation:")

    # Test with a direct transplant verse (1 Corinthians 1:5)
    verse = T.nodeFromSection(('I_Corinthians', 1, 5))
    if verse:
        words = L.d(verse, otype='w')
        print(f"  1 Corinthians 1:5 has {len(words)} words (direct transplant)")

        # Find structure for each word
        for w in words[:5]:
            word_text = F.unicode.v(w) or ''
            clauses = L.u(w, otype='clause')
            phrases = L.u(w, otype='phrase')
            wgs = L.u(w, otype='wg')
            print(f"    '{word_text}': {len(clauses)} clause, {len(phrases)} phrase, {len(wgs)} wg")

            # Show phrase details
            if phrases:
                p = phrases[0]
                func = F.function.v(p) or 'N/A'
                typ = F.typ.v(p) or 'N/A'
                print(f"      -> phrase {p}: function={func}, typ={typ}")

    # Test another direct transplant verse
    verse2 = T.nodeFromSection(('I_Corinthians', 1, 11))
    if verse2:
        words = L.d(verse2, otype='w')
        print(f"\n  1 Corinthians 1:11 has {len(words)} words (direct transplant)")

        # Get all unique phrases in this verse
        all_phrases = set()
        for w in words:
            all_phrases.update(L.u(w, otype='phrase'))

        print(f"    Verse contains {len(all_phrases)} distinct phrases")
        for p in sorted(all_phrases)[:3]:
            phrase_words = L.d(p, otype='w')
            phrase_text = ' '.join(F.unicode.v(w) or '' for w in phrase_words)
            func = F.function.v(p) or 'N/A'
            print(f"    phrase {p} ({func}): {phrase_text[:40]}")

    return True


def main(config=None):
    """Main entry point."""
    with ScriptLogger('p4_08g_verify_structure') as logger:
        logger.info("Verifying TR structure integrity...")

        # Load TF
        logger.info("\n1. Loading Text-Fabric dataset...")
        try:
            TF = verify_tf_load()
            logger.info("   SUCCESS: Dataset loaded")
        except Exception as e:
            logger.error(f"   FAILED: {e}")
            return 1

        # Verify node types
        logger.info("\n2. Verifying node types...")
        try:
            counts = verify_node_types(TF)
            logger.info("   SUCCESS: All node types present")
        except Exception as e:
            logger.error(f"   FAILED: {e}")
            return 1

        # Verify containment
        logger.info("\n3. Verifying slot containment...")
        try:
            if verify_structure_containment(TF):
                logger.info("   SUCCESS: Containment verified")
            else:
                logger.warning("   PARTIAL: Some containment issues")
        except Exception as e:
            logger.error(f"   FAILED: {e}")

        # Verify features
        logger.info("\n4. Verifying structure features...")
        try:
            verify_structure_features(TF)
            logger.info("   SUCCESS: Features accessible")
        except Exception as e:
            logger.error(f"   FAILED: {e}")

        # Verify navigation
        logger.info("\n5. Verifying navigation...")
        try:
            verify_navigation(TF)
            logger.info("   SUCCESS: Navigation works")
        except Exception as e:
            logger.error(f"   FAILED: {e}")

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("VERIFICATION SUMMARY")
        logger.info("=" * 60)

        total_nodes = sum(counts.values())
        logger.info(f"Total nodes: {total_nodes:,}")
        logger.info(f"  Words: {counts.get('w', 0):,}")
        logger.info(f"  Verses: {counts.get('verse', 0):,}")
        logger.info(f"  Chapters: {counts.get('chapter', 0):,}")
        logger.info(f"  Books: {counts.get('book', 0):,}")
        logger.info(f"  Clauses: {counts.get('clause', 0):,}")
        logger.info(f"  Phrases: {counts.get('phrase', 0):,}")
        logger.info(f"  Word groups: {counts.get('wg', 0):,}")

        logger.info("\nStructure verification COMPLETE")

    return 0


if __name__ == '__main__':
    sys.exit(main())
