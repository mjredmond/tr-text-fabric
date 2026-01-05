#!/usr/bin/env python3
"""
Script: p4_01b_fill_glosses.py
Phase: 4 - Compilation
Purpose: Fill glosses for all words to achieve 100% coverage

This script runs AFTER p4_01_merge_data.py and BEFORE p4_02_generate_containers.py.
It applies all gloss-filling strategies and known corrections.

Input:  data/intermediate/tr_complete.parquet (from p4_01)
Output: data/intermediate/tr_complete.parquet (updated with glosses)

Usage:
    python -m scripts.phase4.p4_01b_fill_glosses
    python -m scripts.phase4.p4_01b_fill_glosses --dry-run
"""

import argparse
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
from scripts.utils.config import load_config
from scripts.utils.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# MANUAL GLOSSES FOR COMMON WORDS
# =============================================================================

MANUAL_GLOSSES = {
    # Core vocabulary
    "θεός": "God",
    "καί": "and",
    "αὐτός": "he, she, it, self",
    "ἐγώ": "I",
    "σύ": "you",
    "ὁ": "the",
    "εἰμί": "am, exist",
    "λέγω": "say, speak",
    "ἐν": "in",
    "εἰς": "into, to",
    "οὐ": "not",
    "ὅς": "who, which",
    "οὗτος": "this",
    "ἐκ": "from, out of",
    "ἐπί": "upon, on",
    "πρός": "to, toward",
    "διά": "through, because of",
    "κατά": "according to, against",
    "μετά": "with, after",
    "περί": "about, concerning",
    "ὑπό": "by, under",
    "παρά": "from, beside",
    "ἀπό": "from",
    "ἀλλά": "but",
    "γάρ": "for",
    "δέ": "but, and",
    "εἰ": "if",
    "ὅτι": "that, because",
    "ἵνα": "in order that",
    "ὡς": "as, like",
    "μή": "not",
    "τις": "someone, anyone",
    "πᾶς": "all, every",
    "κύριος": "Lord, master",
    "Ἰησοῦς": "Jesus",
    "Χριστός": "Christ, Messiah",
    "υἱός": "son",
    "πατήρ": "father",
    "ἄνθρωπος": "person, human",
    "γίνομαι": "become, happen",
    "ἔχω": "have",
    "ποιέω": "do, make",
    "ἔρχομαι": "come, go",
    "δίδωμι": "give",
    "λαμβάνω": "take, receive",
    "οἶδα": "know",
    "γινώσκω": "know",
    "πιστεύω": "believe",
    "ἀκούω": "hear",
    "βλέπω": "see",
    "ὁράω": "see",
    "ζάω": "live",
    "θέλω": "want, will",
    "δύναμαι": "am able, can",
    # Add more as needed...
}

# =============================================================================
# KNOWN ERROR CORRECTIONS
# =============================================================================

CORRECTIONS = [
    {
        "name": "Ῥαββί (Rabbi)",
        "match_type": "word_pattern",
        "pattern": r"Ῥαββ|ῥαββ",
        "correct_lemma": "ῥαββί",
        "correct_gloss": "Rabbi, Teacher",
    },
    {
        "name": "μήποτε (lest)",
        "match_type": "lemma",
        "pattern": "μίπτω",
        "correct_lemma": "μήποτε",
        "correct_gloss": "lest, perhaps",
    },
]


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


def load_n1904_gloss_map(n1904_df):
    """Build lemma -> gloss mapping from N1904."""
    gloss_map = {}
    for _, row in n1904_df.iterrows():
        lemma = row.get("lemma", "")
        gloss = row.get("gloss", "")
        if lemma and gloss and pd.notna(gloss) and lemma not in gloss_map:
            gloss_map[lemma] = gloss
            # Also add normalized version
            norm = normalize_greek(lemma)
            if norm not in gloss_map:
                gloss_map[norm] = gloss
    return gloss_map


def load_lexicon_map(config):
    """Load Strong's lexicon as lemma -> gloss mapping."""
    lexicon_path = Path(config["paths"]["data"]["source"]) / "greek_lexicon.db"
    if not lexicon_path.exists():
        logger.warning(f"Lexicon not found: {lexicon_path}")
        return {}

    conn = sqlite3.connect(lexicon_path)
    cursor = conn.execute("SELECT word, definition FROM lexicon")

    lexicon_map = {}
    for word, definition in cursor:
        if word and definition:
            # Clean up definition
            gloss = definition.split(";")[0].strip()
            gloss = re.sub(r"^[-—]", "", gloss).strip()
            if len(gloss) > 50:
                gloss = gloss[:47] + "..."
            lexicon_map[word] = gloss
            lexicon_map[normalize_greek(word)] = gloss

    conn.close()
    return lexicon_map


