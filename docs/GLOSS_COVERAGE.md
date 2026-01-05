# Gloss Coverage

The TR dataset achieves 100% gloss coverage through an integrated pipeline step.

## How It Works

Gloss filling is integrated into **Phase 4, Step 2** of the pipeline:

```
Phase 4: Compilation
  Step 1: Merge Data (tr_transplanted + gap_syntax → tr_complete)
  Step 2: Fill Glosses ← fills 100% of glosses
  Step 3: Generate Containers
  Step 4-8: Generate TF files
```

## Running the Pipeline

Just run the full pipeline - glosses are filled automatically:

```bash
python run_pipeline.py
```

Or run just Phase 4:

```bash
python run_pipeline.py --phase 4
```

## Coverage Progression

| Source | Coverage | Method |
|--------|----------|--------|
| N1904 transplant | 88.8% | Direct inheritance from aligned words |
| N1904 lemma lookup | +2.5% | Lookup glosses by lemma |
| Strong's lexicon | +6.6% | Lookup in greek_lexicon.db |
| Manual glosses | +2.0% | 50+ common word definitions |
| Fallbacks | +0.1% | "(name)" for proper nouns, "(rare)" for hapax |
| **Total** | **100%** | |

## Error Corrections

The script includes automatic corrections for known NLP errors:

| Word | Incorrect | Correct |
|------|-----------|---------|
| Ῥαββί | "beat with rods" | "Rabbi, Teacher" |
| μήποτε | "fall" | "lest, perhaps" |

These errors occurred because Stanza NLP produced wrong lemmas:
- Ῥαββί → lemmatized as "Ῥάβομαι" (confused with ῥαβδίζω)
- μήποτε → lemmatized as "μίπτω" (non-existent verb)

## Adding New Corrections

If you discover new gloss errors, add them to:

**File:** `scripts/phase4/p4_01b_fill_glosses.py`

```python
CORRECTIONS = [
    {
        "name": "description",
        "match_type": "lemma",  # or "word_pattern"
        "pattern": "bad_lemma",
        "correct_lemma": "correct_lemma",
        "correct_gloss": "correct gloss",
    },
    # Add new corrections here
]
```

Then re-run Phase 4:

```bash
python run_pipeline.py --phase 4
```

## Data Sources

1. **N1904 glosses** - From the aligned Nestle 1904 dataset
2. **Strong's lexicon** - `data/source/greek_lexicon.db` (5,246 entries)
3. **Manual glosses** - Defined in `MANUAL_GLOSSES` dict in p4_01b_fill_glosses.py

## Verification

To verify gloss accuracy:

```bash
python scripts/verify_glosses_thorough.py
```

This checks manual glosses against N1904 and Strong's lexicon.

See `data/verification/gloss_verification_report.md` for the full verification report.

## Technical Notes

### Unicode Normalization

Greek text uses multiple Unicode encodings. The script normalizes text before matching:

```python
def normalize_greek(text):
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text.lower()
```

### Fallback Strategy

Words that can't be glossed through lookup receive fallback values:
- **Proper names** (capitalized): "(name)"
- **Rare words**: "(rare)"

This ensures 100% coverage while being transparent about uncertainty.
