#!/usr/bin/env python3
"""
Phase 4 Step 8d: Handle Unknown Words

For the 2.8% of words not found in N1904:
1. Map elided forms to their full forms
2. Use Strong's numbers to find equivalent N1904 words
3. Default proper names to NP
"""

import pandas as pd
import json
from pathlib import Path
import sys
import re
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.utils.logging import ScriptLogger


# Elision mappings: elided form -> (full form, phrase_type, function)
ELISION_MAP = {
    # Conjunctions - typically at clause level
    "ἀλλ᾽": ("ἀλλά", None, None),
    "δ᾽": ("δέ", None, None),
    "οὐδ᾽": ("οὐδέ", None, None),
    "μηδ᾽": ("μηδέ", None, None),

    # Prepositions - start PP
    "δι᾽": ("διά", "PP", "Cmpl"),
    "ἐπ᾽": ("ἐπί", "PP", "Cmpl"),
    "ἀπ᾽": ("ἀπό", "PP", "Cmpl"),
    "μετ᾽": ("μετά", "PP", "Cmpl"),
    "κατ᾽": ("κατά", "PP", "Cmpl"),
    "ἐφ᾽": ("ἐπί", "PP", "Cmpl"),
    "καθ᾽": ("κατά", "PP", "Cmpl"),
    "παρ᾽": ("παρά", "PP", "Cmpl"),
    "μεθ᾽": ("μετά", "PP", "Cmpl"),
    "ἀφ᾽": ("ἀπό", "PP", "Cmpl"),
    "ὑπ᾽": ("ὑπό", "PP", "Cmpl"),
    "ὑφ᾽": ("ὑπό", "PP", "Cmpl"),
    "ἀνθ᾽": ("ἀντί", "PP", "Cmpl"),

    # Demonstratives/pronouns - typically in NP
    "τοῦτ᾽": ("τοῦτο", "NP", None),
    "ταῦτ᾽": ("ταῦτα", "NP", None),
    "ἐκεῖν᾽": ("ἐκεῖνο", "NP", None),

    # Other
    "ποτ᾽": ("ποτέ", "AdvP", "Cmpl"),
    "οὔτ᾽": ("οὔτε", None, None),
    "μήτ᾽": ("μήτε", None, None),
}

# Strong's numbers for common prepositions/conjunctions
STRONG_PHRASE_MAP = {
    # Prepositions -> PP
    "G1223": ("PP", "Cmpl"),  # διά
    "G1519": ("PP", "Cmpl"),  # εἰς
    "G1537": ("PP", "Cmpl"),  # ἐκ
    "G1722": ("PP", "Cmpl"),  # ἐν
    "G1909": ("PP", "Cmpl"),  # ἐπί
    "G2596": ("PP", "Cmpl"),  # κατά
    "G3326": ("PP", "Cmpl"),  # μετά
    "G3844": ("PP", "Cmpl"),  # παρά
    "G4012": ("PP", "Cmpl"),  # περί
    "G4314": ("PP", "Cmpl"),  # πρός
    "G5228": ("PP", "Cmpl"),  # ὑπέρ
    "G5259": ("PP", "Cmpl"),  # ὑπό
    "G575": ("PP", "Cmpl"),   # ἀπό

    # Conjunctions - clause level
    "G235": (None, None),     # ἀλλά
    "G1063": (None, None),    # γάρ
    "G1161": (None, None),    # δέ
    "G2228": (None, None),    # ἤ
    "G2532": (None, None),    # καί
    "G3767": (None, None),    # οὖν

    # Relatives - typically in clause
    "G3739": (None, "Subj"),  # ὅς, ἥ, ὅ

    # Demonstratives - NP
    "G3778": ("NP", None),    # οὗτος
    "G1565": ("NP", None),    # ἐκεῖνος
    "G5124": ("NP", None),    # τοῦτο

    # Numerals - NP
    "G1427": ("NP", None),    # δώδεκα
    "G5062": ("NP", None),    # τεσσαράκοντα
    "G5064": ("NP", None),    # τέσσαρες

    # Articles - NP
    "G3588": ("NP", None),    # ὁ, ἡ, τό (article)

    # Common adverbs - AdvP
    "G2112": ("AdvP", "Cmpl"),  # εὐθέως (immediately)
    "G3379": ("AdvP", "Cmpl"),  # μήποτε (lest)
    "G3381": ("AdvP", "Cmpl"),  # μήπως (lest somehow)
    "G5618": ("AdvP", "Cmpl"),  # ὥσπερ (just as)
    "G1275": ("AdvP", "Cmpl"),  # διαπαντός (always)

    # Common verbs - typically predicates
    "G2036": (None, "Pred"),   # εἶπον (said)
    "G4098": (None, "Pred"),   # πίπτω (fall)
    "G2983": (None, "Pred"),   # λαμβάνω (take)
    "G1831": (None, "Pred"),   # ἐξέρχομαι (go out)
    "G2064": (None, "Pred"),   # ἔρχομαι (come)
    "G1510": (None, "Pred"),   # εἰμί (be)
    "G353": (None, "Pred"),    # ἀναλαμβάνω (take up)
    "G599": (None, "Pred"),    # ἀποθνῄσκω (die)
    "G1632": (None, "Pred"),   # ἐκχέω (pour out)

    # Common pronouns/adjectives - NP
    "G3956": ("NP", None),     # πᾶς (all)
    "G846": ("NP", None),      # αὐτός (he/self)

    # Nouns - NP
    "G2895": ("NP", None),     # κράβαττος (bed)
    "G86": ("NP", None),       # ᾅδης (Hades)
    "G231": ("NP", None),      # ἁλιεύς (fisherman)
    "G3162": ("NP", None),     # μάχαιρα (sword)
    "G1766": ("NP", None),     # ἔνατος (ninth)
    "G4802": (None, None),     # συζητέω (discuss)
}

