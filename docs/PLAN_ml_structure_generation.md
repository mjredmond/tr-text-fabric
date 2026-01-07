# Plan: ML-Based Hierarchical Structure Generation

## Goal

Train machine learning models on N1904's full structure annotation, then apply to TR text to generate hierarchical clause and word group structures with ~85-90% accuracy.

## Current State

| Approach | Exact Boundary Match | Notes |
|----------|---------------------|-------|
| Rule-based (current) | ~50% | Flat patterns only |
| Dependency parsing | ~50% | Good recall, poor precision |
| **ML-based (proposed)** | **85-90%** | Train on N1904, apply to TR |

## Training Data

N1904 provides complete hierarchical annotation:

| Element | Count | Description |
|---------|-------|-------------|
| Verses | 7,943 | Full NT |
| Clauses | 42,506 | With clausetype labels |
| Word groups | 106,868 | With rule labels |
| Words | 137,779 | With morphology |

---

## Phase 1: Data Preparation

### 1.1 Extract N1904 Training Data

Convert N1904 structure to sequence labels:

```python
# For each verse, create labeled sequences:
# Word groups → BIO tags with rule type
# Clauses → BIO tags with clause type

Example verse: "ἐν τῷ κόσμῳ ἦν"
Word:     ἐν      τῷ      κόσμῳ    ἦν
WG-BIO:   B-PrepNp I-PrepNp I-PrepNp B-VP
CL-BIO:   B-main  I-main  I-main   I-main
```

### 1.2 Handle Nested Structure

N1904 has nested word groups. Options:

| Approach | Complexity | Accuracy |
|----------|------------|----------|
| Flatten to outermost | Low | ~80% |
| Multi-layer BIO | Medium | ~85% |
| Span-based prediction | High | ~90% |

Recommended: Start with outermost layer, add nesting in Phase 2.

### 1.3 Output Format

```json
{
  "verse_id": "John.3.16",
  "tokens": ["Οὕτως", "γὰρ", "ἠγάπησεν", ...],
  "wg_labels": ["O", "O", "B-VP", ...],
  "wg_rules": [null, null, "S-V-O", ...],
  "clause_labels": ["B-main", "I-main", "I-main", ...],
  "clause_types": ["main", "main", "main", ...]
}
```

---

## Phase 2: Model Architecture

### 2.1 Base Model Options

| Model | Size | Greek Support | Notes |
|-------|------|---------------|-------|
| multilingual-BERT | 110M | Yes | Good baseline |
| XLM-RoBERTa | 270M | Yes | Better multilingual |
| GreekBERT | 110M | Native | Best for Greek |
| Stanza embeddings | - | Ancient Greek | Already in pipeline |

Recommended: Start with Stanza embeddings (already available), upgrade to GreekBERT if needed.

### 2.2 Model Structure

```
Input: Greek tokens
   ↓
Embedding layer (Stanza/BERT)
   ↓
BiLSTM (2 layers, 256 hidden)
   ↓
┌─────────────────┬─────────────────┐
│ WG Head         │ Clause Head     │
│ (BIO + rule)    │ (BIO + type)    │
└─────────────────┴─────────────────┘
```

### 2.3 Training Configuration

```python
config = {
    "batch_size": 32,
    "learning_rate": 2e-5,
    "epochs": 10,
    "train_split": 0.9,  # 7,149 verses
    "val_split": 0.1,    # 794 verses
    "optimizer": "AdamW",
    "loss": "CrossEntropyLoss",
    "label_smoothing": 0.1
}
```

---

## Phase 3: Training Pipeline

### 3.1 New Scripts

```
scripts/phase4/
├── p4_09a_prepare_ml_training_data.py   # Extract N1904 → training format
├── p4_09b_train_structure_model.py      # Train BiLSTM model
├── p4_09c_apply_structure_model.py      # Apply to TR text
└── p4_09d_build_nested_hierarchy.py     # Convert predictions to nodes
```

### 3.2 Training Process

