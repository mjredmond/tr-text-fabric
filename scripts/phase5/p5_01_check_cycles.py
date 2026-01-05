#!/usr/bin/env python3
"""
Script: p5_01_check_cycles
Phase: 5 - QA
Purpose: Detect circular dependencies in syntax trees

Input:  data/output/tf/parent.tf
Output: logs

Usage:
    python -m scripts.phase5.p5_01_check_cycles
    python -m scripts.phase5.p5_01_check_cycles --dry-run
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils.config import load_config
from scripts.utils.logging import ScriptLogger, get_logger


def load_parent_edges(tf_dir: Path) -> dict:
    """Load parent edges from parent.tf file."""
    parent_map = {}
    parent_path = tf_dir / "parent.tf"

    if not parent_path.exists():
        return parent_map

    with open(parent_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("@"):
                continue
            parts = line.split("\t")
            if len(parts) == 2:
                child = int(parts[0])
                parent = int(parts[1])
                parent_map[child] = parent

    return parent_map


def detect_cycles(parent_map: dict) -> list:
    """
    Detect cycles in the parent relationships using DFS.

    Returns list of (node, cycle_path) tuples for any cycles found.
    """
    cycles = []
    visited = set()

    for node in parent_map:
        if node in visited:
            continue

        # Trace path from this node
        path = []
        current = node
        path_set = set()

        while current is not None:
            if current in path_set:
                # Cycle found - extract the cycle
                cycle_start = path.index(current)
                cycle = path[cycle_start:] + [current]
                cycles.append((node, cycle))
                break

            path.append(current)
            path_set.add(current)
            visited.add(current)
            current = parent_map.get(current)

    return cycles


def main(config: dict = None, dry_run: bool = False) -> bool:
    """Main entry point."""
    if config is None:
        config = load_config()

    logger = get_logger(__name__)

    tf_dir = Path(config["paths"]["data"]["output"]) / "tf"

    if dry_run:
        logger.info("[DRY RUN] Would check for cycles in syntax trees")
        return True

    # Load parent edges
    logger.info("Loading parent edges...")
    parent_map = load_parent_edges(tf_dir)
    logger.info(f"Loaded {len(parent_map)} parent relationships")

    if len(parent_map) == 0:
        logger.info("No parent edges to check")
        return True

    # Detect cycles
    logger.info("Checking for cycles...")
    cycles = detect_cycles(parent_map)

    if cycles:
        logger.error(f"FAILED: Found {len(cycles)} cycles!")
        for node, cycle in cycles[:10]:  # Show first 10
            logger.error(f"  Cycle at node {node}: {' -> '.join(map(str, cycle))}")
        return False
    else:
        logger.info("PASSED: No cycles detected")
        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    with ScriptLogger("p5_01_check_cycles") as logger:
        config = load_config()
        success = main(config, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
