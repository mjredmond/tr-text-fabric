# Phase 4: Compilation & Build

## Objective
Serialize the combined data into valid Text-Fabric files that load correctly.

## Context
Text-Fabric uses a specific file format (`.tf` files) for each feature. We must:
1. Merge the transplanted data (Phase 2) with patched data (Phase 3)
2. Generate correct node structures (otypes hierarchy)
3. Write each feature to its own `.tf` file
4. Configure the metadata correctly

---

## Tasks

### Task 4.1: Data Merge
**Goal:** Combine transplanted syntax and gap syntax into unified dataset.

**Steps:**
- [ ] Load `tr_transplanted.parquet` (Phase 2)
- [ ] Load `gap_syntax.parquet` (Phase 3)
- [ ] Write `merge_data.py` that:
  - Combines both DataFrames
  - Ensures no duplicate word IDs
  - Validates all words from original TR are present
  - Sorts by canonical order (book, chapter, verse, word_rank)
- [ ] Export as `tr_complete.parquet`

**Verification:**
```python
complete = pd.read_parquet('tr_complete.parquet')
original = pd.read_parquet('tr_words.parquet')
assert len(complete) == len(original)
assert set(complete['word_id']) == set(original['word_id'])
```

**Output:** `tr_complete.parquet`

---

### Task 4.2: Container Node Generation
**Goal:** Create clause, phrase, and sentence container nodes.

**Steps:**
- [ ] Write `generate_containers.py` that:
  - Groups words by clause_id to create clause nodes
  - Groups words by phrase_id to create phrase nodes
  - Creates sentence nodes (using verse boundaries or explicit markers)
  - Assigns unique node IDs to all container nodes
- [ ] Ensure container hierarchy is valid:
  - Every word belongs to exactly one phrase
  - Every phrase belongs to exactly one clause
  - Every clause belongs to exactly one sentence
- [ ] Export container nodes as `tr_containers.parquet`

**Verification:**
```python
containers = pd.read_parquet('tr_containers.parquet')
words = pd.read_parquet('tr_complete.parquet')
# Every word's clause_id should be in containers
assert words['clause_id'].isin(containers[containers['otype']=='clause']['node_id']).all()
```

**Output:** `tr_containers.parquet`

---

### Task 4.3: OTypes Hierarchy Configuration
**Goal:** Define the node type hierarchy for Text-Fabric.

**Steps:**
- [ ] Create otypes configuration matching N1904:
  ```python
  otypes = [
      ('book', 'slot'),      # book contains slots
      ('chapter', 'slot'),   # chapter contains slots
      ('verse', 'slot'),     # verse contains slots
      ('sentence', 'slot'),  # sentence contains slots
      ('clause', 'slot'),    # clause contains slots
      ('phrase', 'slot'),    # phrase contains slots
      ('word', 'slot'),      # word IS a slot (terminal)
  ]
  ```
- [ ] Document slot range for each container node
- [ ] Validate hierarchy matches N1904 exactly

**Verification:**
- Load N1904 and compare otypes
- Ensure same container relationships

**Output:** `otypes_config.py` module

---

### Task 4.4: Feature File Generation
**Goal:** Write all node features to `.tf` files.

**Steps:**
- [ ] Write `generate_tf.py` using Text-Fabric's `Fabric.save()` API
- [ ] Generate word features:
  - `word.tf` - Surface form
  - `lemma.tf` - Dictionary form
  - `sp.tf` - Part of speech
  - `gn.tf` - Gender
  - `nu.tf` - Number
  - `ps.tf` - Person
  - `case.tf` - Grammatical case
  - `tense.tf` - Verb tense
  - `voice.tf` - Verb voice
  - `mood.tf` - Verb mood
  - `gloss.tf` - English gloss (if available)
- [ ] Generate syntax features:
  - `function.tf` - Syntactic function
  - `role.tf` - Semantic role
  - `type.tf` - Clause/phrase type
- [ ] Generate metadata:
  - `otype.tf` - Node type assignments
  - `oslots.tf` - Slot containment

**Verification:**
- Each `.tf` file is valid and parseable
- Feature count matches expected node count

**Output:** `tf_output/` directory with all `.tf` files

---

### Task 4.5: Edge Feature Generation
**Goal:** Write parent-child relationships as edge features.

**Steps:**
- [ ] Write `generate_edges.py` that:
  - Creates `parent.tf` edge feature
  - Each entry: `from_node -> to_node`
  - Handles multi-parent cases if present
- [ ] Validate all parent references point to valid nodes

**Verification:**
```python
# Load and verify no dangling references
edges = load_edge_file('parent.tf')
all_nodes = get_all_node_ids()
for from_node, to_node in edges:
    assert from_node in all_nodes
    assert to_node in all_nodes
```

**Output:** Edge `.tf` files in `tf_output/`

---

### Task 4.6: Metadata Configuration
**Goal:** Create TF metadata files.

**Steps:**
- [ ] Create `otext.tf` with:
  - Section structure (book/chapter/verse)
  - Text format templates
  - Language setting (grc)
- [ ] Create `__desc__.tf` with dataset description
- [ ] Add version and provenance metadata

**Verification:**
- Metadata files are valid TF format

**Output:** Metadata files in `tf_output/`

---

### Task 4.7: Build Verification
**Goal:** Verify the dataset loads in Text-Fabric.

**Steps:**
- [ ] Write `verify_build.py` that:
  - Loads the generated TF dataset
  - Runs basic queries to verify structure
  - Checks random sample of verses for correctness
- [ ] Test queries:
  ```python
  from tf.fabric import Fabric
  TF = Fabric(locations=['tf_output'])
  api = TF.load('')

  # Test basic load
  print(f"Words: {len(api.F.otype.s('word'))}")
  print(f"Clauses: {len(api.F.otype.s('clause'))}")

  # Test navigation
  for word in api.F.otype.s('word')[:10]:
      print(api.T.text(word))
  ```

**Verification:**
- Dataset loads without errors
- Queries return expected results

**Output:** `verify_build.py`, verification log

---

## Deliverables Checklist

- [ ] `tr_complete.parquet` - Merged complete data
- [ ] `tr_containers.parquet` - Container nodes
- [ ] `tf_output/` - Complete TF dataset
  - All word feature files
  - All syntax feature files
  - Edge feature files
  - Metadata files
- [ ] Verification that dataset loads correctly

---

## Exit Criteria

Phase 4 is complete when:
1. All data is merged into single source
2. All `.tf` files are generated
3. Dataset loads in Text-Fabric without errors
4. Basic queries work correctly

---

## Files Created This Phase

```
/home/michael/bible/tr/
├── scripts/
│   ├── merge_data.py
│   ├── generate_containers.py
│   ├── otypes_config.py
│   ├── generate_tf.py
│   ├── generate_edges.py
│   └── verify_build.py
├── data/
│   ├── tr_complete.parquet
│   └── tr_containers.parquet
├── tf_output/
│   ├── word.tf
│   ├── lemma.tf
│   ├── sp.tf
│   ├── function.tf
│   ├── role.tf
│   ├── parent.tf
│   ├── otype.tf
│   ├── oslots.tf
│   ├── otext.tf
│   └── __desc__.tf
```