```python
def train_structure_model():
    # 1. Load prepared training data
    train_data = load_n1904_training_data()

    # 2. Initialize model
    model = StructureTagger(
        vocab_size=len(vocab),
        embedding_dim=256,
        hidden_dim=256,
        num_wg_labels=len(wg_labels),    # B-DetNP, I-DetNP, B-PrepNp, ...
        num_clause_labels=len(cl_labels)  # B-main, I-main, B-purpose, ...
    )

    # 3. Train
    for epoch in range(10):
        for batch in train_loader:
            wg_loss = compute_loss(model.wg_head(batch), batch.wg_labels)
            cl_loss = compute_loss(model.clause_head(batch), batch.clause_labels)
            loss = wg_loss + cl_loss
            loss.backward()
            optimizer.step()

    # 4. Save model
    torch.save(model, 'models/structure_tagger.pt')
```

### 3.3 Inference on TR

```python
def apply_to_tr():
    model = torch.load('models/structure_tagger.pt')
    tr_words = load_tr_words()

    for verse in tr_verses:
        tokens = get_verse_tokens(verse)
        wg_preds, clause_preds = model(tokens)

        # Convert BIO predictions to spans
        wg_spans = bio_to_spans(wg_preds)
        clause_spans = bio_to_spans(clause_preds)

        # Create structure nodes
        for span in wg_spans:
            create_wg_node(span.start, span.end, span.rule)
        for span in clause_spans:
            create_clause_node(span.start, span.end, span.type)
```

---

## Phase 4: Nested Hierarchy

### 4.1 Building Hierarchy from Flat Predictions

After getting flat WG predictions, build nesting:

```python
def build_hierarchy(wg_spans):
    # Sort by span size (largest first)
    sorted_spans = sorted(wg_spans, key=lambda s: s.end - s.start, reverse=True)

    # Build tree: larger spans contain smaller ones
    for span in sorted_spans:
        for other in sorted_spans:
            if span.contains(other) and span != other:
                span.add_child(other)

    return root_spans
```

### 4.2 Hierarchy Validation

Check against N1904 patterns:

```python
# Valid nestings (from N1904):
VALID_NESTINGS = {
    'PrepNp': ['DetNP', 'NP', 'NPofNP'],
    'DetNP': ['AdjP', 'NP'],
    'NPofNP': ['DetNP', 'NP'],
    'Conj-CL': ['clause', 'PrepNp', 'DetNP'],
    ...
}
```

---

## Expected Results

### Accuracy Improvement

| Metric | Current | With ML |
|--------|---------|---------|
| WG exact boundary | 50% | 85% |
| WG rule accuracy | 78% | 92% |
| Clause boundary | 44% | 88% |
| Clause type | 68% | 90% |
| Nested hierarchy | None | 80% |

### Output Counts

| Node Type | Current | With ML |
|-----------|---------|---------|
| Clauses | 18,850 | ~40,000 |
| Word groups | 37,354 | ~100,000 |
| Nesting depth | 1 (flat) | 3-5 levels |

---

## Implementation Steps

1. **Data preparation** (p4_09a)
   - Extract N1904 structure to training format
   - Create BIO label sequences
   - Split train/validation

2. **Model training** (p4_09b)
   - Implement BiLSTM tagger
   - Train on N1904 data
   - Validate accuracy

3. **TR inference** (p4_09c)
   - Apply model to TR text
   - Generate flat predictions
   - Handle TR-only variants

4. **Hierarchy building** (p4_09d)
   - Convert flat spans to nested structure
   - Validate nesting patterns
   - Integrate into TF output

5. **Pipeline integration**
   - Add steps to run_pipeline.py
   - Update README with new accuracy
   - Document model usage

---

## Dependencies

```
torch>=2.0
transformers>=4.30  # Optional, for BERT
numpy
pandas
```

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| TR variants not in N1904 | Fall back to rule-based for unknown patterns |
| Model overfitting | Use dropout, early stopping, validation set |
| Inference speed | Batch processing, GPU if available |
| Nesting errors | Validate against known patterns |

---

## Timeline Estimate

| Phase | Effort |
|-------|--------|
| Data preparation | 2-3 hours |
| Model implementation | 4-6 hours |
| Training | 1-2 hours (GPU) |
| TR inference | 1 hour |
| Hierarchy building | 2-3 hours |
| Integration & testing | 2-3 hours |
| **Total** | **~15 hours** |
