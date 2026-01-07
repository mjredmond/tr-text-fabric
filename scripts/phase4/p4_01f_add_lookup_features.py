#!/usr/bin/env python3
"""
Script: p4_01f_add_lookup_features.py
Phase: 4 - Compilation
Purpose: Add N1904 lookup-based features: trans, domain, typems

Input:  data/intermediate/tr_complete.parquet
Output: data/intermediate/tr_complete.parquet (updated in place)

Features added:
- trans: Contextual English translation (from N1904)
- domain: Semantic domain codes (from N1904)
- typems: Morphological subtype (common/proper/etc.)

Strategy:
- For aligned words (~89%): Get directly from N1904 via n1904_node_id
- For TR-only words (~11%): Lookup by (lemma, strong) or lemma alone

Usage:
    python -m scripts.phase4.p4_01f_add_lookup_features
    python -m scripts.phase4.p4_01f_add_lookup_features --dry-run
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils.config import load_config
from scripts.utils.logging import ScriptLogger, get_logger


def load_n1904_data(n1904_tf_path: str):
    """
    Load N1904 TF data and build lookup structures.

    Returns:
        - node_data: dict mapping node_id -> {trans, domain, typems}
        - lemma_lookup: dict mapping (lemma, strong) -> {trans, domain, typems}
    """
    from tf.fabric import Fabric

    logger = get_logger(__name__)
    logger.info(f"Loading N1904 TF data from: {n1904_tf_path}")

    TF = Fabric(locations=n1904_tf_path, silent='deep')
    api = TF.load('trans domain typems lemma strong', silent='deep')

    node_data = {}
    lemma_lookup = {}

    for w in api.F.otype.s('word'):
        trans = api.F.trans.v(w)
        domain = api.F.domain.v(w)
        typems = api.F.typems.v(w)
        lemma = api.F.lemma.v(w)
        strong = api.F.strong.v(w)

        # Store by node ID
        node_data[w] = {
            'trans': trans,
            'domain': domain,
            'typems': typems,
        }

        # Build lemma lookup for TR-only words
        # Use (lemma, strong) as primary key, lemma alone as fallback
        if lemma:
            if strong:
                key = (lemma, strong)
                if key not in lemma_lookup:
                    lemma_lookup[key] = {
                        'trans': trans,  # Use first occurrence
                        'domain': domain,
                        'typems': typems,
                    }
            # Also store by lemma alone (will be overwritten, keeps last value)
            if lemma not in lemma_lookup:
                lemma_lookup[lemma] = {
                    'trans': trans,
                    'domain': domain,
                    'typems': typems,
                }

    logger.info(f"Loaded {len(node_data)} N1904 word nodes")
    logger.info(f"Built lemma lookup with {len(lemma_lookup)} entries")

    return node_data, lemma_lookup


def add_lookup_features(df, node_data: dict, lemma_lookup: dict, logger):
    """
    Add trans, domain, typems features to the dataframe.

    Strategy:
    1. For aligned words: use n1904_node_id to get exact values
    2. For TR-only words: lookup by (lemma, strong) or lemma
    """
    import pandas as pd
    import numpy as np

    # Initialize columns
    df['trans'] = None
    df['domain'] = None
    df['typems'] = None

    aligned_count = 0
    lookup_count = 0
    miss_count = 0

    for idx, row in df.iterrows():
        n1904_id = row.get('n1904_node_id')

        if pd.notna(n1904_id):
            # Aligned word - get directly from N1904
            n1904_id = int(n1904_id)
            if n1904_id in node_data:
                data = node_data[n1904_id]
                df.at[idx, 'trans'] = data['trans']
                df.at[idx, 'domain'] = data['domain']
                df.at[idx, 'typems'] = data['typems']
                aligned_count += 1
            else:
                miss_count += 1
        else:
            # TR-only word - try lookup
            lemma = row.get('lemma')
            strong = row.get('strong')

            data = None

            # Try (lemma, strong) first
            if lemma and strong:
                key = (lemma, strong)
                if key in lemma_lookup:
                    data = lemma_lookup[key]

            # Fall back to lemma alone
            if data is None and lemma and lemma in lemma_lookup:
                data = lemma_lookup[lemma]

            if data:
                df.at[idx, 'trans'] = data['trans']
                df.at[idx, 'domain'] = data['domain']
                df.at[idx, 'typems'] = data['typems']
                lookup_count += 1
            else:
                miss_count += 1

    logger.info(f"Features added:")
    logger.info(f"  From N1904 alignment: {aligned_count}")
    logger.info(f"  From lemma lookup: {lookup_count}")
    logger.info(f"  No data found: {miss_count}")

    return df


def main(config: dict = None, dry_run: bool = False) -> bool:
    """Main entry point."""
    if config is None:
        config = load_config()

    logger = get_logger(__name__)

    complete_path = Path(config["paths"]["data"]["intermediate"]) / "tr_complete.parquet"
    n1904_tf_path = "/home/michael/text-fabric-data/github/CenterBLC/N1904/tf/1.0.0"

    if dry_run:
        logger.info("[DRY RUN] Would add lookup features: trans, domain, typems")
        return True

    import pandas as pd

    # Check input
    if not complete_path.exists():
        logger.error(f"Input not found: {complete_path}")
        return False

    # Load N1904 data
    node_data, lemma_lookup = load_n1904_data(n1904_tf_path)

    # Load TR data
    logger.info(f"Loading TR data from: {complete_path}")
    df = pd.read_parquet(complete_path)
    logger.info(f"Loaded {len(df)} words")

    # Check if features already exist
    new_features = ['trans', 'domain', 'typems']
    existing = [f for f in new_features if f in df.columns]
    if existing:
        logger.info(f"Features already exist (will be overwritten): {existing}")

    # Add features
    logger.info("Adding lookup features...")
    df = add_lookup_features(df, node_data, lemma_lookup, logger)

    # Save
    logger.info(f"Saving to: {complete_path}")
    df.to_parquet(complete_path, index=False)

    # Report coverage
    logger.info("\nFeature coverage:")
    for feat in new_features:
        non_null = df[feat].notna().sum()
        logger.info(f"  {feat}: {non_null}/{len(df)} ({non_null/len(df)*100:.1f}%)")

    # Show samples
    logger.info("\nSample values (first 5 with trans):")
    sample = df[df['trans'].notna()].head(5)
    for _, row in sample.iterrows():
        logger.info(f"  {row['word']}: trans='{row['trans']}', domain={row['domain']}, typems={row['typems']}")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    with ScriptLogger("p4_01f_add_lookup_features") as logger:
        config = load_config()
        success = main(config, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
