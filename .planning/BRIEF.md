# Project Brief: Textus Receptus Text-Fabric Dataset

## Problem Statement

The Textus Receptus (TR) is a foundational Greek New Testament text family that underlies the King James Version and remains significant for biblical scholarship. However, there is no Text-Fabric dataset for the TR that includes full syntactic markup (syntax trees, clause boundaries, phrase functions) comparable to the existing N1904 (Patriarchal Text) dataset.

Creating syntax annotations from scratch would require thousands of hours of expert linguistic annotation. This project provides an efficient path to a complete syntactic dataset.

## Solution: "Graft and Patch" Strategy

Since the TR and N1904 share approximately 98% textual identity (both being Byzantine text-type), we can:

1. **Graft (98%):** Programmatically transplant existing N1904 syntax trees onto matching TR text
2. **Patch (2%):** Use AI (Stanza NLP + LLM review) to generate syntax for TR-exclusive readings

## Success Criteria

- [ ] Complete Text-Fabric dataset loadable via `tf.fabric`
- [ ] All N1904 node types replicated: `sentence`, `clause`, `phrase`, `word`
- [ ] All syntactic features present: `role`, `function`, `parent`, `sp`, `voice`, etc.
- [ ] No orphan nodes (every word in a phrase, every phrase in a clause, etc.)
- [ ] No circular dependencies in syntax trees
- [ ] Verified accuracy on high-profile TR variants (1 John 5:7, Acts 8:37, Rev 22:19)

## Constraints

- **Schema Fidelity:** Must exactly match N1904's feature schema for tool compatibility
- **ID Integrity:** Node ID pointers must be correctly re-indexed after transplant
- **Theological Neutrality:** Syntax annotations should reflect grammatical structure, not interpretive choices

## Technical Environment

- Python 3.10+
- WSL/Linux (recommended for Text-Fabric performance)
- Key libraries: `text-fabric`, `pandas`, `stanza`, `difflib`

## Data Sources

| Source | Purpose |
|--------|---------|
| N1904 Text-Fabric Dataset | Schema master + syntax donor |
| Robinson-Pierpont 2018 (or Scrivener 1894) | TR source text with morphology |

## Stakeholder

Solo developer project for biblical scholarship research.

## Reference

See `plan.md` for the original strategic overview.
