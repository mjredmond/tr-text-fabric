# Phase 2: The Great Alignment

## Objective
Map N1904 syntax trees onto TR text where words are identical (~98% of text).

## Context
The TR and N1904 are both Byzantine text-type manuscripts with approximately 98% textual identity. By aligning these texts at the verse level and matching individual words, we can transplant the carefully annotated N1904 syntax data onto the TR without manual re-annotation.

**Critical Challenge:** Node IDs in syntax trees are pointers. When we transplant data, all parent/child references must be re-indexed to point to the new TR word positions.

---

## Tasks

### Task 2.1: N1904 Data Extraction
**Goal:** Extract all N1904 word-level data into a DataFrame for alignment.

**Steps:**
- [ ] Write `extract_n1904.py` script that:
  - Loads N1904 via Text-Fabric
  - Extracts all words with: `book`, `chapter`, `verse`, `word_rank`, `word`, `lemma`, `parsing`
  - Extracts all syntactic features: `parent`, `clause_atom`, `function`, `role`, etc.
  - Preserves original `node_id` for later re-indexing
- [ ] Export as `n1904_words.parquet`

**Verification:**
```python
df = pd.read_parquet('n1904_words.parquet')
assert 'node_id' in df.columns
assert 'parent' in df.columns
```

**Output:** `n1904_words.parquet` file

---

### Task 2.2: Verse-Level Alignment Framework
**Goal:** Create alignment infrastructure that matches texts verse by verse.

**Steps:**
- [ ] Write `align_verses.py` script that:
  - Groups both DataFrames by `(book, chapter, verse)`
  - For each verse pair, applies `difflib.SequenceMatcher`
  - Match criteria: `lemma` + key parsing features (case, tense, voice, mood)
  - Returns alignment mappings: `[(n1904_word_idx, tr_word_idx), ...]`
- [ ] Handle edge cases:
  - Verse present in TR but not N1904 (mark as gap)
  - Verse present in N1904 but not TR (skip)
  - Word order differences within verse

**Verification:**
- Test on known identical verses (should achieve 100% alignment)
- Test on known variant verses (should correctly identify gaps)

**Output:** `align_verses.py` module

---

### Task 2.3: Proof of Concept - Single Book Alignment
**Goal:** Validate alignment approach on a small, mostly-identical book.

**Steps:**
- [ ] Select test book: 3 John (shortest NT book, minimal variants)
- [ ] Run alignment on 3 John only
- [ ] Generate alignment report:
  - Total words in TR
  - Total words aligned
  - Words flagged as gaps
  - Alignment percentage
- [ ] Manual review of any gaps (should be minimal)

**Verification:**
- Alignment percentage > 95% for 3 John
- Any gaps are legitimate TR/N1904 differences

**Output:** `poc_3john_report.md` with alignment statistics

---

### Task 2.4: Full Text Alignment
**Goal:** Run alignment across entire NT.

**Steps:**
- [ ] Execute alignment for all 27 books
- [ ] Generate comprehensive alignment report by book
- [ ] Collect all gaps into `gaps.csv` with columns:
  - `book`, `chapter`, `verse`, `word_rank`
  - `tr_word`, `tr_lemma`
  - `gap_type`: "addition" (TR has word N1904 lacks) or "substitution"
- [ ] Export alignment mappings as `alignment_map.parquet`

**Verification:**
```python
gaps = pd.read_csv('gaps.csv')
alignment = pd.read_parquet('alignment_map.parquet')
total_words = len(tr_df)
aligned_words = len(alignment)
print(f"Aligned: {aligned_words/total_words:.1%}")  # Should be ~98%
```

**Output:**
- `alignment_map.parquet`
- `gaps.csv`
- `alignment_report.md`

---

### Task 2.5: ID Translation Table
**Goal:** Create mapping from N1904 node IDs to TR node IDs.

**Steps:**
- [ ] Write `build_id_map.py` that:
  - Takes alignment mappings
  - Creates `id_translation.parquet` with columns: `n1904_node_id`, `tr_node_id`
  - For container nodes (clauses, phrases), assigns new sequential IDs
- [ ] Document the ID offset formula for re-indexing

**Verification:**
- Every aligned word has an entry in translation table
- Container nodes have valid new IDs
- No ID collisions

**Output:** `id_translation.parquet`

---

### Task 2.6: Syntax Transplantation
**Goal:** Copy syntactic features from N1904 to TR for aligned words.

**Steps:**
- [ ] Write `transplant_syntax.py` that:
  - Loads TR DataFrame and alignment map
  - For each aligned word, copies all syntactic features
  - Re-indexes all `parent` pointers using ID translation table
  - Preserves clause/phrase container structures
- [ ] Handle edge cases:
  - Parent node not in translation table (should not happen for aligned text)
  - Missing features (use schema_map.json defaults)
- [ ] Export as `tr_transplanted.parquet`

**Verification:**
```python
# Verify no broken parent pointers
tr = pd.read_parquet('tr_transplanted.parquet')
valid_ids = set(tr['tr_node_id'])
for parent_id in tr['parent'].dropna():
    assert parent_id in valid_ids or parent_id == 0  # 0 = root
```

**Output:** `tr_transplanted.parquet`

---

## Deliverables Checklist

- [ ] `n1904_words.parquet` - N1904 extracted data
- [ ] `align_verses.py` - Alignment module
- [ ] `poc_3john_report.md` - Proof of concept results
- [ ] `alignment_map.parquet` - Full alignment mappings
- [ ] `gaps.csv` - All unaligned TR words
- [ ] `id_translation.parquet` - Node ID mappings
- [ ] `tr_transplanted.parquet` - TR with transplanted syntax

---

## Exit Criteria

Phase 2 is complete when:
1. Full NT alignment is run with documented statistics
2. All gaps are identified and exported
3. Syntax transplantation is complete for aligned text
4. No broken parent pointers in transplanted data
5. Alignment percentage is approximately 98%

---

## Files Created This Phase

```
/home/michael/bible/tr/
├── scripts/
│   ├── extract_n1904.py
│   ├── align_verses.py
│   ├── build_id_map.py
│   └── transplant_syntax.py
├── data/
│   ├── n1904_words.parquet
│   ├── alignment_map.parquet
│   ├── gaps.csv
│   ├── id_translation.parquet
│   └── tr_transplanted.parquet
├── reports/
│   ├── poc_3john_report.md
│   └── alignment_report.md
```