# Strong's numbers that indicate proper names
PROPER_NAME_STRONGS = set()  # Will be populated from data


def is_proper_name(word: str, strong: str) -> bool:
    """Check if a word is a proper name."""
    # Check if starts with uppercase (Greek capital)
    if word and word[0].isupper():
        return True

    # Check Strong's number pattern (names often have specific ranges)
    # Most Hebrew/Aramaic names are in certain ranges
    if strong:
        num = int(re.sub(r'[^0-9]', '', strong) or 0)
        # This is a heuristic - proper names often cluster
        # G2424 = Ἰησοῦς, G5547 = Χριστός, etc.

    return False


def get_full_form(word: str) -> str:
    """Get the full (non-elided) form of a word."""
    word_lower = word.lower()

    # Check direct mapping
    if word_lower in ELISION_MAP:
        return ELISION_MAP[word_lower]

    # Check with original case preserved
    if word in ELISION_MAP:
        return ELISION_MAP[word]

    # Check for elision marker and try to reconstruct
    if "᾽" in word or "'" in word:
        # Remove elision marker and try common endings
        base = word.replace("᾽", "").replace("'", "")
        # Try adding common vowel endings
        for ending in ["α", "ε", "ι", "ο", "η"]:
            candidate = base + ending
            return candidate  # Return first guess

    return word


def build_strong_to_phrase_map(n1904: pd.DataFrame) -> dict:
    """
    Build mapping from Strong's number to typical phrase info.

    Returns dict: Strong's -> {
        'typical_function': most common function,
        'typical_phrase_type': most common phrase type,
        'sp': most common part of speech,
        'is_name': whether it's typically a proper name
    }
    """
    strong_data = {}

    for _, row in n1904.iterrows():
        strong = row.get('strong')
        if not strong:
            continue

        if strong not in strong_data:
            strong_data[strong] = {
                'functions': Counter(),
                'sp': Counter(),
                'words': []
            }

        function = row.get('function')
        sp = row.get('sp')
        word = row.get('word', '')

        if function:
            strong_data[strong]['functions'][function] += 1
        if sp:
            strong_data[strong]['sp'][sp] += 1
        if word:
            strong_data[strong]['words'].append(word)

    # Compute typical values
    result = {}
    for strong, data in strong_data.items():
        result[strong] = {
            'typical_function': data['functions'].most_common(1)[0][0] if data['functions'] else None,
            'typical_sp': data['sp'].most_common(1)[0][0] if data['sp'] else None,
            'sample_word': data['words'][0] if data['words'] else None,
            'is_name': data['sp'].get('noun', 0) > 0 and any(w[0].isupper() for w in data['words'][:5] if w)
        }

    return result


