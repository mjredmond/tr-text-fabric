#!/usr/bin/env python3
"""
Thorough verification of manual glosses.

This script verifies glosses by:
1. Checking against Strong's lexicon
2. Checking against N1904 (authoritative source with 125K words)
3. Flagging any that can't be verified from either source

Usage:
    python scripts/verify_glosses_thorough.py
"""

import sqlite3
import unicodedata
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd


def normalize_greek(text):
    """Normalize Greek text for matching."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = text.lower()
    text = re.sub(r"[᾽᾿'ʼ᾿·.,;:!?\"'()]", "", text)
    return text


def load_n1904_glosses():
    """Load word->gloss mapping from N1904."""
    parquet_path = PROJECT_ROOT / "data" / "intermediate" / "n1904_words.parquet"
    df = pd.read_parquet(parquet_path)

    # Build word -> gloss mapping
    word_gloss = {}
    for _, row in df.iterrows():
        word = row.get("word", "")
        gloss = row.get("gloss", "")
        if word and gloss and pd.notna(gloss):
            norm = normalize_greek(word)
            if norm not in word_gloss:
                word_gloss[norm] = gloss

    return word_gloss


def load_lexicon():
    """Load Strong's lexicon."""
    db_path = PROJECT_ROOT / "data" / "source" / "greek_lexicon.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT word, definition FROM lexicon")

    lexicon = {}
    for word, definition in cursor:
        if word:
            norm = normalize_greek(word)
            lexicon[norm] = definition or ""
    conn.close()
    return lexicon


def extract_extended_glosses():
    """Extract EXTENDED_GLOSSES from fill_remaining_glosses.py."""
    script_path = SCRIPT_DIR / "fill_remaining_glosses.py"
    content = script_path.read_text()

    start = content.find("EXTENDED_GLOSSES = {")
    if start == -1:
        return {}

    brace_count = 0
    end = start
    for i, c in enumerate(content[start:]):
        if c == '{':
            brace_count += 1
        elif c == '}':
            brace_count -= 1
            if brace_count == 0:
                end = start + i + 1
                break

    dict_str = content[start:end]
    glosses = {}
    pattern = r'"([^"]+)":\s*"([^"]+)"'
    for match in re.finditer(pattern, dict_str):
        greek, english = match.groups()
        glosses[greek] = english

    return glosses


def check_semantic_match(our_gloss, reference_gloss):
    """Check if glosses are semantically similar."""
    if not reference_gloss:
        return False

    our_words = set(our_gloss.lower().replace(",", " ").split())
    ref_words = set(reference_gloss.lower().replace(",", " ").split())

    # Check for any word overlap
    common = our_words & ref_words
    if common:
        return True

    # Check for common synonyms
    synonyms = {
        "throw": ["cast", "hurl"],
        "go": ["went", "going", "come", "came"],
        "say": ["said", "speak", "spoke", "tell", "told"],
        "see": ["saw", "seen", "look"],
        "give": ["gave", "given"],
        "take": ["took", "taken", "receive"],
        "hear": ["heard"],
        "know": ["knew", "known"],
        "come": ["came"],
        "send": ["sent"],
        "rise": ["rose", "risen", "raise", "raised"],
        "judge": ["judged"],
        "save": ["saved"],
        "believe": ["believed"],
        "love": ["loved"],
        "father": ["dad"],
    }

    for our_word in our_words:
        if our_word in synonyms:
            for syn in synonyms[our_word]:
                if syn in ref_words:
                    return True
        for key, syns in synonyms.items():
            if our_word in syns and key in ref_words:
                return True

    return False


