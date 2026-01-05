# Textus Receptus Text-Fabric Dataset

A complete Text-Fabric dataset for the Stephanus 1550 Textus Receptus (TR) Greek New Testament, with syntactic annotations transplanted from the N1904 (Nestle 1904) dataset.

## Overview

This project creates a syntactically-annotated Text-Fabric dataset for the TR using a "Graft and Patch" strategy:

- **~89% of words**: Syntax transplanted from the aligned N1904 dataset
- **~11% of words**: Syntax generated via Stanza NLP (for TR-only variants)

### Dataset Statistics

| Metric | Value |
|--------|-------|
| Total words | 140,726 |
| Total verses | 7,957 |
| Books | 27 (complete NT) |
| Unique lemmas | 7,943 |
| Syntax from N1904 | 88.8% |
| Syntax from NLP | 11.2% |

### High-Profile TR Variants Included

- Comma Johanneum (1 John 5:7-8)
- Eunuch's Confession (Acts 8:37)
- Pericope Adulterae (John 7:53-8:11)
- Longer Ending of Mark (Mark 16:9-20)
- Lord's Prayer Doxology (Matthew 6:13)

## Requirements

```bash
pip install -r requirements.txt
```

Key dependencies:
- Python 3.9+
- pandas
- text-fabric
- stanza (for NLP parsing)
- requests, beautifulsoup4 (for BLB download)

## Project Structure

```
tr/
├── config.yaml           # Pipeline configuration
├── run_pipeline.py       # Main pipeline runner
├── requirements.txt      # Python dependencies
├── scripts/
│   ├── download_blb_tr.py    # Download TR from Blue Letter Bible
│   ├── compare_tr_n1904.py   # Validation script
│   ├── phase1/               # Data acquisition
│   ├── phase2/               # Alignment & syntax transplant
│   ├── phase3/               # NLP for gaps
│   ├── phase4/               # Text-Fabric generation
│   ├── phase5/               # Quality assurance
│   └── utils/                # Shared utilities
├── data/
│   ├── source/               # Raw input data
│   ├── intermediate/         # Pipeline working files
│   └── output/               # Final TF dataset & reports
└── logs/                     # Pipeline execution logs
```

## Usage

### Running the Full Pipeline

```bash
python run_pipeline.py
```

Or run specific phases:

```bash
python run_pipeline.py --phase 2    # Run only Phase 2
python run_pipeline.py --from 3     # Run from Phase 3 onwards
python run_pipeline.py --dry-run    # Preview without executing
```

### Downloading Fresh TR Data

To download the TR from Blue Letter Bible (with caching):

```bash
python scripts/download_blb_tr.py          # Uses cache if available
python scripts/download_blb_tr.py --fresh  # Ignore cache, re-download everything
python scripts/download_blb_tr.py --clear-cache  # Delete cached HTML files
```

HTML pages are cached in `data/source/blb_cache/` to avoid re-scraping on subsequent runs.

### Validating Against N1904

```bash
python scripts/compare_tr_n1904.py
```

## Pipeline Phases

### Phase 1: Data Acquisition
- Download/load TR source text
- Download/load N1904 Text-Fabric dataset
- Validate source data

### Phase 2: Alignment & Syntax Transplant
- Align TR verses with N1904 verses
- Match words between aligned verses
- Transplant syntactic annotations from N1904 to TR

### Phase 3: NLP Gap Filling
- Identify words without transplanted syntax (TR-only variants)
- Parse with Stanza NLP
- Map Universal Dependencies labels to N1904 format

### Phase 4: Text-Fabric Generation
- Merge aligned and NLP-parsed data
- Generate TF node features (word, lemma, pos, case, etc.)
- Generate TF edge features (parent relationships)
- Build container nodes (book, chapter, verse)

### Phase 5: Quality Assurance
- Check for cycles in syntax trees
- Verify orphan nodes
- Validate feature completeness
- Spot-check high-profile variants
- Generate QA report

## Configuration

Edit `config.yaml` to customize:

- Data paths
- Alignment thresholds
- NLP settings
- Output features
- QA thresholds

## Data Sources

- **TR Text**: Stephanus 1550 from [Blue Letter Bible](https://www.blueletterbible.org/)
- **N1904 Syntax**: [CenterBLC/N1904](https://github.com/CenterBLC/N1904) Text-Fabric dataset

## Output

The final Text-Fabric dataset is generated in `data/output/tf/` with features including:

| Feature | Description | Coverage |
|---------|-------------|----------|
| word | Surface form | 100% |
| lemma | Dictionary form | 100% |
| sp | Part of speech | 100% |
| function | Syntactic function | 41% |
| case | Grammatical case | 57% |
| gloss | English gloss | 100% |

### Gloss Coverage

100% gloss coverage is achieved automatically as part of Phase 4:

```bash
# Just run the pipeline - glosses are filled automatically
python run_pipeline.py
```

| Source | Coverage |
|--------|----------|
| N1904 aligned | 88.8% |
| N1904 + lexicon lookup | 97.9% |
| Manual glosses + fallbacks | 100% |

See [docs/GLOSS_COVERAGE.md](docs/GLOSS_COVERAGE.md) for details.

## License

The pipeline code is provided as-is for research purposes. The underlying text data is subject to the licenses of its respective sources.
