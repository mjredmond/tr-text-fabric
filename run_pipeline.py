#!/usr/bin/env python3
"""
TR Text-Fabric Pipeline Orchestrator

Runs all pipeline scripts in sequence with proper dependency handling,
logging, and checkpoint/resume support.

Usage:
    python run_pipeline.py                      # Run entire pipeline
    python run_pipeline.py --phase 1            # Run only phase 1
    python run_pipeline.py --phase 2 --step 3   # Run phase 2 from step 3
    python run_pipeline.py --dry-run            # Show what would run
    python run_pipeline.py --list               # List all scripts
    python run_pipeline.py --status             # Show pipeline status
"""

import argparse
import importlib
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from scripts.utils.config import load_config, ensure_directories
from scripts.utils.logging import setup_logging, get_logger


@dataclass
class ScriptInfo:
    """Information about a pipeline script."""
    phase: int
    step: int
    module: str
    name: str
    description: str
    inputs: List[str]
    outputs: List[str]


# Define all pipeline scripts
PIPELINE_SCRIPTS: List[ScriptInfo] = [
    # Phase 1: Reconnaissance
    ScriptInfo(
        phase=1, step=1,
        module="scripts.phase1.p1_01_setup_env",
        name="Setup Environment",
        description="Verify all dependencies are installed",
        inputs=[],
        outputs=[]
    ),
    ScriptInfo(
        phase=1, step=2,
        module="scripts.phase1.p1_02_schema_scout",
        name="Schema Scout",
        description="Extract N1904 schema definition",
        inputs=["N1904 dataset"],
        outputs=["data/intermediate/schema_map.json"]
    ),
    ScriptInfo(
        phase=1, step=3,
        module="scripts.phase1.p1_03_analyze_clauses",
        name="Analyze Clauses",
        description="Document embedded clause handling",
        inputs=["data/intermediate/schema_map.json"],
        outputs=["data/intermediate/clause_analysis.json"]
    ),
    ScriptInfo(
        phase=1, step=4,
        module="scripts.phase1.p1_04_acquire_tr",
        name="Acquire TR Data",
        description="Download and prepare TR source text",
        inputs=[],
        outputs=["data/source/tr_raw.csv"]
    ),
    ScriptInfo(
        phase=1, step=5,
        module="scripts.phase1.p1_05_build_tr_dataframe",
        name="Build TR DataFrame",
        description="Create standardized TR word DataFrame",
        inputs=["data/source/tr_raw.csv"],
        outputs=["data/intermediate/tr_words.parquet"]
    ),

    # Phase 2: Alignment
    ScriptInfo(
        phase=2, step=1,
        module="scripts.phase2.p2_01_extract_n1904",
        name="Extract N1904",
        description="Extract N1904 words with syntax features",
        inputs=["N1904 dataset"],
        outputs=["data/intermediate/n1904_words.parquet"]
    ),
    ScriptInfo(
        phase=2, step=2,
        module="scripts.phase2.p2_02_align_verses",
        name="Align Verses",
        description="Create verse alignment framework",
        inputs=["data/intermediate/tr_words.parquet", "data/intermediate/n1904_words.parquet"],
        outputs=[]
    ),
    ScriptInfo(
        phase=2, step=3,
        module="scripts.phase2.p2_03_poc_single_book",
        name="PoC Single Book",
        description="Proof of concept on 3 John",
        inputs=["data/intermediate/tr_words.parquet", "data/intermediate/n1904_words.parquet"],
        outputs=["reports/poc_3john_report.md"]
    ),
    ScriptInfo(
        phase=2, step=4,
        module="scripts.phase2.p2_04_full_alignment",
        name="Full Alignment",
        description="Run alignment on entire NT",
        inputs=["data/intermediate/tr_words.parquet", "data/intermediate/n1904_words.parquet"],
        outputs=["data/intermediate/alignment_map.parquet", "data/intermediate/gaps.csv"]
    ),
    ScriptInfo(
        phase=2, step=5,
        module="scripts.phase2.p2_05_build_id_map",
        name="Build ID Map",
        description="Create node ID translation table",
        inputs=["data/intermediate/alignment_map.parquet"],
        outputs=["data/intermediate/id_translation.parquet"]
    ),
    ScriptInfo(
        phase=2, step=6,
        module="scripts.phase2.p2_06_transplant_syntax",
        name="Transplant Syntax",
        description="Copy syntax features to aligned TR words",
        inputs=["data/intermediate/alignment_map.parquet", "data/intermediate/id_translation.parquet"],
        outputs=["data/intermediate/tr_transplanted.parquet"]
    ),

    # Phase 3: Delta Patching
    ScriptInfo(
        phase=3, step=1,
        module="scripts.phase3.p3_01_analyze_gaps",
        name="Analyze Gaps",
        description="Categorize and group gap spans",
        inputs=["data/intermediate/gaps.csv"],
        outputs=["data/intermediate/gap_spans.csv", "reports/gap_analysis_report.md"]
    ),
    ScriptInfo(
        phase=3, step=2,
        module="scripts.phase3.p3_02_setup_stanza",
        name="Setup Stanza",
        description="Configure Stanza NLP for Ancient Greek",
        inputs=[],
        outputs=[]
    ),
    ScriptInfo(
        phase=3, step=3,
        module="scripts.phase3.p3_03_build_label_map",
        name="Build Label Map",
        description="Create UD to N1904 label mapping",
        inputs=["data/intermediate/schema_map.json"],
        outputs=["data/intermediate/label_map.json"]
    ),
    ScriptInfo(
        phase=3, step=4,
        module="scripts.phase3.p3_04_parse_gaps",
        name="Parse Gaps",
        description="Run Stanza on all gap spans",
        inputs=["data/intermediate/gap_spans.csv"],
        outputs=["data/intermediate/gap_parses/"]
    ),
    ScriptInfo(
        phase=3, step=5,
        module="scripts.phase3.p3_05_convert_parses",
        name="Convert Parses",
        description="Convert Stanza output to N1904 format",
        inputs=["data/intermediate/gap_parses/", "data/intermediate/label_map.json"],
        outputs=["data/intermediate/gap_syntax.parquet"]
    ),
    ScriptInfo(
        phase=3, step=6,
        module="scripts.phase3.p3_06_review_variants",
        name="Review Variants",
        description="LLM review of high-profile variants",
        inputs=["data/intermediate/gap_syntax.parquet"],
        outputs=["reviews/"]
    ),

    # Phase 4: Compilation
    ScriptInfo(
        phase=4, step=1,
        module="scripts.phase4.p4_01_merge_data",
        name="Merge Data",
        description="Combine transplanted and patched data",
        inputs=["data/intermediate/tr_transplanted.parquet", "data/intermediate/gap_syntax.parquet"],
        outputs=["data/intermediate/tr_complete.parquet"]
    ),
    ScriptInfo(
        phase=4, step=2,
        module="scripts.phase4.p4_02_generate_containers",
        name="Generate Containers",
        description="Create clause/phrase/sentence nodes",
        inputs=["data/intermediate/tr_complete.parquet"],
        outputs=["data/intermediate/tr_containers.parquet"]
    ),
    ScriptInfo(
        phase=4, step=3,
        module="scripts.phase4.p4_03_configure_otypes",
        name="Configure OTypes",
        description="Set up node type hierarchy",
        inputs=["data/intermediate/schema_map.json"],
        outputs=[]
    ),
    ScriptInfo(
        phase=4, step=4,
        module="scripts.phase4.p4_04_generate_features",
        name="Generate Features",
        description="Write node feature .tf files",
        inputs=["data/intermediate/tr_complete.parquet", "data/intermediate/tr_containers.parquet"],
        outputs=["data/output/tf/"]
    ),
    ScriptInfo(
        phase=4, step=5,
        module="scripts.phase4.p4_05_generate_edges",
        name="Generate Edges",
        description="Write edge feature .tf files",
        inputs=["data/intermediate/tr_complete.parquet"],
        outputs=["data/output/tf/parent.tf"]
    ),
    ScriptInfo(
        phase=4, step=6,
        module="scripts.phase4.p4_06_generate_metadata",
        name="Generate Metadata",
        description="Write TF metadata files",
        inputs=[],
        outputs=["data/output/tf/otext.tf", "data/output/tf/__desc__.tf"]
    ),
    ScriptInfo(
        phase=4, step=7,
        module="scripts.phase4.p4_07_verify_build",
        name="Verify Build",
        description="Test that TF dataset loads correctly",
        inputs=["data/output/tf/"],
        outputs=[]
    ),

    # Phase 5: QA
    ScriptInfo(
        phase=5, step=1,
        module="scripts.phase5.p5_01_check_cycles",
        name="Check Cycles",
        description="Detect circular dependencies in syntax trees",
        inputs=["data/output/tf/"],
        outputs=["qa_results/qa_cycle_check.log"]
    ),
    ScriptInfo(
        phase=5, step=2,
        module="scripts.phase5.p5_02_check_orphans",
        name="Check Orphans",
        description="Detect orphan and dangling nodes",
        inputs=["data/output/tf/"],
        outputs=["qa_results/qa_orphan_check.log"]
    ),
    ScriptInfo(
        phase=5, step=3,
        module="scripts.phase5.p5_03_check_features",
        name="Check Features",
        description="Verify all required features present",
        inputs=["data/output/tf/", "data/intermediate/schema_map.json"],
        outputs=["qa_results/qa_feature_check.log"]
    ),
    ScriptInfo(
        phase=5, step=4,
        module="scripts.phase5.p5_04_compare_stats",
        name="Compare Stats",
        description="Statistical comparison with N1904",
        inputs=["data/output/tf/"],
        outputs=["qa_results/qa_stats_comparison.md"]
    ),
    ScriptInfo(
        phase=5, step=5,
        module="scripts.phase5.p5_05_spot_check_variants",
        name="Spot Check Variants",
        description="Manual verification of high-profile variants",
        inputs=["data/output/tf/"],
        outputs=["qa_results/qa_variant_reviews/"]
    ),
    ScriptInfo(
        phase=5, step=6,
        module="scripts.phase5.p5_06_test_queries",
        name="Test Queries",
        description="Verify TF queries work correctly",
        inputs=["data/output/tf/"],
        outputs=["qa_results/qa_query_tests.log"]
    ),
    ScriptInfo(
        phase=5, step=7,
        module="scripts.phase5.p5_07_test_edge_cases",
        name="Test Edge Cases",
        description="Test unusual grammatical constructions",
        inputs=["data/output/tf/"],
        outputs=["qa_results/qa_edge_cases.log"]
    ),
    ScriptInfo(
        phase=5, step=8,
        module="scripts.phase5.p5_08_generate_report",
        name="Generate Report",
        description="Create final QA report",
        inputs=["qa_results/"],
        outputs=["reports/QA_FINAL_REPORT.md"]
    ),
]


