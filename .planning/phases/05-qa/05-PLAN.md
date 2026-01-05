# Phase 5: Quality Assurance

## Objective
Verify dataset integrity, correctness, and usability before release.

## Context
A syntactic dataset with errors can lead to incorrect biblical analysis. We must verify:
1. **Structural integrity:** No cycles or orphans in the tree structure
2. **Data completeness:** Every node has required features
3. **Correctness:** Syntax annotations match the Greek grammar
4. **Usability:** Dataset works with standard Text-Fabric workflows

---

## Tasks

### Task 5.1: Cycle Detection
**Goal:** Ensure no circular dependencies in syntax trees.

**Steps:**
- [ ] Write `check_cycles.py` that:
  - Builds a directed graph from parent relationships
  - Runs DFS to detect cycles
  - Reports any node that is its own ancestor
- [ ] Algorithm:
  ```python
  def has_cycle(node, visited, rec_stack, parent_map):
      visited.add(node)
      rec_stack.add(node)
      parent = parent_map.get(node)
      if parent:
          if parent in rec_stack:
              return True, node  # Cycle found
          if parent not in visited:
              result = has_cycle(parent, visited, rec_stack, parent_map)
              if result[0]:
                  return result
      rec_stack.remove(node)
      return False, None
  ```
- [ ] Report all cycles found (should be 0)

**Verification:**
- Script runs on entire dataset
- No cycles detected

**Output:** `qa_cycle_check.log`

---

### Task 5.2: Orphan Detection
**Goal:** Ensure every node belongs to proper containers.

**Steps:**
- [ ] Write `check_orphans.py` that verifies:
  - Every word belongs to exactly one phrase
  - Every phrase belongs to exactly one clause
  - Every clause belongs to exactly one sentence
  - Every sentence belongs to exactly one verse
  - No container nodes are empty
- [ ] Report any orphan nodes
- [ ] Report any empty containers

**Verification:**
- Script runs on entire dataset
- No orphans or empty containers

**Output:** `qa_orphan_check.log`

---

### Task 5.3: Feature Completeness Check
**Goal:** Verify all nodes have required features.

**Steps:**
- [ ] Write `check_features.py` that:
  - For each otype, lists required features (from schema_map.json)
  - Checks every node of that type has all required features
  - Allows for documented optional features
- [ ] Report nodes with missing required features

**Verification:**
- All required features present
- Missing features are documented as intentional

**Output:** `qa_feature_check.log`

---

### Task 5.4: Statistical Comparison with N1904
**Goal:** Verify TR dataset has similar statistics to N1904.

**Steps:**
- [ ] Write `compare_stats.py` that generates:
  - Word count comparison (TR vs N1904)
  - Clause count comparison
  - Phrase count comparison
  - Average clause length comparison
  - Part-of-speech distribution comparison
  - Function distribution comparison
- [ ] Flag any significant deviations (>10% difference)
- [ ] Document expected differences (TR additions)

**Verification:**
- Statistics are comparable
- Differences are explained by TR variants

**Output:** `qa_stats_comparison.md`

---

### Task 5.5: High-Profile Variant Spot Check
**Goal:** Manually verify syntax of theologically significant passages.

**Steps:**
- [ ] For each high-profile variant, verify in TF:
  - **1 John 5:7-8 (Comma Johanneum)**
    - [ ] Three witnesses correctly structured
    - [ ] Apposition relationships correct
  - **Acts 8:37 (Eunuch's confession)**
    - [ ] "I believe" clause structure
    - [ ] "Son of God" as predicate
  - **1 Timothy 3:16 (θεός/ὅς)**
    - [ ] Subject of relative clause
    - [ ] Verb agreement
  - **Mark 16:9-20 (Longer ending)**
    - [ ] All 12 verses have valid syntax
    - [ ] Participle chains correct
  - **John 7:53-8:11 (Pericope Adulterae)**
    - [ ] All verses present
    - [ ] Accusation scene syntax
  - **Revelation 22:19 (βιβλίου variant)**
    - [ ] "Book of life" phrase structure
- [ ] Document any issues found and corrections made

**Verification:**
- Each variant passage is manually reviewed
- Syntax is grammatically correct

**Output:** `qa_variant_reviews/` directory with per-passage reports

---

### Task 5.6: Query Functionality Test
**Goal:** Verify standard TF queries work correctly.

**Steps:**
- [ ] Write `test_queries.py` with common query patterns:
  ```python
  # Find all infinitives
  query = '''
  phrase function=Complement
    word sp=verb mood=infinitive
  '''

  # Find all genitive absolutes
  query = '''
  clause type=genabs
    phrase
      word sp=verb mood=participle case=genitive
  '''

  # Find all subject-verb-object patterns
  query = '''
  clause
    phrase function=Subject
    phrase function=Predicate
      word sp=verb
    phrase function=Object
  '''
  ```
- [ ] Verify queries return expected results
- [ ] Compare query results with N1904 where applicable

**Verification:**
- All test queries execute without error
- Results are linguistically plausible

**Output:** `qa_query_tests.log`

---

### Task 5.7: Edge Case Testing
**Goal:** Test unusual grammatical constructions.

**Steps:**
- [ ] Test handling of:
  - [ ] Extremely long sentences
  - [ ] Deeply nested clauses
  - [ ] Rare constructions (optative mood, dual number)
  - [ ] Hapax legomena (words appearing only once)
  - [ ] Verses with many variants
- [ ] Document any edge cases that need attention

**Verification:**
- No crashes on edge cases
- Edge cases have valid syntax

**Output:** `qa_edge_cases.log`

---

### Task 5.8: Final Build Verification
**Goal:** Complete end-to-end verification of dataset.

**Steps:**
- [ ] Fresh load of TF dataset from scratch
- [ ] Run all QA scripts in sequence
- [ ] Generate final QA report summarizing:
  - Total nodes by type
  - Total features
  - Tests passed/failed
  - Known issues
  - Recommendations

**Verification:**
- All tests pass
- Dataset is ready for use

**Output:** `QA_FINAL_REPORT.md`

---

## Deliverables Checklist

- [ ] `check_cycles.py` - Cycle detection script
- [ ] `check_orphans.py` - Orphan detection script
- [ ] `check_features.py` - Feature completeness script
- [ ] `compare_stats.py` - Statistics comparison
- [ ] `test_queries.py` - Query functionality tests
- [ ] `qa_variant_reviews/` - Manual review documentation
- [ ] `QA_FINAL_REPORT.md` - Final quality assurance report

---

## Exit Criteria

Phase 5 is complete when:
1. No cycles in syntax trees
2. No orphan nodes
3. All required features present
4. Statistics are comparable to N1904
5. High-profile variants are verified
6. Standard queries work correctly
7. Final QA report is generated

---

## Files Created This Phase

```
/home/michael/bible/tr/
├── scripts/
│   ├── check_cycles.py
│   ├── check_orphans.py
│   ├── check_features.py
│   ├── compare_stats.py
│   └── test_queries.py
├── qa_results/
│   ├── qa_cycle_check.log
│   ├── qa_orphan_check.log
│   ├── qa_feature_check.log
│   ├── qa_stats_comparison.md
│   ├── qa_query_tests.log
│   ├── qa_edge_cases.log
│   └── qa_variant_reviews/
│       ├── 1john_5_7-8.md
│       ├── acts_8_37.md
│       └── ...
├── reports/
│   └── QA_FINAL_REPORT.md
```
