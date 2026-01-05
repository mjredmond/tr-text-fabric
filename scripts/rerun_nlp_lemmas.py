#!/usr/bin/env python3
"""
Re-run NLP lemmatization with improved settings.

Issues with original run:
1. Stanza re-tokenized text, causing word boundary issues
2. No validation against known lemmas
3. No post-processing to fix common errors

This script:
1. Uses pre-tokenized words (already correct from TR source)
2. Validates lemmas against N1904 when possible
3. Post-processes to fix common Stanza errors

Usage:
    python scripts/rerun_nlp_lemmas.py
    python scripts/rerun_nlp_lemmas.py --dry-run
"""

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import stanza
from tqdm import tqdm

from scripts.utils.config import load_config

# Common lemma corrections (Stanza error -> correct lemma)
LEMMA_FIXES = {
    "πατέρχομαι": "πατήρ",
    "λίγνυμι": "λέγω",
    "παταέράσσω": "πατήρ",
    "πέύπω": "πέμπω",
    "κύρίνω": "κρίνω",
    "λίγω": "λέγω",
    "ἅγομαι": "ἄγω",
    "θείνω": "τίθημι",
    "γίγνομαι": "γίνομαι",
    "μεθίημι": "ἀφίημι",
    "κυρίόω": "κύριος",
}


def build_n1904_lemma_lookup(n1904_df):
    """Build word -> lemma lookup from N1904."""
    # For each word form, get the most common lemma
    word_lemmas = (
        n1904_df.groupby("word")["lemma"]
        .agg(lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else x.iloc[0])
        .to_dict()
    )
    return word_lemmas


def lemmatize_word(word_text, nlp, n1904_lookup):
    """
    Get lemma for a single word with validation.

    Priority:
    1. N1904 lookup (if word appears there)
    2. Stanza lemmatization
    3. Post-processing fixes
    """
    # Try N1904 lookup first
    if word_text in n1904_lookup:
        return n1904_lookup[word_text], "n1904"

    # Use Stanza
    try:
        doc = nlp(word_text)
        if doc.sentences and doc.sentences[0].words:
            lemma = doc.sentences[0].words[0].lemma

            # Apply fixes
            if lemma in LEMMA_FIXES:
                return LEMMA_FIXES[lemma], "fixed"

            return lemma, "stanza"
    except Exception:
        pass

    # Fallback to word itself
    return word_text, "fallback"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("=" * 60)
    print("RE-RUN NLP LEMMATIZATION")
    print("=" * 60)

    config = load_config()
    intermediate_dir = Path(config["paths"]["data"]["intermediate"])

    # Load data
    print("\nLoading data...")
    tr_df = pd.read_parquet(intermediate_dir / "tr_complete.parquet")
    n1904_df = pd.read_parquet(intermediate_dir / "n1904_words.parquet")

    # Get NLP-sourced words only
    nlp_words = tr_df[tr_df["source"] == "nlp"].copy()
    print(f"  NLP-sourced words: {len(nlp_words):,}")

    # Build N1904 lookup
    print("Building N1904 lemma lookup...")
    n1904_lookup = build_n1904_lemma_lookup(n1904_df)
    print(f"  N1904 word->lemma entries: {len(n1904_lookup):,}")

    if args.dry_run:
        # Sample check
        print("\n[DRY RUN] Sample words to re-lemmatize:")
        sample = nlp_words[nlp_words["gloss"].isna()].head(10)
        for _, row in sample.iterrows():
            word = row["word"]
            old_lemma = row["lemma"]
            n1904_lemma = n1904_lookup.get(word, None)
            print(f"  {word}: {old_lemma} -> {n1904_lemma or '(stanza)'}")
        return

    # Initialize Stanza
    print("\nInitializing Stanza...")
    nlp = stanza.Pipeline(
        "grc",
        processors="tokenize,pos,lemma",
        tokenize_pretokenized=True,  # Important: don't re-tokenize
        verbose=False,
    )

    # Re-lemmatize
    print("\nRe-lemmatizing NLP-sourced words...")
    new_lemmas = []
    sources = []

    unique_words = nlp_words["word"].unique()
    word_lemma_cache = {}

    for word in tqdm(unique_words, desc="Lemmatizing"):
        lemma, source = lemmatize_word(word, nlp, n1904_lookup)
        word_lemma_cache[word] = (lemma, source)

    # Apply to all rows
    print("Applying new lemmas...")
    n1904_count = 0
    stanza_count = 0
    fixed_count = 0
    fallback_count = 0

    for idx in nlp_words.index:
        word = tr_df.at[idx, "word"]
        lemma, source = word_lemma_cache.get(word, (word, "fallback"))
        tr_df.at[idx, "lemma"] = lemma

        if source == "n1904":
            n1904_count += 1
        elif source == "stanza":
            stanza_count += 1
        elif source == "fixed":
            fixed_count += 1
        else:
            fallback_count += 1

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Total re-lemmatized: {len(nlp_words):,}")
    print(f"  From N1904 lookup: {n1904_count:,}")
    print(f"  From Stanza: {stanza_count:,}")
    print(f"  Fixed (post-process): {fixed_count:,}")
    print(f"  Fallback (word=lemma): {fallback_count:,}")

    # Save
    tr_df.to_parquet(intermediate_dir / "tr_complete.parquet")
    print(f"\n  Saved updated dataset")

    # Now re-run gloss filling
    print("\n" + "=" * 60)
    print("RE-FILLING GLOSSES WITH NEW LEMMAS")
    print("=" * 60)

    # Import and run gloss filling
    from scripts.fill_missing_glosses import load_data, build_n1904_gloss_map, fill_from_n1904

    tr_df, n1904_df, _ = load_data()
    n1904_gloss_map = build_n1904_gloss_map(n1904_df)
    tr_df, filled, still_missing = fill_from_n1904(tr_df, n1904_gloss_map)

    # Save again
    tr_df.to_parquet(intermediate_dir / "tr_complete.parquet")

    # Final stats
    final_missing = (tr_df["gloss"].isna() | (tr_df["gloss"] == "")).sum()
    coverage = (len(tr_df) - final_missing) / len(tr_df) * 100

    print(f"\n  Final gloss coverage: {coverage:.1f}%")
    print(f"  Words with gloss: {len(tr_df) - final_missing:,}")
    print(f"  Words without gloss: {final_missing:,}")

    print("=" * 60)


if __name__ == "__main__":
    main()
