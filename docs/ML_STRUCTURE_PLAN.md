# Machine Learning Plan for Hierarchical Structure Generation

This document outlines the plan to use ML (fine-tuned Ancient Greek BERT) for generating syntactic structure in TR-only content.

## Overview

### Why ML?

| Approach | Pros | Cons |
|----------|------|------|
| Rule-based (N1904 patterns) | Consistent with N1904, interpretable | Limited to seen patterns |
| Stanza NLP | General-purpose, no training needed | Different annotation scheme |
| **ML (fine-tuned BERT)** | Learns complex patterns, probability scores, N1904-consistent | Requires training, GPU |

### Proposed Hybrid Pipeline

```
For TR-only content:
┌─────────────────────────────────────────────────────┐
│ 1. N1904 Direct Transplant (100% aligned verses)    │ → confidence=1.0
├─────────────────────────────────────────────────────┤
│ 2. N1904 Pattern Lookup (Strong's, POS bigrams)     │ → confidence=0.75-0.9
├─────────────────────────────────────────────────────┤
│ 3. ML Model Prediction (fine-tuned BERT)            │ → confidence=model_prob
├─────────────────────────────────────────────────────┤
│ 4. Stanza Fallback (if ML confidence < threshold)   │ → confidence=0.5-0.7
└─────────────────────────────────────────────────────┘
```

---

## Pre-trained Models

### Available Ancient Greek BERT Models