# Status file location
STATUS_FILE = Path(__file__).parent / "data" / "pipeline_status.json"


def load_status() -> Dict:
    """Load pipeline execution status."""
    if STATUS_FILE.exists():
        with open(STATUS_FILE, "r") as f:
            return json.load(f)
    return {"completed": [], "last_run": None}


def save_status(status: Dict) -> None:
    """Save pipeline execution status."""
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATUS_FILE, "w") as f:
        json.dump(status, f, indent=2, default=str)


def get_script_key(script: ScriptInfo) -> str:
    """Get unique key for a script."""
    return f"p{script.phase}_{script.step:02d}"


def run_script(script: ScriptInfo, config: dict, dry_run: bool = False) -> bool:
    """
    Run a single pipeline script.

    Args:
        script: Script info
        config: Pipeline config
        dry_run: If True, just print what would be done

    Returns:
        True if successful
    """
    logger = get_logger(__name__)
    key = get_script_key(script)

    logger.info(f"\n{'='*60}")
    logger.info(f"Running: [{key}] {script.name}")
    logger.info(f"Description: {script.description}")
    logger.info(f"{'='*60}")

    if dry_run:
        logger.info("[DRY RUN] Would run: %s", script.module)
        return True

    try:
        # Dynamically import the module
        module = importlib.import_module(script.module)

        # Call the main function
        if hasattr(module, "main"):
            success = module.main(config)
            return success if isinstance(success, bool) else True
        else:
            logger.warning(f"Module {script.module} has no main() function")
            return False

    except ModuleNotFoundError as e:
        logger.error(f"Module not found: {script.module}")
        logger.error(f"Error: {e}")
        logger.info("(This is expected if the script hasn't been implemented yet)")
        return False

    except Exception as e:
        logger.error(f"Script failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def list_scripts() -> None:
    """Print all pipeline scripts."""
    print("\nTR Text-Fabric Pipeline Scripts")
    print("=" * 70)

    current_phase = 0
    for script in PIPELINE_SCRIPTS:
        if script.phase != current_phase:
            current_phase = script.phase
            print(f"\nPhase {current_phase}:")
            print("-" * 40)

        key = get_script_key(script)
        print(f"  [{key}] {script.name}")
        print(f"         {script.description}")

    print()


def show_status(config: dict) -> None:
    """Show current pipeline status."""
    status = load_status()

    print("\nPipeline Status")
    print("=" * 70)
    print(f"Last run: {status.get('last_run', 'Never')}")
    print()

    current_phase = 0
    for script in PIPELINE_SCRIPTS:
        if script.phase != current_phase:
            current_phase = script.phase
            print(f"\nPhase {current_phase}:")
            print("-" * 40)

        key = get_script_key(script)
        completed = key in status.get("completed", [])
        marker = "[x]" if completed else "[ ]"

        # Check if outputs exist
        outputs_exist = True
        for output in script.outputs:
            output_path = Path(config["paths"]["root"]) / output
            if not output_path.exists():
                outputs_exist = False
                break

        output_marker = "+" if outputs_exist else "-"

        print(f"  {marker} [{key}] {script.name} {output_marker}")

    print()
    print("Legend: [x]=completed, [ ]=pending, +=outputs exist, -=outputs missing")
    print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--phase", "-p",
        type=int,
        help="Run only this phase (1-5)"
    )
    parser.add_argument(
        "--step", "-s",
        type=int,
        default=1,
        help="Start from this step within the phase"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Show what would be run without executing"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all scripts"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show pipeline status"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last completed step"
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        default=True,
        help="Stop on first failure (default: True)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    # Load config
    config = load_config()

    # Handle special commands
    if args.list:
        list_scripts()
        return 0

    if args.status:
        show_status(config)
        return 0

    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging("pipeline", config, log_level)
    logger = get_logger(__name__)

    # Ensure directories exist
    ensure_directories(config)

    # Load status for resume
    status = load_status()

    # Filter scripts to run
    scripts_to_run = []
    for script in PIPELINE_SCRIPTS:
        # Phase filter
        if args.phase and script.phase != args.phase:
            continue

        # Step filter (within phase)
        if args.phase and script.step < args.step:
            continue

        # Resume filter
        if args.resume:
            key = get_script_key(script)
            if key in status.get("completed", []):
                continue

        scripts_to_run.append(script)

    if not scripts_to_run:
        logger.info("No scripts to run!")
        return 0

    logger.info(f"Running {len(scripts_to_run)} scripts...")

    if args.dry_run:
        logger.info("[DRY RUN MODE]")

    # Run scripts
    failed = []
    for script in scripts_to_run:
        success = run_script(script, config, args.dry_run)

        if success and not args.dry_run:
            key = get_script_key(script)
            if key not in status.get("completed", []):
                status.setdefault("completed", []).append(key)
            status["last_run"] = datetime.now().isoformat()
            save_status(status)
        elif not success:
            failed.append(script)
            if args.fail_fast:
                logger.error("Stopping due to failure (--fail-fast)")
                break

    # Summary
    print()
    print("=" * 60)
    if failed:
        print(f"FAILED: {len(failed)} script(s) failed")
        for script in failed:
            print(f"  - [{get_script_key(script)}] {script.name}")
        return 1
    else:
        print(f"SUCCESS: {len(scripts_to_run)} script(s) completed")
        return 0


if __name__ == "__main__":
    sys.exit(main())
