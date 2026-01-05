# Scripts Architecture

## Design Principles

1. **Idempotent:** Each script can be run multiple times safely
2. **Configurable:** All paths and parameters come from `config.yaml`
3. **Logged:** Each script logs its actions to `logs/`
4. **Checkpointed:** Intermediate outputs saved to `data/` for resumability
5. **Testable:** Each script has a `--dry-run` mode

---

## Directory Structure

```
/home/michael/bible/tr/
├── config.yaml              # All project configuration
├── requirements.txt         # Python dependencies
├── run_pipeline.py          # Main orchestrator
├── scripts/
│   ├── __init__.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py        # Config loader
│   │   ├── logging.py       # Logging utilities
│   │   └── tf_helpers.py    # Text-Fabric utilities
│   ├── phase1/
│   │   ├── __init__.py
│   │   ├── p1_01_setup_env.py
│   │   ├── p1_02_schema_scout.py
│   │   ├── p1_03_analyze_clauses.py
│   │   ├── p1_04_acquire_tr.py
│   │   └── p1_05_build_tr_dataframe.py
│   ├── phase2/
│   │   ├── __init__.py
│   │   ├── p2_01_extract_n1904.py
│   │   ├── p2_02_align_verses.py
│   │   ├── p2_03_poc_single_book.py
│   │   ├── p2_04_full_alignment.py
│   │   ├── p2_05_build_id_map.py
│   │   └── p2_06_transplant_syntax.py
│   ├── phase3/
│   │   ├── __init__.py
│   │   ├── p3_01_analyze_gaps.py
│   │   ├── p3_02_setup_stanza.py
│   │   ├── p3_03_build_label_map.py
│   │   ├── p3_04_parse_gaps.py
│   │   ├── p3_05_convert_parses.py
│   │   └── p3_06_review_variants.py
│   ├── phase4/
│   │   ├── __init__.py
│   │   ├── p4_01_merge_data.py
│   │   ├── p4_02_generate_containers.py
│   │   ├── p4_03_configure_otypes.py
│   │   ├── p4_04_generate_features.py
│   │   ├── p4_05_generate_edges.py
│   │   ├── p4_06_generate_metadata.py
│   │   └── p4_07_verify_build.py
│   └── phase5/
│       ├── __init__.py
│       ├── p5_01_check_cycles.py
│       ├── p5_02_check_orphans.py
│       ├── p5_03_check_features.py
│       ├── p5_04_compare_stats.py
│       ├── p5_05_spot_check_variants.py
│       ├── p5_06_test_queries.py
│       ├── p5_07_test_edge_cases.py
│       └── p5_08_generate_report.py
├── data/
│   ├── source/              # Input data (TR source, downloaded files)
│   ├── intermediate/        # Checkpointed data between scripts
│   └── output/              # Final TF dataset
├── logs/                    # Script execution logs
├── reports/                 # Generated reports
└── tests/                   # Unit tests for scripts
```

---

## Script Interface Standard

Every script follows this interface:

```python
#!/usr/bin/env python3
"""
Script: p1_02_schema_scout.py
Phase: 1 - Reconnaissance
Purpose: Extract N1904 schema definition

Input:  N1904 Text-Fabric dataset (via tf.app)
Output: data/intermediate/schema_map.json

Usage:
    python -m scripts.phase1.p1_02_schema_scout
    python -m scripts.phase1.p1_02_schema_scout --dry-run
    python -m scripts.phase1.p1_02_schema_scout --verbose
"""

import argparse
from scripts.utils.config import load_config
from scripts.utils.logging import get_logger

def main(config: dict, dry_run: bool = False) -> bool:
    """
    Main entry point.

    Returns:
        True if successful, False otherwise
    """
    logger = get_logger(__name__)
    logger.info("Starting schema scout...")

    if dry_run:
        logger.info("[DRY RUN] Would extract schema from N1904")
        return True

    # Actual implementation
    ...

    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    config = load_config()
    success = main(config, dry_run=args.dry_run)
    exit(0 if success else 1)
```

---

## Pipeline Orchestrator

`run_pipeline.py` orchestrates all scripts:

```python
# Usage examples:
python run_pipeline.py                    # Run entire pipeline
python run_pipeline.py --phase 1          # Run only phase 1
python run_pipeline.py --phase 2 --step 3 # Run phase 2, step 3 onwards
python run_pipeline.py --dry-run          # Show what would run
python run_pipeline.py --resume           # Resume from last checkpoint
```

---

## Script Dependency Graph

```
Phase 1:
p1_01 → p1_02 → p1_03
              ↘
p1_04 → p1_05

Phase 2 (requires Phase 1):
p1_05 + p1_02 → p2_01 → p2_02 → p2_03 → p2_04 → p2_05 → p2_06

Phase 3 (requires Phase 2):
p2_04 (gaps.csv) → p3_01 → p3_02 → p3_03 → p3_04 → p3_05 → p3_06

Phase 4 (requires Phase 2 + Phase 3):
p2_06 + p3_05 → p4_01 → p4_02 → p4_03 → p4_04 → p4_05 → p4_06 → p4_07

Phase 5 (requires Phase 4):
p4_07 → p5_01 → p5_02 → p5_03 → p5_04 → p5_05 → p5_06 → p5_07 → p5_08
```

---

## Data Files (Checkpoints)

| Script | Output File | Format |
|--------|-------------|--------|
| p1_02 | `data/intermediate/schema_map.json` | JSON |
| p1_03 | `data/intermediate/clause_analysis.json` | JSON |
| p1_05 | `data/intermediate/tr_words.parquet` | Parquet |
| p2_01 | `data/intermediate/n1904_words.parquet` | Parquet |
| p2_04 | `data/intermediate/alignment_map.parquet` | Parquet |
| p2_04 | `data/intermediate/gaps.csv` | CSV |
| p2_05 | `data/intermediate/id_translation.parquet` | Parquet |
| p2_06 | `data/intermediate/tr_transplanted.parquet` | Parquet |
| p3_01 | `data/intermediate/gap_spans.csv` | CSV |
| p3_03 | `data/intermediate/label_map.json` | JSON |
| p3_04 | `data/intermediate/gap_parses/` | CoNLL-U |
| p3_05 | `data/intermediate/gap_syntax.parquet` | Parquet |
| p4_01 | `data/intermediate/tr_complete.parquet` | Parquet |
| p4_02 | `data/intermediate/tr_containers.parquet` | Parquet |
| p4_04-06 | `data/output/tf/` | TF files |

---

## Error Handling

Each script:
1. Validates inputs exist before processing
2. Validates outputs after processing
3. Logs errors with full stack traces
4. Returns non-zero exit code on failure
5. Can be safely re-run (idempotent)

---

## Testing

```bash
# Run all tests
pytest tests/

# Run tests for specific phase
pytest tests/test_phase1.py

# Run with coverage
pytest --cov=scripts tests/
```
