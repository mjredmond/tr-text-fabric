# Phase 1: Reconnaissance & Schema Extraction

## Objective
Map exactly which features exist in N1904 so we can replicate the structure.

## Context
Before we can transplant syntax data from N1904 to TR, we must understand:
1. What node types (otypes) exist in N1904
2. What features each node type carries
3. How embedded structures (clauses within clauses) are represented
4. How to uniquely identify each word in the TR source

---

## Tasks

### Task 1.1: Environment Setup
**Goal:** Ensure all required libraries are installed and functional.

**Steps:**
- [ ] Install Python dependencies: `text-fabric`, `pandas`, `stanza`, `difflib`
- [ ] Verify Text-Fabric can load N1904 dataset
- [ ] Test Stanza Ancient Greek model loads correctly

**Verification:**
```python
from tf.app import use
A = use('ETCBC/N1904')
# Should load without errors
```

**Output:** Working environment confirmed

---

### Task 1.2: N1904 Schema Probe
**Goal:** Extract complete schema definition from N1904.

**Steps:**
- [ ] Write `schema_scout.py` script that:
  - Lists all otypes (e.g., `book`, `chapter`, `verse`, `sentence`, `clause`, `phrase`, `word`)
  - Lists all node features per otype
  - Lists all edge features
  - Documents feature data types and example values
- [ ] Run script and capture output
- [ ] Create `schema_map.json` with structured definition

**Verification:**
```python
# schema_map.json should contain entries like:
{
  "otypes": ["book", "chapter", "verse", "sentence", "clause", "phrase", "word"],
  "features": {
    "word": ["sp", "gn", "nu", "ps", "case", "tense", "voice", "mood", ...],
    "clause": ["function", "type", ...],
    ...
  }
}
```

**Output:** `schema_map.json` file

---

### Task 1.3: Embedded Clause Analysis
**Goal:** Understand how N1904 represents clause nesting.

**Steps:**
- [ ] Query N1904 for example of embedded clause
- [ ] Document the parent-child relationship pattern
- [ ] Identify which features mark embedding level
- [ ] Note any edge features used for clause relationships

**Verification:**
- Clear documentation of how clause nesting works
- Example output showing parent/child clause structure

**Output:** Section added to schema documentation

---

### Task 1.4: TR Source Acquisition
**Goal:** Obtain and standardize TR text with morphology.

**Steps:**
- [ ] Download Robinson-Pierpont 2018 (or Scrivener 1894) in machine-readable format
- [ ] Identify available fields: word, lemma, parsing codes
- [ ] Document the parsing code schema (e.g., V-PAI-3S = Verb, Present Active Indicative, 3rd Singular)

**Verification:**
- TR data file exists and is readable
- Parsing codes are understood

**Output:** TR source data file (CSV/JSON)

---

### Task 1.5: TR DataFrame Construction
**Goal:** Load TR into standardized DataFrame with unique word identifiers.

**Steps:**
- [ ] Create `load_tr.py` script that:
  - Reads TR source file
  - Creates DataFrame with columns: `book`, `chapter`, `verse`, `word_rank`, `word`, `lemma`, `parsing`
  - Assigns unique `word_id` to each word (sequential integer)
- [ ] Validate word count against known TR statistics
- [ ] Export as `tr_words.parquet` for efficient reloading

**Verification:**
```python
df = pd.read_parquet('tr_words.parquet')
assert 'word_id' in df.columns
assert df['word_id'].is_unique
assert len(df) > 140000  # TR has ~140K words
```

**Output:** `tr_words.parquet` file

---

## Deliverables Checklist

- [ ] Working Python environment with all dependencies
- [ ] `schema_map.json` - Complete N1904 feature schema
- [ ] Documented understanding of embedded clause handling
- [ ] TR source data acquired
- [ ] `tr_words.parquet` - Standardized TR word DataFrame

---

## Exit Criteria

Phase 1 is complete when:
1. N1904 schema is fully documented in `schema_map.json`
2. Embedded clause handling is understood and documented
3. TR text is loaded into DataFrame with unique word IDs
4. All scripts are functional and tested

---

## Files Created This Phase

```
/home/michael/bible/tr/
├── scripts/
│   ├── schema_scout.py
│   └── load_tr.py
├── data/
│   ├── schema_map.json
│   ├── tr_source/
│   │   └── [TR raw data files]
│   └── tr_words.parquet
```
