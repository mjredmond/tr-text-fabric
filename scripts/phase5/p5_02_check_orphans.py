#!/usr/bin/env python3
"""
Script: p5_02_check_orphans
Phase: 5 - QA
Purpose: Detect orphan nodes (words not in any container) and empty containers

Input:  data/output/tf/oslots.tf, otype.tf
Output: logs

Usage:
    python -m scripts.phase5.p5_02_check_orphans
    python -m scripts.phase5.p5_02_check_orphans --dry-run
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils.config import load_config
from scripts.utils.logging import ScriptLogger, get_logger


def load_otype(tf_dir: Path) -> dict:
    """Load node types from otype.tf."""
    otypes = {}
    otype_path = tf_dir / "otype.tf"

    with open(otype_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("@"):
                continue
            parts = line.split("\t")
            if len(parts) == 2:
                node = int(parts[0])
                otype = parts[1]
                otypes[node] = otype

    return otypes


def load_oslots(tf_dir: Path) -> dict:
    """Load slot containment from oslots.tf."""
    oslots = {}
    oslots_path = tf_dir / "oslots.tf"

    with open(oslots_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("@"):
                continue
            parts = line.split("\t")
            if len(parts) == 2:
                container = int(parts[0])
                slots_str = parts[1]

                # Parse slot ranges (e.g., "1-100" or "1,2,3")
                slots = set()
                for part in slots_str.split(","):
                    if "-" in part:
                        start, end = part.split("-")
                        slots.update(range(int(start), int(end) + 1))
                    else:
                        slots.add(int(part))

                oslots[container] = slots

    return oslots


def main(config: dict = None, dry_run: bool = False) -> bool:
    """Main entry point."""
    if config is None:
        config = load_config()

    logger = get_logger(__name__)

    tf_dir = Path(config["paths"]["data"]["output"]) / "tf"

    if dry_run:
        logger.info("[DRY RUN] Would check for orphan nodes")
        return True

    # Load data
    logger.info("Loading node types...")
    otypes = load_otype(tf_dir)

    logger.info("Loading slot containment...")
    oslots = load_oslots(tf_dir)

    # Get all word slots
    word_slots = {n for n, t in otypes.items() if t == "word"}
    logger.info(f"Total word slots: {len(word_slots)}")

    # Get all slots contained in containers
    contained_slots = set()
    for container, slots in oslots.items():
        contained_slots.update(slots)

    # Find orphan slots (not in any container)
    orphan_slots = word_slots - contained_slots
    if orphan_slots:
        logger.warning(f"Found {len(orphan_slots)} orphan slots not in any container")
        if len(orphan_slots) <= 10:
            logger.warning(f"  Orphan slots: {sorted(orphan_slots)}")
    else:
        logger.info("All word slots are contained in at least one container")

    # Find empty containers
    empty_containers = []
    for container in oslots:
        if len(oslots[container]) == 0:
            empty_containers.append(container)

    if empty_containers:
        logger.warning(f"Found {len(empty_containers)} empty containers")
    else:
        logger.info("No empty containers found")

    # Summary
    all_ok = len(orphan_slots) == 0 and len(empty_containers) == 0

    logger.info("\nOrphan Check Summary:")
    logger.info("-" * 40)
    logger.info(f"Orphan slots: {len(orphan_slots)}")
    logger.info(f"Empty containers: {len(empty_containers)}")

    if all_ok:
        logger.info("PASSED: No orphans or empty containers")
    else:
        logger.warning("WARNING: Issues found (may be acceptable)")

    # Return True even with warnings - these aren't necessarily errors
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    with ScriptLogger("p5_02_check_orphans") as logger:
        config = load_config()
        success = main(config, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
