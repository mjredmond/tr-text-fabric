#!/usr/bin/env python3
"""
Script: p1_01_setup_env.py
Phase: 1 - Reconnaissance
Purpose: Verify all required dependencies are installed and functional

Input:  None
Output: None (prints status)

Usage:
    python -m scripts.phase1.p1_01_setup_env
    python -m scripts.phase1.p1_01_setup_env --verbose
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils.config import load_config
from scripts.utils.logging import ScriptLogger, get_logger


def check_import(module_name: str, package_name: str = None) -> bool:
    """
    Try to import a module and report success/failure.

    Args:
        module_name: The module to import
        package_name: Display name if different from module name

    Returns:
        True if import succeeded
    """
    logger = get_logger(__name__)
    display_name = package_name or module_name

    try:
        __import__(module_name)
        logger.info(f"  [OK] {display_name}")
        return True
    except ImportError as e:
        logger.error(f"  [FAIL] {display_name}: {e}")
        return False


def main(config: dict = None, dry_run: bool = False) -> bool:
    """
    Main entry point.

    Args:
        config: Pipeline configuration dict
        dry_run: If True, just report what would be checked

    Returns:
        True if all checks pass
    """
    if config is None:
        config = load_config()

    logger = get_logger(__name__)
    logger.info("Checking required dependencies...")

    if dry_run:
        logger.info("[DRY RUN] Would check all dependencies")
        return True

    all_ok = True

    # Core dependencies
    logger.info("\nCore Libraries:")
    all_ok &= check_import("pandas")
    all_ok &= check_import("pyarrow")
    all_ok &= check_import("yaml", "pyyaml")

    # Text-Fabric
    logger.info("\nText-Fabric:")
    all_ok &= check_import("tf", "text-fabric")

    # Try to load Text-Fabric API
    try:
        from tf.fabric import Fabric
        logger.info("  [OK] Text-Fabric API available")
    except Exception as e:
        logger.error(f"  [FAIL] Text-Fabric API: {e}")
        all_ok = False

    # NLP
    logger.info("\nNLP Libraries:")
    all_ok &= check_import("stanza")

    # Check Stanza Ancient Greek model
    try:
        import stanza
        # Just check if we can create the pipeline class
        logger.info("  [OK] Stanza available (grc model may need download)")
    except Exception as e:
        logger.error(f"  [FAIL] Stanza: {e}")
        all_ok = False

    # Optional dependencies
    logger.info("\nOptional Libraries:")
    check_import("tqdm")  # Not required but nice to have
    check_import("requests")

    # Check directory structure
    logger.info("\nDirectory Structure:")
    root = Path(config["paths"]["root"])
    required_dirs = [
        "data/source",
        "data/intermediate",
        "data/output",
        "logs",
        "reports",
    ]

    for dir_path in required_dirs:
        full_path = root / dir_path
        if full_path.exists():
            logger.info(f"  [OK] {dir_path}/")
        else:
            logger.info(f"  [CREATE] {dir_path}/")
            full_path.mkdir(parents=True, exist_ok=True)

    # Summary
    logger.info("")
    if all_ok:
        logger.info("All required dependencies are installed!")
        return True
    else:
        logger.error("Some dependencies are missing. Please install them:")
        logger.error("  pip install -r requirements.txt")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    with ScriptLogger("p1_01_setup_env") as logger:
        config = load_config()
        success = main(config, dry_run=args.dry_run)
        sys.exit(0 if success else 1)
