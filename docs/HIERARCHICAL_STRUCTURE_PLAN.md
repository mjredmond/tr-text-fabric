# Hierarchical Structure Implementation Plan

This document outlines the plan to add hierarchical syntactic structure (clause, phrase, sentence, wg nodes) to the TR Text-Fabric dataset.

## Current State Analysis

### Verse Alignment Statistics

| Category | Verses | % | Words | % |
|----------|--------|---|-------|---|
| 100% aligned (Option B) | 1,812 | 22.8% | 26,211 | 18.6% |
| Partially aligned (Option C) | 6,127 | 77.0% | 114,289 | 81.2% |
| No alignment | 18 | 0.2% | 226 | 0.2% |
| **Total** | **7,957** | **100%** | **140,726** | **100%** |

### N1904 Node Types to Add

| Node Type | N1904 Count | Description |
|-----------|-------------|-------------|
| clause | 42,505 | Clause-level groupings |
| phrase | 69,006 | Phrase-level groupings |
| sentence | 8,010 | Sentence boundaries |
| group | 8,944 | Coordination groups |
| subphrase | 116,178 | Sub-phrase constituents |
| wg | 106,867 | Word groups (generic) |

### N1904 Structure Features to Add

| Feature | Applies To | Description |
|---------|------------|-------------|
| clausetype | clause | Type of clause |
| cltype | clause | Clause type code |
| rela | clause, phrase, wg | Relation to parent |
| typ | phrase, wg | Phrase/group type |
| rule | various | Syntactic rule |
| junction | various | Coordination type |
| appositioncontainer | wg | Apposition marker |
| articular | phrase | Has article |
| discontinuous | phrase | Discontinuous phrase |

---

## Phase 3A: Option B - 100% Aligned Verses

### Approach

For verses where ALL words align with N1904, transplant the complete syntactic structure.

### Implementation Steps

#### Step 1: Identify Transplantable Structure

```
For each verse with 100% word alignment:
  1. Get all N1904 word node IDs for this verse
  2. Find all N1904 structure nodes that contain ONLY these words
  3. These structure nodes can be safely transplanted
```

#### Step 2: Build Node Mapping

```
For each transplantable N1904 structure node:
  1. Record node type (clause/phrase/wg/etc.)
  2. Record slot range (which words it contains)
  3. Map N1904 word slots → TR word slots
  4. Assign new TR node ID
```

#### Step 3: Copy Structure Features

```
For each transplanted node:
  1. Copy all applicable features (clausetype, rela, typ, etc.)
  2. Set source='n1904' to indicate provenance
  3. Set confidence=1.0 (fully aligned)
```

#### Step 4: Rebuild Containment

```
For each transplanted node:
  1. Compute oslots (TR word slots contained)
  2. Preserve parent-child relationships between structure nodes
```

### Expected Output

- ~1,812 verses with full syntactic structure
- ~18.6% word coverage with hierarchical annotation
- 100% confidence on all structure nodes

### Script

`scripts/phase4/p4_08a_transplant_aligned_structure.py`

---

## Phase 3B: Option C - Partially Aligned Verses

### NLP Tool: Stanza Dependency Parsing

