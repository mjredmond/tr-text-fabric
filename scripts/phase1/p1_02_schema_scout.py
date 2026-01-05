#!/usr/bin/env python3
"""
Script: p1_02_schema_scout.py
Phase: 1 - Reconnaissance
Purpose: Extract complete schema definition from N1904 Text-Fabric dataset

Input:  N1904 Text-Fabric dataset (loaded via tf.app.use)
Output: data/intermediate/schema_map.json

Usage:
    python -m scripts.phase1.p1_02_schema_scout
    python -m scripts.phase1.p1_02_schema_scout --dry-run
    python -m scripts.phase1.p1_02_schema_scout --verbose
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils.config import load_config, get_path
from scripts.utils.logging import ScriptLogger, get_logger
from scripts.utils.tf_helpers import load_n1904


def get_feature_info(api: Any, feature_name: str) -> Dict[str, Any]:
    """
    Get detailed information about a feature.

    Args:
        api: Text-Fabric API object
        feature_name: Name of the feature

    Returns:
        Dict with feature metadata and sample values
    """
    feature = getattr(api.F, feature_name, None)
    if feature is None:
        return {"error": "Feature not found"}

    info = {
        "name": feature_name,
        "values": [],
        "sample_values": [],
    }

    # Get value frequency list - try different API methods
    try:
        if hasattr(feature, 'freqList'):
            freq_list = list(feature.freqList())[:20]
            info["values"] = [{"value": v, "count": c} for v, c in freq_list]
            info["sample_values"] = [v for v, c in freq_list[:5]]
        else:
            # Fallback: sample some values manually
            sample_vals = set()
            for node in list(api.N.walk())[:1000]:
                val = feature.v(node)
                if val is not None:
                    sample_vals.add(val)
                if len(sample_vals) >= 20:
                    break
            info["sample_values"] = list(sample_vals)[:5]
    except Exception:
        pass

    return info


def get_features_for_otype(api: Any, otype: str) -> List[Dict[str, Any]]:
    """
    Get all features that have values for a given otype.

    Args:
        api: Text-Fabric API object
        otype: Node type name

    Returns:
        List of feature info dicts
    """
    logger = get_logger(__name__)
    features = []

    # Get sample nodes of this type
    sample_nodes = list(api.F.otype.s(otype))[:100]
    if not sample_nodes:
        return features

    # Check each feature
    all_features = [f for f in dir(api.F) if not f.startswith("_")]

    for feature_name in all_features:
        feature = getattr(api.F, feature_name, None)
        if feature is None:
            continue

        # Check if this feature has values for this otype
        has_values = False
        try:
            for node in sample_nodes[:10]:
                val = feature.v(node)
                if val is not None:
                    has_values = True
                    break
        except Exception:
            continue

        if has_values:
            features.append(get_feature_info(api, feature_name))

    return features


def extract_full_schema(api: Any) -> Dict[str, Any]:
    """
    Extract the complete schema from the N1904 dataset.

    Args:
        api: Text-Fabric API object

    Returns:
        Complete schema dictionary
    """
    logger = get_logger(__name__)

    schema = {
        "dataset": "N1904",
        "description": "Nestle 1904 / Patriarchal Text with syntax annotations",
        "otypes": [],
        "otype_hierarchy": [],
        "otype_counts": {},
        "features_by_otype": {},
        "edge_features": [],
        "all_features": [],
    }

    # Get otypes and their counts using the correct API
    logger.info("Extracting otypes...")
    # Get all otypes from the otype feature
    all_otypes = api.F.otype.all
    for otype in all_otypes:
        count = len(list(api.F.otype.s(otype)))
        schema["otypes"].append(otype)
        schema["otype_counts"][otype] = count
        logger.info(f"  {otype}: {count:,} nodes")

    # Determine hierarchy (which otypes contain which)
    schema["otype_hierarchy"] = list(reversed(schema["otypes"]))

    # Get features for each otype
    logger.info("\nExtracting features by otype...")
    for otype in schema["otypes"]:
        logger.info(f"  Processing {otype}...")
        features = get_features_for_otype(api, otype)
        schema["features_by_otype"][otype] = features
        logger.info(f"    Found {len(features)} features")

    # Get edge features
    logger.info("\nExtracting edge features...")
    edge_features = [e for e in dir(api.E) if not e.startswith("_")]
    for edge_name in edge_features:
        edge = getattr(api.E, edge_name, None)
        if edge is not None:
            try:
                # Try to get some info about the edge
                schema["edge_features"].append({
                    "name": edge_name,
                })
                logger.info(f"  {edge_name}")
            except Exception:
                pass

    # Collect all unique feature names
    all_features = set()
    for otype_features in schema["features_by_otype"].values():
        for f in otype_features:
            all_features.add(f["name"])
    schema["all_features"] = sorted(list(all_features))

    return schema


def main(config: dict = None, dry_run: bool = False) -> bool:
    """
    Main entry point.

    Args:
        config: Pipeline configuration dict
        dry_run: If True, just report what would be done

    Returns:
        True if successful
    """
    if config is None:
        config = load_config()

    logger = get_logger(__name__)

    # Determine output path
    output_path = Path(config["paths"]["data"]["intermediate"]) / "schema_map.json"

    if dry_run:
        logger.info("[DRY RUN] Would extract schema from N1904")
        logger.info(f"[DRY RUN] Would write to: {output_path}")
        return True

    # Load N1904
    logger.info("Loading N1904 dataset...")
    try:
        A = load_n1904(config)
        api = A.api
    except Exception as e:
        logger.error(f"Failed to load N1904: {e}")
        logger.error("Make sure Text-Fabric can access the N1904 dataset.")
        logger.error("Try: python -c \"from tf.app import use; use('ETCBC/N1904')\"")
        return False

    # Extract schema
    logger.info("Extracting schema...")
    schema = extract_full_schema(api)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write schema to file
    logger.info(f"Writing schema to {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)

    # Summary
    logger.info("\nSchema extraction complete!")
    logger.info(f"  OTypes: {len(schema['otypes'])}")
    logger.info(f"  Features: {len(schema['all_features'])}")
    logger.info(f"  Edge features: {len(schema['edge_features'])}")
    logger.info(f"  Output: {output_path}")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    with ScriptLogger("p1_02_schema_scout") as logger:
        config = load_config()
        success = main(config, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
