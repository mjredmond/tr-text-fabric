# Hierarchical Structure Implementation Plan

This document outlines the practical approach to adding clause, phrase, and sentence structure to the TR dataset.

## Data Analysis Summary

### Word-Level Alignment

| Status | Count | % | Description |
|--------|-------|---|-------------|
| Aligned | 124,961 | 88.8% | Direct N1904 match, structure can be transplanted |
| Inferable | 11,823 | 8.4% | Word form exists in N1904, position differs |
| Unknown | 3,942 | 2.8% | Spelling variants, mostly proper names |

### Verse-Level Coverage

| Category | Verses | % | Words | % |
|----------|--------|---|-------|---|
| 100% aligned | 1,812 | 22.8% | 26,211 | 18.6% |
| All words known | 5,026 | 63.2% | 83,824 | 59.6% |
| Has unknowns | 2,931 | 36.8% | 56,902 | 40.4% |

### Key Insight

The "11% gap" is misleading. Only **2.8%** of words are truly unknown. The rest are known words in different positions, which can be handled with pattern lookup.

---

## Implementation Approach

### Tier 1: Direct Transplant (22.8% of verses)

**Scope**: Verses where every TR word aligns 1:1 with N1904

**Method**:
1. Identify verses with 100% word alignment
2. Copy clause/phrase/sentence structure from N1904
3. Remap N1904 node IDs to TR node space
4. Remap word slots to TR word IDs

**Confidence**: High (100%)

**Output**:
- `structure_source = "n1904_direct"`
- `structure_confidence = 1.0`

### Tier 2: Transplant + Inference (40.4% additional verses)

**Scope**: Verses where all words exist in N1904, but positions differ

**Method**:
1. Transplant structure for aligned words
2. For inferable words, determine placement by:
   - Matching to adjacent aligned words' phrases
   - Looking up typical phrase membership for that word form
   - Using POS-based heuristics (articles join nearest noun, etc.)

**Example**:
```
TR:    ὁ     βασιλεὺς  Δαβὶδ
       ↓     ↓         (not aligned)
N1904: -     βασιλεύς  Δαυίδ

Strategy: "ὁ" is an article → attach to same NP as βασιλεύς
```

**Confidence**: Medium (0.8-0.9)

**Output**:
- `structure_source = "n1904_inferred"`
- `structure_confidence = 0.85`

### Tier 3: Lookup Table for Unknowns (2.8% of words)

**Scope**: Spelling variants and TR-only forms (mostly proper names)

