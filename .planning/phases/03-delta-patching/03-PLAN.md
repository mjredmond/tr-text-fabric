# Phase 3: Delta Patching (AI Processing)

## Objective
Generate syntax trees for TR-exclusive readings (~2% of text) using NLP and LLM review.

## Context
The gaps identified in Phase 2 represent text that exists in TR but not in N1904 (or differs significantly). These include famous variants like:
- **1 John 5:7-8** - Comma Johanneum
- **Acts 8:37** - Ethiopian eunuch's confession
- **1 Timothy 3:16** - "God" vs "who"
- **Revelation 22:19** - "book" vs "tree" of life

For these passages, we must generate syntax annotations that match N1904's schema.

---

## Tasks

### Task 3.1: Gap Analysis and Categorization
**Goal:** Understand the scope and nature of gaps.

**Steps:**
- [ ] Load `gaps.csv` from Phase 2
- [ ] Categorize gaps by type:
  - Single word additions
  - Multi-word phrase additions
  - Word substitutions
  - Entire verse additions (e.g., Acts 8:37)
- [ ] Group gaps by contiguous spans (adjacent gap words form a single unit)
- [ ] Generate `gap_spans.csv` with:
  - `span_id`, `book`, `chapter`, `verse`
  - `start_word_rank`, `end_word_rank`
  - `text` (full Greek text of span)
  - `word_count`
  - `category`

**Verification:**
- Every word in `gaps.csv` belongs to exactly one span
- Span text is coherent Greek

**Output:** `gap_spans.csv`, `gap_analysis_report.md`

---

### Task 3.2: Stanza Configuration
**Goal:** Set up Stanza NLP for Ancient Greek dependency parsing.

**Steps:**
- [ ] Install Stanza Ancient Greek model:
  ```python
  import stanza
  stanza.download('grc')
  ```
- [ ] Test on sample Greek text
- [ ] Document Stanza's output format (CoNLL-U)
- [ ] Identify available dependency relations in Stanza's `grc` model

**Verification:**
```python
import stanza
nlp = stanza.Pipeline('grc', processors='tokenize,pos,lemma,depparse')
doc = nlp("ἐν ἀρχῇ ἦν ὁ λόγος")
for sent in doc.sentences:
    for word in sent.words:
        print(f"{word.text}\t{word.deprel}\t{word.head}")
```

**Output:** Working Stanza pipeline, documentation of output format

---

### Task 3.3: UD-to-N1904 Label Mapping ("Rosetta Stone")
**Goal:** Create mapping from Stanza's Universal Dependencies labels to N1904's schema.

**Steps:**
- [ ] Research N1904's label system (likely Lowfat/OpenText based)
- [ ] Research Stanza's UD label system for Ancient Greek
- [ ] Create `label_map.json` with mappings:
  ```json
  {
    "nsubj": "Subject",
    "obj": "Object",
    "iobj": "IndirectObject",
    "obl": "Adjunct",
    "advmod": "Adverb",
    ...
  }
  ```
- [ ] Document any labels that require special handling
- [ ] Identify unmappable labels and decision strategy

**Verification:**
- Every Stanza label has a mapping or documented exception
- Test mapping on sample parsed output

**Output:** `label_map.json`, mapping documentation

---

### Task 3.4: Batch Stanza Processing
**Goal:** Generate dependency parses for all gap spans.

**Steps:**
- [ ] Write `parse_gaps.py` that:
  - Loads `gap_spans.csv`
  - Runs Stanza on each span's text
  - Outputs CoNLL-U format per span
  - Stores results in `gap_parses/` directory (one file per span)
- [ ] Handle tokenization differences:
  - Stanza may tokenize differently than TR source
  - Align Stanza tokens back to TR word positions

**Verification:**
- Every span has a parse file
- Token count matches word count (or differences documented)

**Output:** `gap_parses/` directory with CoNLL-U files

---

### Task 3.5: Parse-to-N1904 Conversion
**Goal:** Convert Stanza output to N1904-compatible format.

**Steps:**
- [ ] Write `convert_parses.py` that:
  - Reads each CoNLL-U file
  - Applies `label_map.json` to dependency relations
  - Assigns TR node IDs to parsed words
  - Creates clause/phrase containers based on parse structure
  - Outputs N1904-schema compatible records
- [ ] Handle container creation:
  - Stanza provides flat dependency trees
  - N1904 has explicit clause/phrase containers
  - Heuristic: Verb-headed subtrees = clauses, noun-headed = phrases
- [ ] Export as `gap_syntax.parquet`

**Verification:**
```python
gap_syntax = pd.read_parquet('gap_syntax.parquet')
# Should have all required N1904 columns
required_cols = ['word_id', 'parent', 'function', 'role', 'clause_id', 'phrase_id']
for col in required_cols:
    assert col in gap_syntax.columns
```

**Output:** `gap_syntax.parquet`

---

### Task 3.6: High-Profile Verse Review (LLM)
**Goal:** Human/LLM review of theologically significant variants.

**Steps:**
- [ ] Identify priority verses for review:
  - 1 John 5:7-8 (Comma Johanneum)
  - Acts 8:37 (Eunuch's confession)
  - 1 Timothy 3:16 (θεός variant)
  - Mark 16:9-20 (Longer ending)
  - John 7:53-8:11 (Pericope Adulterae)
  - Revelation 22:19 (βιβλίου variant)
- [ ] For each priority verse:
  - Extract generated syntax tree
  - Format for LLM review prompt:
    ```
    Verse: [Greek text]
    Generated Syntax:
    [Tree representation]

    Review for:
    1. Subject-predicate agreement
    2. Proper case function assignment
    3. Clause boundary correctness
    4. Any grammatical anomalies
    ```
  - Apply any corrections
- [ ] Document all LLM-suggested changes

**Verification:**
- Each priority verse has review documentation
- Any changes are justified and recorded

**Output:** `reviews/` directory with per-verse review docs, updated `gap_syntax.parquet`

---

## Deliverables Checklist

- [ ] `gap_spans.csv` - Contiguous gap spans
- [ ] `gap_analysis_report.md` - Gap statistics
- [ ] `label_map.json` - UD to N1904 mapping
- [ ] `gap_parses/` - Stanza CoNLL-U output
- [ ] `gap_syntax.parquet` - Converted syntax data
- [ ] `reviews/` - LLM review documentation

---

## Exit Criteria

Phase 3 is complete when:
1. All gap spans are parsed by Stanza
2. All parses are converted to N1904 schema
3. High-profile verses are reviewed and validated
4. No gaps remain without syntax annotation

---

## Files Created This Phase

```
/home/michael/bible/tr/
├── scripts/
│   ├── parse_gaps.py
│   └── convert_parses.py
├── data/
│   ├── gap_spans.csv
│   ├── label_map.json
│   ├── gap_parses/
│   │   ├── span_001.conllu
│   │   ├── span_002.conllu
│   │   └── ...
│   └── gap_syntax.parquet
├── reviews/
│   ├── 1john_5_7-8.md
│   ├── acts_8_37.md
│   └── ...
├── reports/
│   └── gap_analysis_report.md
```