| Model | Source | Training Data | Best For |
|-------|--------|---------------|----------|
| [pranaydeeps/Ancient-Greek-BERT](https://huggingface.co/pranaydeeps/Ancient-Greek-BERT) | HuggingFace | First1KGreek, Perseus, PROIEL, Gorman | **Recommended** - >90% on POS/morph |
| [Jacobo/aristoBERTo](https://huggingface.co/Jacobo/aristoBERTo) | HuggingFace | GreekBERT + Ancient texts | Alternative |
| [altsoph/bert-base-ancientgreek-uncased](https://huggingface.co/altsoph/bert-base-ancientgreek-uncased) | HuggingFace | GreekBERT + Ancient corpora | Style/authorship |
| [UGARIT/grc-ner-bert](https://huggingface.co/UGARIT/grc-ner-bert) | HuggingFace | NER datasets (2024) | Named entities |

### Recommended: pranaydeeps/Ancient-Greek-BERT

- Initialized from Greek BERT, fine-tuned on ancient texts
- Trained on PROIEL and Gorman treebanks (similar to N1904's source)
- State-of-the-art on POS tagging (>90% accuracy)
- Perplexity: 4.8 on held-out test

---

## Training Data: N1904

### Available Data

| Type | Count | Notes |
|------|-------|-------|
| Words | 137,779 | All annotated |
| Phrases (typed) | 20,768 | NP, PP, AdjP, AdvP, VP |
| Phrases (untyped) | 48,239 | Have structure but no type label |
| Clauses | 42,506 | Sentence-level structure |
| Sentences | 8,010 | Top-level boundaries |

### Class Distribution (Phrase Types)

| Type | Count | Percentage |
|------|-------|------------|
| NP (Noun Phrase) | 10,935 | 52.7% |
| PP (Prepositional Phrase) | 9,609 | 46.3% |
| AdvP (Adverb Phrase) | 154 | 0.7% |
| AdjP (Adjective Phrase) | 60 | 0.3% |
| VP (Verb Phrase) | 10 | 0.05% |

**Note**: Imbalanced classes - will need class weighting or oversampling for AdjP/AdvP/VP.

### Data Split Strategy

```
N1904 Data (137,779 words)
├── Training:   80% (~110K words) - for model training
├── Validation: 10% (~14K words)  - for hyperparameter tuning
└── Test:       10% (~14K words)  - for final evaluation

Split by book to avoid verse-level leakage:
- Train: Matthew-Galatians
- Val:   Ephesians-Hebrews
- Test:  James-Revelation
```

---

## Task Formulation

### Task 1: Phrase Boundary Detection (BIO Tagging)

**Input**: Sequence of words
**Output**: BIO tags for each word

```
Input:  [ἐν]   [ἀρχῇ]  [ἦν] [ὁ]    [λόγος]
Output: [B-PP] [I-PP]  [O]  [B-NP] [I-NP]

Tags:
- B-{type}: Beginning of phrase
- I-{type}: Inside phrase
- O: Outside (not in typed phrase)
```

**Model Architecture**:
```
Ancient-Greek-BERT
       ↓
   [CLS] [w1] [w2] [w3] ... [SEP]
       ↓
Linear Classification Layer (per token)
       ↓
   [tag1] [tag2] [tag3] ...
```

### Task 2: Phrase Type Classification (Optional, Simpler)

**Input**: Pre-identified phrase span
**Output**: Phrase type (NP/PP/AdjP/AdvP/VP)

```
Input:  [CLS] ὁ λόγος [SEP]
Output: NP (0.92), PP (0.05), AdjP (0.02), AdvP (0.01)
```

### Task 3: Clause Boundary Detection (Separate Model)

```
Input:  [ἐν] [ἀρχῇ] [ἦν] [ὁ] [λόγος] [,] [καὶ] ...
Output: [I]  [I]    [I]  [I] [I]     [O] [B]   ...
```

### Recommended: Start with Task 1

BIO tagging is well-established and handles both boundary detection and type classification in one model.

---

## Implementation Plan

### Phase 1: Data Preparation

#### Script: `scripts/ml/prepare_training_data.py`

```python
def convert_n1904_to_bio():
    """Convert N1904 structure to BIO format for training."""

    training_data = []

    for verse in n1904_verses:
        words = get_verse_words(verse)
        labels = []

        for word in words:
            phrase = get_containing_phrase(word)
            if phrase and phrase.typ:
                if is_phrase_start(word, phrase):
                    labels.append(f"B-{phrase.typ}")
                else:
                    labels.append(f"I-{phrase.typ}")
            else:
                labels.append("O")

        training_data.append({
            "tokens": [w.text for w in words],
            "labels": labels,
            "verse_ref": verse.ref
        })

    return training_data
```

**Output Format** (JSON Lines):
```json
{"tokens": ["ἐν", "ἀρχῇ", "ἦν", "ὁ", "λόγος"], "labels": ["B-PP", "I-PP", "O", "B-NP", "I-NP"]}
{"tokens": ["καὶ", "ὁ", "λόγος", "ἦν"], "labels": ["O", "B-NP", "I-NP", "O"]}
```

### Phase 2: Model Fine-tuning

#### Script: `scripts/ml/train_phrase_tagger.py`

```python
from transformers import (
    AutoModelForTokenClassification,
    AutoTokenizer,
    TrainingArguments,
    Trainer
)

def train_phrase_tagger():
    # Load pre-trained Ancient Greek BERT
    model_name = "pranaydeeps/Ancient-Greek-BERT"
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # Label mapping
    label_list = ["O", "B-NP", "I-NP", "B-PP", "I-PP",
                  "B-AdjP", "I-AdjP", "B-AdvP", "I-AdvP", "B-VP", "I-VP"]

    model = AutoModelForTokenClassification.from_pretrained(
        model_name,
        num_labels=len(label_list)
    )

    # Training arguments
    training_args = TrainingArguments(
        output_dir="./models/phrase_tagger",
        num_train_epochs=10,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        warmup_steps=500,
        weight_decay=0.01,
        logging_dir="./logs",
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
    )

    # Class weights for imbalanced data
    class_weights = compute_class_weights(train_dataset)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
    )

    trainer.train()
    trainer.save_model("./models/phrase_tagger_final")
```

### Phase 3: Evaluation

#### Script: `scripts/ml/evaluate_model.py`

**Metrics to Track**:

| Metric | Description |
|--------|-------------|
| Token Accuracy | % of tokens with correct BIO tag |
| Phrase F1 | F1 score for complete phrase extraction |
| Per-class F1 | F1 for each phrase type (NP, PP, etc.) |
| Boundary Precision | % of predicted boundaries that are correct |
| Boundary Recall | % of true boundaries that are detected |

**Expected Performance** (based on similar tasks):

| Metric | Target | Notes |
|--------|--------|-------|
| Token Accuracy | >92% | Based on BERT POS performance |
| NP F1 | >85% | Most common class |
| PP F1 | >85% | Second most common |
| AdjP/AdvP F1 | >70% | Rare classes, harder |
| Overall Phrase F1 | >80% | Weighted average |

### Phase 4: Integration

#### Script: `scripts/phase4/p4_08c_ml_structure.py`

```python
from transformers import pipeline

class MLPhrasePredictor:
    def __init__(self, model_path="./models/phrase_tagger_final"):
        self.pipe = pipeline(
            "token-classification",
            model=model_path,
            aggregation_strategy="simple"
        )

    def predict_structure(self, words: list[str]) -> list[dict]:
        """
        Predict phrase structure for a sequence of words.

        Returns list of phrases with:
        - type: NP/PP/etc.
        - start: start word index
        - end: end word index
        - confidence: model probability
        """
        results = self.pipe(" ".join(words))

        phrases = []
        for entity in results:
            phrases.append({
                "type": entity["entity_group"],
                "start": entity["start"],
                "end": entity["end"],
                "confidence": entity["score"],
                "source": "ml"
            })

        return phrases

    def predict_with_threshold(self, words, threshold=0.7):
        """Only return predictions above confidence threshold."""
        phrases = self.predict_structure(words)
        return [p for p in phrases if p["confidence"] >= threshold]
```

---

## Confidence Score Mapping

| Model Probability | Mapped Confidence | Action |
|-------------------|-------------------|--------|
| ≥ 0.90 | 0.85-0.90 | Use ML prediction |
| 0.80-0.90 | 0.75-0.85 | Use ML, flag for review |
| 0.70-0.80 | 0.65-0.75 | Use ML if N1904 pattern agrees |
| < 0.70 | - | Fall back to N1904 patterns or Stanza |

---

## Training Requirements

### Hardware

| Option | Time Estimate | Notes |
|--------|---------------|-------|
| GPU (NVIDIA T4/V100) | 2-4 hours | Recommended |
| CPU only | 24-48 hours | Slow but works |
| Google Colab (free) | 2-4 hours | Good option if no local GPU |

### Dependencies

```bash
pip install transformers torch datasets seqeval accelerate
```

### Storage

| Item | Size |
|------|------|
| Pre-trained model | ~500 MB |
| Training data | ~10 MB |
| Fine-tuned model | ~500 MB |
| Total | ~1 GB |

---

## Integration with Existing Plan

### Updated Pipeline Priority

```
For TR-only segments:

1. N1904 Structure Extension (if partially aligned)
   → confidence from alignment coverage

2. N1904 Pattern Lookup
   - Strong's number → phrase type
   - POS bigram patterns
   → confidence 0.75-0.90

3. ML Model Prediction (NEW)
   - Fine-tuned Ancient-Greek-BERT
   - BIO tagging for phrase boundaries
   → confidence from model probability

4. Hybrid Decision
   - If ML and N1904 patterns agree → boost confidence
   - If disagree → use higher confidence one
   - If both low → flag for review

5. Stanza Fallback (last resort)
   → confidence 0.5-0.7
```

### Scripts to Create

| Script | Purpose |
|--------|---------|
| `scripts/ml/prepare_training_data.py` | Convert N1904 to BIO format |
| `scripts/ml/train_phrase_tagger.py` | Fine-tune BERT model |
| `scripts/ml/evaluate_model.py` | Evaluate on test set |
| `scripts/ml/export_model.py` | Export for inference |
| `scripts/phase4/p4_08c_ml_structure.py` | Integration with pipeline |

---

## Verification Plan

### Model Verification

1. **Held-out Test Set** (10% of N1904)
   - Must achieve >80% phrase F1 before deployment
   - Per-class breakdown for rare classes

2. **Cross-validation**
   - 5-fold CV on training data
   - Check for overfitting

3. **Error Analysis**
   - Confusion matrix for phrase types
   - Analysis of boundary errors
   - Check performance on long vs short phrases

### Application Verification

1. **Compare ML vs N1904 Patterns**
   - On aligned verses, compare ML predictions to actual N1904
   - Should be >85% agreement

2. **Spot-check TR-only Predictions**
   - Manual review of 100 TR-only segments
   - Check linguistic validity

3. **Confidence Calibration**
   - Verify that model probability correlates with accuracy
   - Adjust mapping if needed

---

## Timeline

| Phase | Task | Duration |
|-------|------|----------|
| 1 | Data preparation | 1 day |
| 2 | Model training | 1-2 days |
| 3 | Evaluation & tuning | 1 day |
| 4 | Integration | 1 day |
| 5 | Verification | 1 day |
| **Total** | | **5-6 days** |

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Class imbalance | Poor AdjP/AdvP performance | Class weighting, oversampling |
| Overfitting | Poor generalization to TR | Cross-validation, early stopping |
| Tokenization mismatch | Alignment issues | Careful token-word mapping |
| GPU not available | Slow training | Use Colab or CPU with patience |
| Model too confident | Overconfident wrong predictions | Temperature scaling, threshold |

---

## Success Criteria

- [ ] Model achieves >80% phrase F1 on N1904 test set
- [ ] NP and PP F1 both >85%
- [ ] >85% agreement with N1904 patterns on aligned data
- [ ] Manual review of TR-only predictions passes
- [ ] Confidence scores are well-calibrated
- [ ] Integration with pipeline works end-to-end