def process_unknown_word(
    word: str,
    strong: str,
    strong_to_phrase: dict,
    n1904_words: set
) -> dict:
    """
    Determine structure assignment for an unknown word.

    Returns dict with:
    - resolved_form: the matched/resolved form
    - phrase_type: inferred phrase type
    - function: inferred function
    - confidence: confidence score
    - method: how it was resolved
    """
    result = {
        'original': word,
        'resolved_form': None,
        'phrase_type': None,
        'function': None,
        'confidence': 0.5,
        'method': 'unknown'
    }

    word_lower = word.lower()

    # 1. Try elision mapping (with phrase type info)
    if word_lower in ELISION_MAP:
        full_form, phrase_type, function = ELISION_MAP[word_lower]
        result['resolved_form'] = full_form
        result['phrase_type'] = phrase_type
        result['function'] = function
        result['method'] = 'elision_map'
        result['confidence'] = 0.95
        return result

    # 2. Try Strong's phrase mapping
    if strong and strong in STRONG_PHRASE_MAP:
        phrase_type, function = STRONG_PHRASE_MAP[strong]
        result['phrase_type'] = phrase_type
        result['function'] = function
        result['method'] = 'strong_phrase_map'
        result['confidence'] = 0.90
        return result

    # 3. Try N1904 Strong's data lookup
    if strong and strong in strong_to_phrase:
        info = strong_to_phrase[strong]
        result['function'] = info.get('typical_function')
        result['typical_sp'] = info.get('typical_sp')

        if info.get('is_name'):
            result['phrase_type'] = 'NP'
            result['function'] = result['function'] or 'Appo'
            result['method'] = 'strong_name'
            result['confidence'] = 0.9
            return result
        elif result['function']:
            result['method'] = 'strong_lookup'
            result['confidence'] = 0.85
            return result

    # 4. Check if proper name by capitalization
    if word and word[0].isupper():
        result['phrase_type'] = 'NP'
        result['method'] = 'capital_name'
        result['confidence'] = 0.85
        return result

    # 5. Default handling
    result['method'] = 'default'
    result['confidence'] = 0.5

    return result


def main():
    """Main entry point."""
    with ScriptLogger('p4_08d_handle_unknowns') as logger:
        # Load data
        logger.info("Loading data...")
        unknown_forms = pd.read_csv('data/intermediate/unknown_word_forms.csv')
        n1904 = pd.read_parquet('data/intermediate/n1904_words.parquet')
        tr = pd.read_parquet('data/intermediate/tr_structure_classified.parquet')

        logger.info(f"Unknown forms to process: {len(unknown_forms):,}")
        logger.info(f"Total unknown occurrences: {unknown_forms['count'].sum():,}")

        # Build lookups
        logger.info("Building Strong's lookup...")
        strong_to_phrase = build_strong_to_phrase_map(n1904)
        logger.info(f"  {len(strong_to_phrase):,} Strong's numbers mapped")

        # Build N1904 word set
        n1904_words = set(n1904['word'].str.lower().dropna())
        logger.info(f"  {len(n1904_words):,} unique N1904 word forms")

        # Process each unknown form
        logger.info("Processing unknown forms...")
        results = []
        method_counts = Counter()

        for _, row in unknown_forms.iterrows():
            word = row['word']
            strong = row['strong']
            count = row['count']

            result = process_unknown_word(word, strong, strong_to_phrase, n1904_words)
            result['count'] = count
            result['strong'] = strong
            results.append(result)
            method_counts[result['method']] += count

        # Summary
        logger.info("\nResolution methods (by occurrence count):")
        for method, count in method_counts.most_common():
            pct = count / unknown_forms['count'].sum() * 100
            logger.info(f"  {method}: {count:,} ({pct:.1f}%)")

        # Confidence distribution
        total_occ = unknown_forms['count'].sum()
        high_conf = sum(r['count'] for r in results if r['confidence'] >= 0.8)
        med_conf = sum(r['count'] for r in results if 0.6 <= r['confidence'] < 0.8)
        low_conf = sum(r['count'] for r in results if r['confidence'] < 0.6)

        logger.info(f"\nConfidence distribution:")
        logger.info(f"  High (>=80%): {high_conf:,} ({high_conf/total_occ*100:.1f}%)")
        logger.info(f"  Medium (60-80%): {med_conf:,} ({med_conf/total_occ*100:.1f}%)")
        logger.info(f"  Low (<60%): {low_conf:,} ({low_conf/total_occ*100:.1f}%)")

        # Save results
        output_path = Path('data/intermediate/unknown_word_resolutions.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"\nSaved to: {output_path}")

        # Also save as CSV for review
        results_df = pd.DataFrame(results)
        csv_path = Path('data/intermediate/unknown_word_resolutions.csv')
        results_df.to_csv(csv_path, index=False)
        logger.info(f"Saved CSV to: {csv_path}")

        # Show sample resolutions
        logger.info("\nSample resolutions:")
        for r in results[:15]:
            logger.info(f"  {r['original']} ({r['strong']}): {r['method']} -> conf={r['confidence']:.0%}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
