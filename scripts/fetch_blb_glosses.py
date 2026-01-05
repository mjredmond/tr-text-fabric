#!/usr/bin/env python3
"""
Fetch missing glosses from local Strong's lexicon database.

This script fills English definitions for Greek lemmas that don't have
glosses from the N1904 transplant. It uses the local greek_lexicon.db
which contains Strong's definitions and Thayer's lexicon data.

Usage:
    python scripts/fetch_blb_glosses.py              # Fill all missing
    python scripts/fetch_blb_glosses.py --dry-run    # Show what would be done
"""

import argparse
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from scripts.utils.config import load_config

# Manual glosses for common words where automatic extraction fails
MANUAL_GLOSSES = {
    "θεός": "God",
    "θεοῦ": "God",
    "καί": "and",
    "αὐτός": "he, she, it, self",
    "ἀλλά": "but",
    "ἀλλ᾽": "but",
    "ἐγώ": "I",
    "δέ": "but, and",
    "σύ": "you",
    "εἰμί": "I am, to be",
    "ἀπό": "from",
    "κατά": "according to, against",
    "διά": "through, because of",
    "δι᾽": "through",
    "ἐπί": "upon, on",
    "ἐπ᾽": "upon",
    "ἐν": "in",
    "εἰς": "into, to",
    "ἐκ": "out of, from",
    "ἐξ": "out of",
    "μετά": "with, after",
    "μετ᾽": "with",
    "πρός": "to, toward",
    "ὑπό": "by, under",
    "ὑπ᾽": "by",
    "περί": "about, concerning",
    "παρά": "from, beside",
    "ὅς": "who, which",
    "ὅτι": "that, because",
    "οὗτος": "this",
    "ἐκεῖνος": "that",
    "τίς": "who? what?",
    "τις": "someone, anyone",
    "πᾶς": "all, every",
    "εἷς": "one",
    "οὐ": "not",
    "οὐκ": "not",
    "οὐχ": "not",
    "μή": "not",
    "γάρ": "for",
    "οὖν": "therefore",
    "ἤ": "or",
    "εἰ": "if",
    "ἐάν": "if",
    "ὡς": "as, like",
    "ἵνα": "in order that",
    "κύριος": "Lord, master",
    "Ἰησοῦς": "Jesus",
    "Χριστός": "Christ, Anointed",
    "πνεῦμα": "spirit",
    "λόγος": "word",
    "ἄνθρωπος": "man, person",
    "γυνή": "woman, wife",
    "υἱός": "son",
    "πατήρ": "father",
    "ἀδελφός": "brother",
    "κόσμος": "world",
    "οὐρανός": "heaven",
    "γῆ": "earth",
    "ἡμέρα": "day",
    "ζωή": "life",
    "θάνατος": "death",
    "ἀγάπη": "love",
    "πίστις": "faith",
    "ἔργον": "work",
    "λέγω": "I say",
    "ποιέω": "I do, make",
    "ἔρχομαι": "I come, go",
    "γίνομαι": "I become",
    "ἔχω": "I have",
    "ὁράω": "I see",
    "εἶδον": "I saw",
    "ἀκούω": "I hear",
    "γινώσκω": "I know",
    "οἶδα": "I know",
    "πιστεύω": "I believe",
    "δίδωμι": "I give",
    "λαμβάνω": "I take, receive",
    "δύναμαι": "I am able",
    "θέλω": "I wish, want",
    "μέγας": "great",
    "ἀγαθός": "good",
    "κακός": "bad, evil",
    "νέος": "new, young",
    "ἅγιος": "holy",
    "ἀληθής": "true",
    "ἐάω": "I permit",
    "κυρίόω": "Lord (variant)",
    "Ἰησός": "Jesus",
    "Ἰησοῦ": "Jesus",
    "θείνω": "I strike",
    "γίγνομαι": "I become",
    "κύριον": "Lord",
    "ἀφίημι": "I send away, forgive",
    "Μωσή": "Moses",
    "Μωσῆς": "Moses",
    "Μωϋσῆς": "Moses",
    "μεθίημι": "I release",
    "πίπτω": "I fall",
    "ἄρα": "therefore",
    "τέ": "and",
    "ἴδιος": "one's own",
    "νῦν": "now",
    "ἕως": "until",
    "οὕτω": "thus, so",
    "οὕτως": "thus, so",
    "πόλις": "city",
    "ὄνομα": "name",
    "χείρ": "hand",
    "λαός": "people",
    "ὥρα": "hour",
    "ἔτος": "year",
    "δόξα": "glory",
    "βασιλεία": "kingdom",
    "ἐκκλησία": "church, assembly",
    "ψυχή": "soul",
    "σῶμα": "body",
    "αἷμα": "blood",
    "ὕδωρ": "water",
    "οἶκος": "house",
    "ὁδός": "way, road",
    "ὄχλος": "crowd",
    "ἔθνος": "nation",
    "νόμος": "law",
    "γραφή": "scripture",
    "προφήτης": "prophet",
    "ἀπόστολος": "apostle",
    "μαθητής": "disciple",
    "δοῦλος": "servant, slave",
    "ἁμαρτία": "sin",
    "χάρις": "grace",
    "εἰρήνη": "peace",
    "ἀλήθεια": "truth",
    "δικαιοσύνη": "righteousness",
    "δύναμις": "power",
    "σοφία": "wisdom",
    "Παῦλος": "Paul",
    "Πέτρος": "Peter",
    "Ἰωάννης": "John",
    "Ἀβραάμ": "Abraham",
    "Δαβίδ": "David",
    "Ἰσραήλ": "Israel",
    "Ἰερουσαλήμ": "Jerusalem",
}