**Method**:
1. Build lookup table mapping unknown forms to:
   - Canonical N1904 equivalent (by Strong's number)
   - Default phrase type (NP for nouns/names)
   - Default syntactic role

**Example Mappings**:
| TR Form | Strong's | N1904 Equivalent | Default Type |
|---------|----------|------------------|--------------|
| Δαβίδ | G1138 | Δαυίδ | NP |
| Φάρες | G5329 | Φαρές | NP |
| Ἑσρώμ | G2074 | Ἑσρώμ | NP |

**Estimated Effort**:
- ~300-400 unique unknown forms
- ~2-4 hours to build lookup table
- Can be semi-automated by Strong's number matching

**Confidence**: Medium-High (0.85-0.95 for names, lower for other forms)

**Output**:
- `structure_source = "lookup"`
- `structure_confidence = 0.9` (names) / `0.75` (other)

---

## Implementation Steps

### Phase 1: Data Preparation

**Script**: `scripts/phase4/p4_08a_prepare_structure_data.py`

1. Load TR and N1904 data
2. Classify each TR word as: aligned / inferable / unknown
3. Build verse-level alignment statistics
4. Export classification for downstream steps

**Output**: `data/intermediate/tr_structure_classification.parquet`

### Phase 2: Direct Transplant

**Script**: `scripts/phase4/p4_08b_transplant_structure.py`

1. Identify 100%-aligned verses (1,812 verses)
2. For each verse:
   - Load N1904 clause/phrase/sentence structure
   - Map N1904 word nodes to TR word nodes
   - Create TR structure nodes with remapped slots
3. Track parent-child relationships

**Output**: `data/intermediate/tr_structure_direct.parquet`

### Phase 3: Inference Engine

**Script**: `scripts/phase4/p4_08c_infer_structure.py`

1. Build N1904 word-to-phrase-type lookup
2. Build POS-based attachment rules:
   - Articles → attach to nearest noun's phrase
   - Conjunctions → typically clause boundaries
   - Prepositions → start PP
3. For each inferable word:
   - Find adjacent aligned words
   - Determine phrase membership
   - Assign to existing or new phrase node

**Output**: `data/intermediate/tr_structure_inferred.parquet`

### Phase 4: Unknown Word Handling

**Script**: `scripts/phase4/p4_08d_handle_unknowns.py`

1. Extract unique unknown word forms
2. Match to N1904 by Strong's number where possible
3. Generate lookup table with defaults
4. Manual review of ambiguous cases (~50-100 words)
5. Apply lookup to assign structure

**Output**:
- `data/source/unknown_word_mappings.csv` (manual review)
- `data/intermediate/tr_structure_complete.parquet`

### Phase 5: Structure Generation

**Script**: `scripts/phase4/p4_08e_generate_structure_nodes.py`

1. Merge all structure data
2. Generate clause nodes with features:
   - `clausetype`, `cltype`, `rela`
3. Generate phrase nodes with features:
   - `typ`, `function`, `rela`
4. Generate sentence nodes
5. Build oslots mappings
6. Build parent edges

**Output**: Structure nodes in TF format

### Phase 6: Verification

**Script**: `scripts/phase5/p5_03_verify_structure.py`

1. Check for orphan words (not in any phrase)
2. Check for cycles in parent relationships
3. Verify clause/phrase/sentence hierarchy
4. Spot-check known passages:
   - John 1:1-5 (complex structure)
   - Romans 8:28-30 (nested clauses)
   - Comma Johanneum (TR-only)
5. Compare structure to N1904 for aligned verses

**Output**: `data/output/reports/structure_qa_report.md`

---

## N1904 Structure Features to Transplant

### Clause Features
| Feature | Description |
|---------|-------------|
| `clausetype` | Main, subordinate, relative, etc. |
| `cltype` | Clause type code |
| `rela` | Relation to parent clause |

### Phrase Features
| Feature | Description |
|---------|-------------|
| `typ` | NP, PP, VP, AdjP, AdvP |
| `function` | Subject, object, predicate, etc. |
| `rela` | Relation to parent |

### Word Group Features
| Feature | Description |
|---------|-------------|
| `junction` | Coordination type |
| `rule` | Syntactic rule applied |

---

## Confidence Score System

| Source | Base Confidence | Adjustments |
|--------|-----------------|-------------|
| Direct transplant | 1.0 | - |
| Inferred (article/conj) | 0.9 | -0.05 per inference step |
| Inferred (other) | 0.8 | -0.05 per inference step |
| Lookup (proper name) | 0.9 | - |
| Lookup (other) | 0.75 | - |

Words with confidence < 0.7 will be flagged for review.

---

## Estimated Effort

| Phase | Task | Hours |
|-------|------|-------|
| 1 | Data preparation | 2 |
| 2 | Direct transplant | 4 |
| 3 | Inference engine | 8 |
| 4 | Unknown handling | 4 |
| 5 | Structure generation | 4 |
| 6 | Verification | 4 |
| **Total** | | **26 hours** |

---

## Success Criteria

- [ ] 100% of words have phrase assignment
- [ ] 100% of phrases have clause assignment
- [ ] No orphan nodes in hierarchy
- [ ] No cycles in parent relationships
- [ ] Direct transplant verses match N1904 exactly
- [ ] Structure confidence scores are calibrated
- [ ] QA report shows <5% flagged items
- [ ] Spot-check passages pass manual review

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Inference errors compound | Wrong phrase boundaries | Confidence scoring, human review |
| Proper name handling | Incorrect NP boundaries | Strong's-based lookup, manual review |
| Word order differences | Phrase structure mismatch | Conservative attachment rules |
| N1904 structure inconsistencies | Inherited errors | Document as known limitation |

---

## Future Enhancements

1. **ML refinement**: Train model on direct-transplant verses to improve inference
2. **Scholar review**: Flag low-confidence structures for expert correction
3. **Community corrections**: Accept pull requests for structure fixes