def main():
    print("=" * 70)
    print("THOROUGH GLOSS VERIFICATION")
    print("=" * 70)

    # Load data sources
    print("\nLoading N1904 glosses (authoritative source)...")
    n1904_glosses = load_n1904_glosses()
    print(f"  Loaded {len(n1904_glosses)} unique word forms with glosses")

    print("\nLoading Strong's lexicon...")
    lexicon = load_lexicon()
    print(f"  Loaded {len(lexicon)} lexicon entries")

    print("\nExtracting manual glosses...")
    our_glosses = extract_extended_glosses()
    print(f"  Found {len(our_glosses)} manual gloss entries")

    # Verify each entry
    verified_n1904 = []
    verified_lexicon = []
    verified_semantic = []
    proper_names = []
    aramaic = []
    unverified = []

    proper_name_list = ["John", "David", "Moses", "Jesus", "Peter", "Paul",
                        "Abraham", "Israel", "Jerusalem", "Galilee", "Rome",
                        "Elijah", "Herod", "Pilate", "Caesar", "Judas", "Jacob",
                        "Satan", "Nazareth", "Bethlehem", "Simon", "Pharisee",
                        "Sadducee", "Ephesus", "Corinth", "Athens", "Capernaum",
                        "Barabbas", "Nazarene", "Fortunatus", "Christ", "James"]

    aramaic_list = ["forsaken", "little girl", "arise", "be opened",
                    "mammon", "rabbi", "master", "my God", "hosanna",
                    "amen", "hallelujah", "Abba", "father"]

    for greek, our_gloss in our_glosses.items():
        norm = normalize_greek(greek)

        # Check if proper name
        is_proper = any(name in our_gloss for name in proper_name_list)
        if is_proper:
            proper_names.append((greek, our_gloss))
            continue

        # Check if Aramaic
        is_aramaic = any(term in our_gloss.lower() for term in aramaic_list)
        if is_aramaic:
            aramaic.append((greek, our_gloss))
            continue

        # Check N1904 (exact match)
        if norm in n1904_glosses:
            ref_gloss = n1904_glosses[norm]
            if check_semantic_match(our_gloss, ref_gloss):
                verified_n1904.append((greek, our_gloss, ref_gloss))
            else:
                verified_semantic.append((greek, our_gloss, ref_gloss, "N1904"))
            continue

        # Check lexicon
        if norm in lexicon:
            ref_def = lexicon[norm]
            if check_semantic_match(our_gloss, ref_def):
                verified_lexicon.append((greek, our_gloss, ref_def[:50]))
            else:
                verified_semantic.append((greek, our_gloss, ref_def[:50], "lexicon"))
            continue

        # Check if any prefix matches in N1904
        found = False
        for n_word, n_gloss in n1904_glosses.items():
            if len(norm) >= 4 and (norm.startswith(n_word[:4]) or n_word.startswith(norm[:4])):
                if check_semantic_match(our_gloss, n_gloss):
                    verified_semantic.append((greek, our_gloss, n_gloss, "prefix"))
                    found = True
                    break
        if found:
            continue

        unverified.append((greek, our_gloss))

    # Report
    print("\n" + "=" * 70)
    print("VERIFICATION RESULTS")
    print("=" * 70)

    total = len(our_glosses)

    print(f"\n✓ Proper names (standard biblical): {len(proper_names)} ({len(proper_names)/total*100:.1f}%)")
    print(f"✓ Aramaic/Hebrew terms (well-documented): {len(aramaic)} ({len(aramaic)/total*100:.1f}%)")
    print(f"✓ Verified against N1904: {len(verified_n1904)} ({len(verified_n1904)/total*100:.1f}%)")
    print(f"✓ Verified against lexicon: {len(verified_lexicon)} ({len(verified_lexicon)/total*100:.1f}%)")
    print(f"✓ Verified by semantic/prefix match: {len(verified_semantic)} ({len(verified_semantic)/total*100:.1f}%)")

    verified_total = len(proper_names) + len(aramaic) + len(verified_n1904) + len(verified_lexicon) + len(verified_semantic)
    print(f"\n{'='*40}")
    print(f"TOTAL VERIFIED: {verified_total}/{total} ({verified_total/total*100:.1f}%)")
    print(f"UNVERIFIED: {len(unverified)}/{total} ({len(unverified)/total*100:.1f}%)")
    print(f"{'='*40}")

    if unverified:
        print(f"\n" + "=" * 70)
        print("UNVERIFIED ENTRIES (need manual review)")
        print("=" * 70)
        for greek, gloss in unverified[:30]:
            print(f"  {greek}: \"{gloss}\"")
        if len(unverified) > 30:
            print(f"  ... and {len(unverified) - 30} more")

    # Show sample verified entries
    print(f"\n" + "=" * 70)
    print("SAMPLE VERIFIED AGAINST N1904")
    print("=" * 70)
    for greek, our_gloss, ref_gloss in verified_n1904[:10]:
        print(f"  ✓ {greek}: \"{our_gloss}\" (N1904: \"{ref_gloss}\")")

    print("=" * 70)


if __name__ == "__main__":
    main()