def normalize_greek(text):
    """Normalize Greek text for matching (remove accents, breathings, etc.)."""
    if not text:
        return ""
    # First normalize to NFC to combine any decomposed characters
    text = unicodedata.normalize("NFC", text)
    # Then NFD to decompose
    text = unicodedata.normalize("NFD", text)
    # Remove all combining marks (accents, breathings, etc.)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = text.lower()
    # Remove common punctuation and apostrophes
    text = re.sub(r"[᾽᾿'ʼ᾿]", "", text)
    return text


def load_lexicon(config):
    """Load the Greek lexicon database."""
    db_path = Path(config["paths"]["data"]["source"]) / "greek_lexicon.db"

    if not db_path.exists():
        raise FileNotFoundError(f"Lexicon database not found: {db_path}")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Load all entries into a dictionary
    cur.execute("""
        SELECT strongs_number, word, transliteration, definition, thayer_definition, kjv_usage
        FROM lexicon
    """)

    lexicon = {}
    word_to_strongs = {}

    for row in cur.fetchall():
        strongs, word, translit, definition, thayer, kjv = row

        # Store by Strong's number
        lexicon[strongs] = {
            "word": word,
            "transliteration": translit,
            "definition": definition,
            "thayer": thayer,
            "kjv_usage": kjv,
        }

        # Also map normalized word to Strong's number(s)
        if word:
            norm_word = normalize_greek(word)
            if norm_word not in word_to_strongs:
                word_to_strongs[norm_word] = []
            word_to_strongs[norm_word].append(strongs)

    conn.close()
    return lexicon, word_to_strongs


def extract_short_gloss(entry):
    """Extract a short gloss from lexicon entry."""
    # Try definition - look for English gloss after :—
    if entry.get("definition"):
        definition = entry["definition"]

        # Extract meaning after :— which has the English glosses
        if ":—" in definition:
            gloss_part = definition.split(":—")[1].strip()
            # Remove trailing period
            gloss_part = gloss_part.rstrip(".")
            # Take first gloss
            parts = re.split(r"[,;]", gloss_part)
            if parts:
                gloss = parts[0].strip()
                if gloss and 2 < len(gloss) < 50:
                    return gloss

        # Look for quoted words like "son" or (word)
        quoted = re.search(r'[&]quot;([^&]+)[&]quot;', definition)
        if quoted:
            return quoted.group(1)

        # Look for pattern: i.e. MEANING
        ie_match = re.search(r'i\.e\.\s+([^:;,]+)', definition)
        if ie_match:
            gloss = ie_match.group(1).strip()
            if gloss and 2 < len(gloss) < 50:
                return gloss

    # Try KJV usage
    if entry.get("kjv_usage") and entry["kjv_usage"].strip():
        usage = entry["kjv_usage"]
        # Clean up and take first few words
        usage = re.sub(r"^\s*[A-Z]+\s*\(\d+x?\):\s*", "", usage)
        parts = re.split(r"[,;]", usage)
        if parts:
            gloss = parts[0].strip()
            if gloss and 2 < len(gloss) < 50:
                return gloss

    # Fallback: try to extract from definition without :—
    if entry.get("definition"):
        definition = entry["definition"]
        # Skip transliteration at start (ends with ;)
        if ";" in definition:
            definition = definition.split(";", 1)[1].strip()

        # Look for word in parens or key phrase
        paren = re.search(r'\(([a-zA-Z][^)]+)\)', definition)
        if paren:
            gloss = paren.group(1)
            if 2 < len(gloss) < 40:
                return gloss

    return None


