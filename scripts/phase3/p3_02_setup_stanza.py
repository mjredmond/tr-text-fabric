#!/usr/bin/env python3
"""
Script: p3_02_setup_stanza.py
Phase: 3 - Delta Patching
Purpose: Configure Stanza NLP for Ancient Greek dependency parsing

Input:  None (downloads model)
Output: Stanza model installed, test verification

Usage:
    python -m scripts.phase3.p3_02_setup_stanza
    python -m scripts.phase3.p3_02_setup_stanza --dry-run
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils.config import load_config
from scripts.utils.logging import ScriptLogger, get_logger


def download_stanza_model() -> bool:
    """Download Stanza Ancient Greek model."""
    import stanza

    logger = get_logger(__name__)

    logger.info("Downloading Stanza Ancient Greek model...")
    try:
        stanza.download("grc", verbose=True)
        logger.info("Model downloaded successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to download model: {e}")
        return False


def test_stanza_pipeline() -> bool:
    """Test Stanza pipeline on sample Greek text."""
    import stanza

    logger = get_logger(__name__)

    logger.info("Testing Stanza pipeline...")

    try:
        # Create pipeline with required processors
        nlp = stanza.Pipeline(
            "grc",
            processors="tokenize,pos,lemma,depparse",
            verbose=False
        )

        # Test on famous Greek text (John 1:1)
        test_text = "ἐν ἀρχῇ ἦν ὁ λόγος"
        logger.info(f"Test input: {test_text}")

        doc = nlp(test_text)

        logger.info("Parse results:")
        logger.info("-" * 60)
        logger.info(f"{'Word':<15} {'Lemma':<15} {'POS':<8} {'DepRel':<12} {'Head'}")
        logger.info("-" * 60)

        for sent in doc.sentences:
            for word in sent.words:
                head_text = sent.words[word.head - 1].text if word.head > 0 else "ROOT"
                logger.info(
                    f"{word.text:<15} {word.lemma:<15} {word.upos:<8} "
                    f"{word.deprel:<12} {head_text}"
                )

        logger.info("-" * 60)
        logger.info("Stanza pipeline test PASSED")

        # Document available dependency relations
        logger.info("\nStanza UD dependency relations used in Ancient Greek:")
        deprels = set()
        for sent in doc.sentences:
            for word in sent.words:
                deprels.add(word.deprel)
        for deprel in sorted(deprels):
            logger.info(f"  - {deprel}")

        return True

    except Exception as e:
        logger.error(f"Pipeline test failed: {e}")
        return False


def document_stanza_output(config: dict) -> None:
    """Document Stanza's output format for reference."""
    import stanza
    import json

    logger = get_logger(__name__)

    output_path = Path(config["paths"]["data"]["intermediate"]) / "stanza_info.json"

    nlp = stanza.Pipeline("grc", processors="tokenize,pos,lemma,depparse", verbose=False)

    # Get sample parse
    doc = nlp("καὶ ὁ λόγος ἦν πρὸς τὸν θεόν")

    # Extract info
    info = {
        "language": "grc",
        "processors": ["tokenize", "pos", "lemma", "depparse"],
        "sample_parse": [],
        "pos_tags": set(),
        "deprels": set(),
    }

    for sent in doc.sentences:
        for word in sent.words:
            info["sample_parse"].append({
                "id": word.id,
                "text": word.text,
                "lemma": word.lemma,
                "upos": word.upos,
                "xpos": word.xpos,
                "feats": word.feats,
                "head": word.head,
                "deprel": word.deprel,
            })
            info["pos_tags"].add(word.upos)
            info["deprels"].add(word.deprel)

    # Convert sets to lists for JSON
    info["pos_tags"] = sorted(list(info["pos_tags"]))
    info["deprels"] = sorted(list(info["deprels"]))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2, ensure_ascii=False)

    logger.info(f"Stanza info documented: {output_path}")


def main(config: dict = None, dry_run: bool = False) -> bool:
    """Main entry point."""
    if config is None:
        config = load_config()

    logger = get_logger(__name__)

    if dry_run:
        logger.info("[DRY RUN] Would download and configure Stanza for Ancient Greek")
        return True

    try:
        import stanza
    except ImportError:
        logger.error("Stanza not installed. Run: pip install stanza")
        return False

    # Download model
    if not download_stanza_model():
        return False

    # Test pipeline
    if not test_stanza_pipeline():
        return False

    # Document output format
    document_stanza_output(config)

    logger.info("\nStanza setup complete!")
    logger.info("Ready for Phase 3 gap parsing")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    with ScriptLogger("p3_02_setup_stanza") as logger:
        config = load_config()
        success = main(config, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