Ancient Greek's free word order makes constituency parsing unreliable. The state-of-the-art
approach uses **dependency parsing** (see [NLP-progress](http://nlpprogress.com/english/constituency_parsing.html)).

**Stanza** (already in pipeline) provides Ancient Greek dependency parsing:

```python
import stanza
nlp = stanza.Pipeline('grc', processors='tokenize,pos,lemma,depparse')
doc = nlp('ἐν ἀρχῇ ἦν ὁ λόγος')

# Output:
# ἐν: head=ἀρχῇ, deprel=case      → groups into PP with ἀρχῇ
# ἀρχῇ: head=ROOT, deprel=root
# ἦν: head=ἀρχῇ, deprel=cop
# ὁ: head=λόγος, deprel=det       → groups into NP with λόγος
# λόγος: head=ἀρχῇ, deprel=nsubj
```

**Dependency → Phrase Structure Conversion**:

| Head POS | Dependents | → Phrase Type |
|----------|------------|---------------|
| subs/pron | det, amod, nmod | NP |
| prep | + governed NP | PP |
| adjv | advmod | AdjP |
| advb | advmod | AdvP |
| verb | subj, obj, obl | VP/Clause |

### Approach

For verses with partial alignment, use Stanza dependency parsing + heuristics to adapt N1904 structure.

### Strategy: Structure Inheritance with Gaps

#### Case 1: Structure Node Spans Only Aligned Words (Easy)

```
N1904 phrase: [word1, word2, word3] - all aligned to TR
→ Transplant directly, confidence=1.0
```

#### Case 2: Structure Node Has Gap Words (Medium)

```
N1904 phrase: [word1, word2, word3, word4]
TR alignment:  [yes,   yes,   NO,    yes]

Options:
  A) Extend structure to include TR-only word at position 3
     → confidence=0.8, flag='extended'

  B) Split structure around gap
     → Two smaller structures, confidence=0.7, flag='split'

  C) Skip this structure node
     → No structure for these words
```

#### Case 3: TR Has Extra Words Not in N1904 (Hard)

```
TR verse: [w1, w2, w3_extra, w4, w5]
N1904:    [w1, w2,          w4, w5]

Strategy:
  1. Transplant N1904 structure for [w1,w2,w4,w5]
  2. For w3_extra: attach to nearest structure based on:
     - Word order (attach to preceding phrase)
     - Part of speech compatibility
     - Syntactic role hints from word-level features
  → confidence=0.6, flag='extended_with_tr_only'
```

### Heuristic Rules

#### Rule 1: Extend Small Gaps

```
IF structure_node contains N words
AND only 1-2 words are unaligned
AND unaligned words are interior (not at edges)
THEN extend structure to include unaligned words
     confidence = 0.85
```

#### Rule 2: Preserve Majority Structure

```
IF structure_node contains N words
AND >= 70% are aligned
THEN extend to include all words in TR verse range
     confidence = 0.7
```

#### Rule 3: Attach Orphan Words

```
IF TR word has no structure node
AND adjacent TR word has structure node
AND POS is compatible (e.g., article before noun)
THEN attach orphan to adjacent structure
     confidence = 0.6
```

#### Rule 4: Generate Structure for TR-Only Segments (N1904-Informed)

**Priority 1: Strong's Number Lookup**
```
IF TR word has Strong's number
AND Strong's number exists in N1904
THEN:
  1. Look up typical phrase type for this Strong's number
  2. Group with adjacent words that share compatible Strong's patterns
  confidence = 0.85-0.9
  source = 'n1904_strong'
```

**Priority 2: POS Bigram Patterns**
```
IF consecutive TR-only words exist
THEN:
  1. Check POS bigrams against N1904 patterns:
     - prep + art  → PP (94% confidence in N1904)
     - prep + pron → PP (94%)
     - prep + subs → PP (94%)
     - art + subs  → NP (66%)
     - subs + adjv → NP (78%)
  2. Group words matching these patterns
  confidence = 0.75-0.85
  source = 'n1904_pattern'
```

**Priority 3: Stanza Fallback**
```
IF no N1904 pattern matches
THEN:
  1. Run Stanza dependency parse on the segment
  2. Convert dependency tree to phrase structure
  3. Validate against N1904 patterns where possible
  confidence = 0.5-0.7
  source = 'stanza'
```

### N1904 Lookup Tables to Build

| Table | Size | Usage |
|-------|------|-------|
| Strong's → phrase type | 3,258 | Primary lookup for TR words |
| POS bigram → phrase type | ~100 | Boundary detection |
| POS sequence → phrase type | ~500 | Full phrase matching |
| Lemma → typical role | ~5,000 | Role assignment |

### Implementation Steps

#### Step 0: Build N1904 Lookup Tables

```python
def build_n1904_lookups():
    """Pre-compute lookup tables from N1904 for TR generation."""

    # 1. Strong's number → phrase type distribution
    strong_to_phrase = {}  # {strong: {NP: 100, PP: 20, ...}}

    # 2. POS bigram → phrase type
    bigram_to_phrase = {}  # {(prep, art): {PP: 94%, NP: 6%}}

    # 3. POS sequence → phrase type (for 2-5 word sequences)
    sequence_to_phrase = {}  # {(art, subs, pron): NP}

    # 4. Lemma → typical phrase position
    lemma_to_role = {}  # {lemma: {head: 50%, dependent: 50%}}

    # Save to data/intermediate/n1904_structure_lookups.json
```

Script: `scripts/phase4/p4_07_build_structure_lookups.py`

#### Step 1: Analyze Each Verse

```python
for verse in partially_aligned_verses:
    tr_words = get_tr_words(verse)
    n1904_words = get_aligned_n1904_words(verse)
    n1904_structures = get_n1904_structures(n1904_words)

    for structure in n1904_structures:
        coverage = compute_alignment_coverage(structure, tr_words)
        decide_strategy(structure, coverage)
```

#### Step 2: Apply Heuristics

```python
def decide_strategy(structure, coverage):
    if coverage == 1.0:
        return transplant_direct(structure)
    elif coverage >= 0.7:
        return extend_structure(structure)
    elif coverage >= 0.5:
        return split_or_extend(structure)
    else:
        return skip_structure(structure)
```

#### Step 3: Handle Orphans

```python
def handle_orphan_words(verse):
    orphans = get_words_without_structure(verse)
    for orphan in orphans:
        neighbor = find_best_neighbor_structure(orphan)
        if neighbor and is_compatible(orphan, neighbor):
            attach_to_structure(orphan, neighbor)
        else:
            create_minimal_wg(orphan)
```

#### Step 4: Assign Confidence Scores

| Scenario | Confidence | Source |
|----------|------------|--------|
| Direct transplant (100% aligned) | 1.0 | n1904 |
| Extended with 1 gap word | 0.85 | extended |
| Extended with 2+ gap words | 0.7 | extended |
| Majority alignment (≥70%) | 0.7 | extended |
| Strong's number lookup match | 0.85-0.9 | n1904_strong |
| POS bigram pattern match | 0.75-0.85 | n1904_pattern |
| Orphan attached to neighbor | 0.6 | heuristic |
| Stanza-generated structure | 0.5-0.7 | stanza |

### Expected Output

- ~6,127 verses with heuristic structure
- ~81.2% additional word coverage
- Variable confidence scores (0.4-1.0)
- `structure_source` feature: 'n1904' | 'extended' | 'generated'
- `structure_confidence` feature: 0.0-1.0

### Script

`scripts/phase4/p4_08b_heuristic_structure.py`

---

## Phase 3C: Verification Plan for Option C

### Automated Verification

#### Test 1: Structural Integrity

```python
def verify_structural_integrity():
    """Verify no orphan words, no overlapping structures"""

    for word in all_words:
        structures = get_containing_structures(word)
        assert len(structures) >= 1, f"Orphan word: {word}"

    for s1, s2 in all_structure_pairs:
        if s1.type == s2.type:  # Same level
            slots1 = set(s1.slots)
            slots2 = set(s2.slots)
            overlap = slots1 & slots2
            assert len(overlap) == 0 or slots1 <= slots2 or slots2 <= slots1
```

#### Test 2: Hierarchy Consistency

```python
def verify_hierarchy():
    """Verify proper nesting: sentence > clause > phrase > word"""

    for clause in all_clauses:
        parent_sentence = get_parent(clause, 'sentence')
        assert parent_sentence is not None or is_independent_clause(clause)

    for phrase in all_phrases:
        parent = get_parent(phrase, ['clause', 'wg'])
        assert parent is not None
```

#### Test 3: Feature Completeness

```python
def verify_features():
    """Verify required features are present"""

    for clause in all_clauses:
        assert clause.clausetype is not None or clause.source == 'generated'

    for phrase in all_phrases:
        assert phrase.typ is not None or phrase.source == 'generated'
```

#### Test 4: Confidence Distribution

```python
def verify_confidence_distribution():
    """Check confidence scores are reasonable"""

    confidence_scores = [n.confidence for n in all_structure_nodes]

    # At least 20% should be high confidence (≥0.85)
    high_conf = sum(1 for c in confidence_scores if c >= 0.85)
    assert high_conf / len(confidence_scores) >= 0.20

    # Average should be reasonable
    avg_conf = sum(confidence_scores) / len(confidence_scores)
    assert avg_conf >= 0.65
```

### Manual Spot-Check Verification

#### Check 1: High-Profile Passages

Manually verify structure for:

1. **John 3:16** - Famous verse, should have clear structure
2. **Romans 8:28-30** - Complex theology, tests clause handling
3. **Ephesians 1:3-14** - Long sentence, tests sentence boundaries
4. **1 John 5:7-8** - Comma Johanneum, TR-only content
5. **Acts 8:37** - Eunuch's confession, TR-only verse

```python
def spot_check_passage(book, chapter, verse):
    """Print structure for manual review"""

    print(f"=== {book} {chapter}:{verse} ===")
    words = get_verse_words(book, chapter, verse)

    for word in words:
        structures = get_containing_structures(word)
        indent = "  " * len(structures)
        print(f"{indent}{word.text} [{word.confidence}]")
        for s in structures:
            print(f"    -> {s.type}: {s.typ} (conf={s.confidence})")
```

#### Check 2: Random Sample Review

```python
def random_sample_review(n=50):
    """Review random verses for structure quality"""

    verses = random.sample(all_verses, n)

    for verse in verses:
        print_verse_structure(verse)
        # Manual review: Does structure look reasonable?
        # Flag issues for investigation
```

#### Check 3: Low-Confidence Review

```python
def review_low_confidence():
    """Review all structures with confidence < 0.5"""

    low_conf = [n for n in all_structure_nodes if n.confidence < 0.5]

    for node in low_conf[:100]:  # Review first 100
        print_structure_context(node)
        # Manual review: Is the heuristic reasonable?
```

### Comparison Verification

#### Compare with N1904 on Aligned Content

```python
def compare_with_n1904():
    """For 100% aligned verses, compare structure exactly"""

    for verse in fully_aligned_verses:
        tr_structure = get_tr_structure(verse)
        n1904_structure = get_n1904_structure(verse)

        # Should match exactly
        assert structures_equivalent(tr_structure, n1904_structure)
```

#### Cross-Reference with Word Features

```python
def verify_structure_word_consistency():
    """Verify structure aligns with word-level features"""

    for phrase in all_phrases:
        if phrase.typ == 'NP':  # Noun phrase
            words = get_phrase_words(phrase)
            # Should contain at least one noun/pronoun
            has_noun = any(w.sp in ['subs', 'pron'] for w in words)
            if not has_noun:
                flag_for_review(phrase, "NP without noun")
```

### Verification Report Template

```markdown
## Hierarchical Structure Verification Report

### Summary Statistics
- Total structure nodes: X
- By type: clause=X, phrase=X, wg=X, ...
- Average confidence: X.XX
- Low confidence (<0.5): X nodes (X%)

### Automated Tests
- [ ] Structural integrity: PASS/FAIL
- [ ] Hierarchy consistency: PASS/FAIL
- [ ] Feature completeness: PASS/FAIL
- [ ] Confidence distribution: PASS/FAIL

### Manual Spot-Checks
- [ ] John 3:16: OK/ISSUES
- [ ] Romans 8:28-30: OK/ISSUES
- [ ] Ephesians 1:3-14: OK/ISSUES
- [ ] 1 John 5:7-8: OK/ISSUES
- [ ] Acts 8:37: OK/ISSUES

### Random Sample (50 verses)
- Reviewed: X/50
- Issues found: X
- Issue types: ...

### Low-Confidence Review
- Reviewed: X/100
- Acceptable: X
- Problematic: X
- Action items: ...

### Recommendations
1. ...
2. ...
```

---

## Implementation Order

1. **Phase 3A**: Implement Option B (100% aligned verses)
   - Script: `p4_08a_transplant_aligned_structure.py`
   - Test on small sample first
   - Verify against N1904 exactly

2. **Phase 3B**: Implement Option C (partially aligned verses)
   - Script: `p4_08b_heuristic_structure.py`
   - Start with high-coverage verses (≥90% aligned)
   - Progressively handle lower coverage

3. **Phase 3C**: Run verification suite
   - Script: `p4_09_verify_structure.py`
   - Generate verification report
   - Manual review of flagged items

4. **Iterate**: Fix issues found in verification

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Incorrect structure | Confidence scores + source tracking |
| Performance issues | Process in batches by book |
| Edge cases | Extensive test suite |
| User confusion | Clear documentation of limitations |

---

## Success Criteria

- [ ] 100% of words contained in at least one structure node
- [ ] No overlapping same-level structures
- [ ] Proper hierarchical nesting
- [ ] Average confidence ≥ 0.65
- [ ] Manual spot-checks pass
- [ ] Automated tests pass