def find_gloss_for_lemma(lemma, lexicon, word_to_strongs):
    """Find a gloss for a Greek lemma."""
    if not lemma:
        return None

    # Check manual glosses first (exact match)
    if lemma in MANUAL_GLOSSES:
        return MANUAL_GLOSSES[lemma]

    # Check manual glosses with normalized lookup
    norm_lemma = normalize_greek(lemma)
    for manual_word, gloss in MANUAL_GLOSSES.items():
        if normalize_greek(manual_word) == norm_lemma:
            return gloss

    # Direct lookup
    if norm_lemma in word_to_strongs:
        for strongs in word_to_strongs[norm_lemma]:
            entry = lexicon.get(strongs)
            if entry:
                gloss = extract_short_gloss(entry)
                if gloss:
                    return gloss

    # Try without final sigma variation
    alt_lemma = norm_lemma.replace("ς", "σ")
    if alt_lemma != norm_lemma and alt_lemma in word_to_strongs:
        for strongs in word_to_strongs[alt_lemma]:
            entry = lexicon.get(strongs)
            if entry:
                gloss = extract_short_gloss(entry)
                if gloss:
                    return gloss

    # Try fuzzy match - check if any lexicon word starts with our lemma
    for lex_word, strongs_list in word_to_strongs.items():
        if lex_word.startswith(norm_lemma) or norm_lemma.startswith(lex_word):
            for strongs in strongs_list:
                entry = lexicon.get(strongs)
                if entry:
                    gloss = extract_short_gloss(entry)
                    if gloss:
                        return gloss

    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    args = parser.parse_args()

    print("=" * 60)
    print("FILL MISSING GLOSSES FROM STRONG'S LEXICON")
    print("=" * 60)

    # Load config and data
    config = load_config()
    intermediate_dir = Path(config["paths"]["data"]["intermediate"])

    print("\nLoading data...")
    tr_df = pd.read_parquet(intermediate_dir / "tr_complete.parquet")

    # Load lexicon
    print("Loading lexicon database...")
    lexicon, word_to_strongs = load_lexicon(config)
    print(f"  Lexicon entries: {len(lexicon)}")
    print(f"  Word mappings: {len(word_to_strongs)}")

    # Find words without gloss
    no_gloss_mask = tr_df["gloss"].isna() | (tr_df["gloss"] == "")
    no_gloss = tr_df[no_gloss_mask]

    print(f"\n  Words without gloss: {len(no_gloss):,}")

    # Get unique lemmas
    missing_lemmas = no_gloss["lemma"].value_counts()
    print(f"  Unique lemmas to look up: {len(missing_lemmas)}")

    if args.dry_run:
        print("\n[DRY RUN] Would look up glosses for:")
        found = 0
        for lemma, count in missing_lemmas.head(20).items():
            gloss = find_gloss_for_lemma(lemma, lexicon, word_to_strongs)
            status = f"-> {gloss}" if gloss else "(not found)"
            if gloss:
                found += 1
            print(f"    {lemma}: {count} words {status}")

        # Count total findable
        total_found = sum(1 for l in missing_lemmas.index
                         if find_gloss_for_lemma(l, lexicon, word_to_strongs))
        total_words = sum(missing_lemmas[l] for l in missing_lemmas.index
                         if find_gloss_for_lemma(l, lexicon, word_to_strongs))
        print(f"\n  Lemmas with glosses available: {total_found}/{len(missing_lemmas)}")
        print(f"  Words that would be filled: {total_words:,}")
        return

    # Build lemma -> gloss map
    print("\nLooking up glosses...")
    lemma_gloss_map = {}
    found = 0
    not_found = 0

    for i, lemma in enumerate(missing_lemmas.index):
        if pd.isna(lemma):
            continue

        gloss = find_gloss_for_lemma(lemma, lexicon, word_to_strongs)
        if gloss:
            lemma_gloss_map[lemma] = gloss
            found += 1
        else:
            not_found += 1

        if (i + 1) % 500 == 0:
            print(f"  Progress: {i+1}/{len(missing_lemmas)} (found: {found})")

    print(f"\n  Lemmas found: {found}")
    print(f"  Lemmas not found: {not_found}")

    # Apply glosses
    print("\nApplying glosses to dataset...")
    filled = 0
    for idx in no_gloss.index:
        lemma = tr_df.at[idx, "lemma"]
        if lemma in lemma_gloss_map:
            tr_df.at[idx, "gloss"] = lemma_gloss_map[lemma]
            filled += 1

    # Summary
    final_missing = (tr_df["gloss"].isna() | (tr_df["gloss"] == "")).sum()
    total_words = len(tr_df)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Words filled: {filled:,}")
    print(f"  Still missing: {final_missing:,}")
    print(f"  Total coverage: {(total_words - final_missing) / total_words * 100:.1f}%")

    # Save updated data
    if filled > 0:
        tr_df.to_parquet(intermediate_dir / "tr_complete.parquet")
        print(f"\n  Saved updated dataset")

    # Show samples of what was filled
    if lemma_gloss_map:
        print("\n  Sample glosses added:")
        for lemma, gloss in list(lemma_gloss_map.items())[:10]:
            print(f"    {lemma} -> {gloss}")

    # Show what's still missing
    still_missing = tr_df[tr_df["gloss"].isna() | (tr_df["gloss"] == "")]
    if len(still_missing) > 0:
        print(f"\n  Top lemmas still without gloss:")
        for lemma, count in still_missing["lemma"].value_counts().head(10).items():
            print(f"    {lemma}: {count}")

    print("=" * 60)


if __name__ == "__main__":
    main()
