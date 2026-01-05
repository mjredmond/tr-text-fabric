#!/usr/bin/env python3
"""
Script: p1_05_build_tr_dataframe.py
Phase: 1 - Reconnaissance
Purpose: Load TR source into standardized DataFrame with unique word IDs

Input:  data/source/tr_raw.csv
Output: data/intermediate/tr_words.parquet

Usage:
    python -m scripts.phase1.p1_05_build_tr_dataframe
    python -m scripts.phase1.p1_05_build_tr_dataframe --dry-run
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils.config import load_config
from scripts.utils.logging import ScriptLogger, get_logger


def parse_robinson_morphology(morph_code: str) -> dict:
    """
    Parse Robinson morphology code into components.

    Example: V-PAI-3S -> verb, present, active, indicative, 3rd, singular

    Args:
        morph_code: Robinson-style morphology code

    Returns:
        Dict with parsed components
    """
    result = {
        "sp": None,      # Part of speech
        "tense": None,
        "voice": None,
        "mood": None,
        "case": None,
        "number": None,
        "gender": None,
        "person": None,
    }

    if not morph_code or morph_code == "-":
        return result

    parts = morph_code.split("-")

    # First character is usually POS
    if parts:
        pos_map = {
            "N": "noun",
            "V": "verb",
            "A": "adjective",
            "D": "adverb",
            "P": "preposition",
            "C": "conjunction",
            "T": "article",
            "R": "pronoun",
            "I": "interjection",
            "X": "particle",
        }
        result["sp"] = pos_map.get(parts[0][:1], parts[0])

    # Parse verb morphology (e.g., PAI-3S)
    if len(parts) >= 2 and result["sp"] == "verb":
        verb_part = parts[1] if len(parts) > 1 else ""

        tense_map = {"P": "present", "I": "imperfect", "F": "future", "A": "aorist", "X": "perfect", "Y": "pluperfect"}
        voice_map = {"A": "active", "M": "middle", "P": "passive"}
        mood_map = {"I": "indicative", "S": "subjunctive", "O": "optative", "M": "imperative", "N": "infinitive", "P": "participle"}

        if len(verb_part) >= 1:
            result["tense"] = tense_map.get(verb_part[0])
        if len(verb_part) >= 2:
            result["voice"] = voice_map.get(verb_part[1])
        if len(verb_part) >= 3:
            result["mood"] = mood_map.get(verb_part[2])

        # Person and number (e.g., 3S)
        if len(parts) >= 3:
            pn = parts[2]
            if len(pn) >= 1 and pn[0].isdigit():
                result["person"] = int(pn[0])
            if len(pn) >= 2:
                result["number"] = {"S": "singular", "P": "plural", "D": "dual"}.get(pn[1])

    # Parse noun/adjective morphology
    if result["sp"] in ["noun", "adjective", "article", "pronoun"]:
        if len(parts) >= 2:
            case_num_gen = parts[1]
            case_map = {"N": "nominative", "G": "genitive", "D": "dative", "A": "accusative", "V": "vocative"}
            if len(case_num_gen) >= 1:
                result["case"] = case_map.get(case_num_gen[0])
            if len(case_num_gen) >= 2:
                result["number"] = {"S": "singular", "P": "plural"}.get(case_num_gen[1])
            if len(case_num_gen) >= 3:
                result["gender"] = {"M": "masculine", "F": "feminine", "N": "neuter"}.get(case_num_gen[2])

    return result


def tokenize_greek(text: str) -> list:
    """
    Tokenize Greek text into words.

    Args:
        text: Greek text string

    Returns:
        List of word tokens
    """
    import re
    # Remove punctuation but keep Greek letters and diacritics
    # Split on whitespace and punctuation
    words = re.findall(r'[\u0370-\u03FF\u1F00-\u1FFF]+', text)
    return words


def load_and_process_tr(input_path: Path, config: dict) -> "pd.DataFrame":
    """
    Load TR CSV and create standardized DataFrame.

    Args:
        input_path: Path to TR CSV file
        config: Pipeline config

    Returns:
        Processed DataFrame with one row per word
    """
    import pandas as pd

    logger = get_logger(__name__)

    logger.info(f"Loading: {input_path}")

    # Load CSV
    df = pd.read_csv(input_path)
    logger.info(f"Columns found: {list(df.columns)}")
    logger.info(f"Loaded {len(df):,} rows (verses)")

    # Standardize column names
    col_map = {}
    for col in df.columns:
        col_lower = col.lower()
        if "book" in col_lower:
            col_map[col] = "book"
        elif "chap" in col_lower:
            col_map[col] = "chapter"
        elif "verse" in col_lower:
            col_map[col] = "verse"
        elif "text" in col_lower:
            col_map[col] = "text"

    df = df.rename(columns=col_map)

    # Check if data is verse-level (has 'text' column with full verse)
    if "text" in df.columns:
        logger.info("Data is verse-level, tokenizing into words...")

        # Expand verses into words
        word_records = []
        for _, row in df.iterrows():
            book = row["book"]
            chapter = int(row["chapter"])
            verse = int(row["verse"])
            text = row["text"]

            words = tokenize_greek(text)
            for word_rank, word in enumerate(words, 1):
                word_records.append({
                    "book": book,
                    "chapter": chapter,
                    "verse": verse,
                    "word_rank": word_rank,
                    "word": word,
                })

        df = pd.DataFrame(word_records)
        logger.info(f"Tokenized into {len(df):,} words")

    else:
        # Data is already word-level
        required = ["book", "chapter", "verse", "word"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}. Found: {list(df.columns)}")

        # Add word_rank if not present
        if "word_rank" not in df.columns:
            df["word_rank"] = df.groupby(["book", "chapter", "verse"]).cumcount() + 1

    # Add unique word_id
    df["word_id"] = range(1, len(df) + 1)

    # Ensure types
    df["chapter"] = df["chapter"].astype(int)
    df["verse"] = df["verse"].astype(int)
    df["word_rank"] = df["word_rank"].astype(int)
    df["word_id"] = df["word_id"].astype(int)

    # Select and order columns
    output_cols = ["word_id", "book", "chapter", "verse", "word_rank", "word"]

    # Add optional columns if present
    optional_cols = ["lemma", "morph", "sp", "tense", "voice", "mood", "case", "number", "gender", "person"]
    for col in optional_cols:
        if col in df.columns:
            output_cols.append(col)

    df = df[output_cols]

    return df


def main(config: dict = None, dry_run: bool = False) -> bool:
    """Main entry point."""
    if config is None:
        config = load_config()

    logger = get_logger(__name__)

    input_path = Path(config["paths"]["data"]["source"]) / "tr_raw.csv"
    output_path = Path(config["paths"]["data"]["intermediate"]) / "tr_words.parquet"

    if dry_run:
        logger.info(f"[DRY RUN] Would load: {input_path}")
        logger.info(f"[DRY RUN] Would write: {output_path}")
        return True

    # Check input exists
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Run p1_04_acquire_tr.py first")
        return False

    try:
        import pandas as pd
    except ImportError:
        logger.error("pandas not installed. Run: pip install pandas")
        return False

    # Process
    df = load_and_process_tr(input_path, config)

    # Validate
    assert df["word_id"].is_unique, "word_id must be unique"
    logger.info(f"Total words: {len(df):,}")
    logger.info(f"Books: {df['book'].nunique()}")
    logger.info(f"Columns: {list(df.columns)}")

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved to: {output_path}")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    with ScriptLogger("p1_05_build_tr_dataframe") as logger:
        config = load_config()
        success = main(config, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
