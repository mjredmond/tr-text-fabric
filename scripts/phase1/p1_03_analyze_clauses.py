#!/usr/bin/env python3
"""
Script: p1_03_analyze_clauses.py
Phase: 1 - Reconnaissance
Purpose: Document how N1904 handles embedded/nested clauses

Input:  data/intermediate/schema_map.json, N1904 dataset
Output: data/intermediate/clause_analysis.json

Usage:
    python -m scripts.phase1.p1_03_analyze_clauses
    python -m scripts.phase1.p1_03_analyze_clauses --dry-run
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils.config import load_config
from scripts.utils.logging import ScriptLogger, get_logger
from scripts.utils.tf_helpers import load_n1904


def analyze_clause_structure(api: Any) -> Dict[str, Any]:
    """
    Analyze how clauses are structured and nested in N1904.

    Args:
        api: Text-Fabric API object

    Returns:
        Analysis dict with clause structure documentation
    """
    logger = get_logger(__name__)
    analysis = {
        "clause_types": {},
        "nesting_patterns": [],
        "parent_child_examples": [],
        "max_nesting_depth": 0,
        "features_on_clauses": [],
    }

    # Get clause types
    logger.info("Analyzing clause types...")
    if hasattr(api.F, "type"):
        for clause in list(api.F.otype.s("clause"))[:1000]:
            clause_type = api.F.type.v(clause)
            if clause_type:
                analysis["clause_types"][clause_type] = analysis["clause_types"].get(clause_type, 0) + 1

    # Analyze parent-child relationships
    logger.info("Analyzing clause nesting...")
    if hasattr(api.E, "parent"):
        sample_clauses = list(api.F.otype.s("clause"))[:100]
        for clause in sample_clauses:
            # Get parents
            parents = api.E.parent.t(clause) if hasattr(api.E.parent, "t") else []
            # Get children
            children = api.E.parent.f(clause) if hasattr(api.E.parent, "f") else []

            if parents or children:
                example = {
                    "clause_id": clause,
                    "parent_count": len(parents) if parents else 0,
                    "child_count": len(children) if children else 0,
                }
                if len(analysis["parent_child_examples"]) < 10:
                    analysis["parent_child_examples"].append(example)

    # Get features available on clauses
    logger.info("Identifying clause features...")
    sample_clause = list(api.F.otype.s("clause"))[0]
    for feature_name in dir(api.F):
        if feature_name.startswith("_"):
            continue
        feature = getattr(api.F, feature_name, None)
        if feature:
            try:
                val = feature.v(sample_clause)
                if val is not None:
                    analysis["features_on_clauses"].append(feature_name)
            except Exception:
                pass

    return analysis


def main(config: dict = None, dry_run: bool = False) -> bool:
    """Main entry point."""
    if config is None:
        config = load_config()

    logger = get_logger(__name__)

    # Paths
    schema_path = Path(config["paths"]["data"]["intermediate"]) / "schema_map.json"
    output_path = Path(config["paths"]["data"]["intermediate"]) / "clause_analysis.json"

    if dry_run:
        logger.info("[DRY RUN] Would analyze clause structure in N1904")
        logger.info(f"[DRY RUN] Would read: {schema_path}")
        logger.info(f"[DRY RUN] Would write to: {output_path}")
        return True

    # Verify schema exists
    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        logger.error("Run p1_02_schema_scout.py first")
        return False

    # Load N1904
    logger.info("Loading N1904 dataset...")
    try:
        A = load_n1904(config)
        api = A.api
    except Exception as e:
        logger.error(f"Failed to load N1904: {e}")
        return False

    # Analyze clause structure
    logger.info("Analyzing clause structure...")
    analysis = analyze_clause_structure(api)

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)

    logger.info(f"Analysis written to: {output_path}")
    logger.info(f"  Clause types found: {len(analysis['clause_types'])}")
    logger.info(f"  Features on clauses: {len(analysis['features_on_clauses'])}")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    with ScriptLogger("p1_03_analyze_clauses") as logger:
        config = load_config()
        success = main(config, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