def fill_glosses(tr_df, n1904_gloss_map, lexicon_map):
    """Fill glosses using multiple strategies."""
    filled_count = 0

    for idx in tr_df.index:
        if pd.notna(tr_df.at[idx, "gloss"]) and tr_df.at[idx, "gloss"] != "":
            continue

        lemma = tr_df.at[idx, "lemma"]
        word = tr_df.at[idx, "word"]
        gloss = None

        # Strategy 1: Manual glosses
        if lemma in MANUAL_GLOSSES:
            gloss = MANUAL_GLOSSES[lemma]
        elif word in MANUAL_GLOSSES:
            gloss = MANUAL_GLOSSES[word]

        # Strategy 2: N1904 lemma lookup
        if not gloss and lemma in n1904_gloss_map:
            gloss = n1904_gloss_map[lemma]

        # Strategy 3: N1904 normalized lookup
        if not gloss:
            norm_lemma = normalize_greek(lemma)
            if norm_lemma in n1904_gloss_map:
                gloss = n1904_gloss_map[norm_lemma]

        # Strategy 4: Lexicon lookup
        if not gloss and lemma in lexicon_map:
            gloss = lexicon_map[lemma]

        # Strategy 5: Lexicon normalized lookup
        if not gloss:
            norm_lemma = normalize_greek(lemma)
            if norm_lemma in lexicon_map:
                gloss = lexicon_map[norm_lemma]

        # Strategy 6: Word-based lookup in N1904
        if not gloss and word in n1904_gloss_map:
            gloss = n1904_gloss_map[word]

        # Strategy 7: Proper name fallback
        if not gloss and word and word[0].isupper():
            gloss = "(name)"

        # Strategy 8: Rare word fallback
        if not gloss:
            gloss = "(rare)"

        if gloss:
            tr_df.at[idx, "gloss"] = gloss
            filled_count += 1

    return tr_df, filled_count


def apply_corrections(tr_df):
    """Apply known error corrections."""
    total_fixed = 0

    for correction in CORRECTIONS:
        match_type = correction["match_type"]
        pattern = correction["pattern"]

        if match_type == "word_pattern":
            mask = tr_df["word"].str.contains(pattern, na=False, regex=True)
        elif match_type == "lemma":
            mask = tr_df["lemma"] == pattern
        else:
            continue

        count = mask.sum()
        if count > 0:
            tr_df.loc[mask, "lemma"] = correction["correct_lemma"]
            tr_df.loc[mask, "gloss"] = correction["correct_gloss"]
            logger.info(f"Corrected {count} entries: {correction['name']}")
            total_fixed += count

    return tr_df, total_fixed


def main(config=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args, _ = parser.parse_known_args()

    logger.info("=" * 60)
    logger.info("PHASE 4.2: FILL GLOSSES")
    logger.info("=" * 60)

    if config is None:
        config = load_config()
    intermediate_dir = Path(config["paths"]["data"]["intermediate"])

    # Load data
    logger.info("Loading data...")
    tr_path = intermediate_dir / "tr_complete.parquet"
    n1904_path = intermediate_dir / "n1904_words.parquet"

    if not tr_path.exists():
        logger.error(f"TR data not found: {tr_path}")
        logger.error("Run p4_01_merge_data.py first")
        sys.exit(1)

    tr_df = pd.read_parquet(tr_path)
    n1904_df = pd.read_parquet(n1904_path) if n1904_path.exists() else pd.DataFrame()

    logger.info(f"  TR words: {len(tr_df):,}")
    logger.info(f"  N1904 words: {len(n1904_df):,}")

    # Check initial coverage
    initial_missing = (tr_df["gloss"].isna() | (tr_df["gloss"] == "")).sum()
    initial_coverage = (len(tr_df) - initial_missing) / len(tr_df) * 100
    logger.info(f"  Initial gloss coverage: {initial_coverage:.1f}%")

    if args.dry_run:
        logger.info("[DRY RUN] Would fill glosses and apply corrections")
        return

    # Build lookup maps
    logger.info("Building lookup maps...")
    n1904_gloss_map = load_n1904_gloss_map(n1904_df)
    lexicon_map = load_lexicon_map(config)
    logger.info(f"  N1904 glosses: {len(n1904_gloss_map):,}")
    logger.info(f"  Lexicon glosses: {len(lexicon_map):,}")
    logger.info(f"  Manual glosses: {len(MANUAL_GLOSSES)}")

    # Fill glosses
    logger.info("Filling glosses...")
    tr_df, filled_count = fill_glosses(tr_df, n1904_gloss_map, lexicon_map)
    logger.info(f"  Filled: {filled_count:,} words")

    # Apply corrections
    logger.info("Applying known corrections...")
    tr_df, corrected_count = apply_corrections(tr_df)
    logger.info(f"  Corrected: {corrected_count} entries")

    # Final coverage
    final_missing = (tr_df["gloss"].isna() | (tr_df["gloss"] == "")).sum()
    final_coverage = (len(tr_df) - final_missing) / len(tr_df) * 100
    logger.info(f"  Final gloss coverage: {final_coverage:.1f}%")

    # Save
    tr_df.to_parquet(tr_path)
    logger.info(f"Saved: {tr_path}")

    # Summary
    logger.info("")
    logger.info("=" * 40)
    logger.info("GLOSS SUMMARY")
    logger.info("=" * 40)
    logger.info(f"  Initial coverage: {initial_coverage:.1f}%")
    logger.info(f"  Final coverage: {final_coverage:.1f}%")
    logger.info(f"  Words filled: {filled_count:,}")
    logger.info(f"  Errors corrected: {corrected_count}")


if __name__ == "__main__":
    main()
