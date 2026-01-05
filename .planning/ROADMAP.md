# Project Roadmap: TR Text-Fabric Dataset

## Overview

This roadmap breaks the "Graft and Patch" strategy into 5 sequential phases. Each phase must complete before the next begins (except where noted).

---

## Phase 1: Reconnaissance & Schema Extraction
**Folder:** `.planning/phases/01-reconnaissance/`

**Objective:** Map exactly which features exist in N1904 so we can replicate the structure.

**Key Deliverables:**
- `schema_map.json` - Complete N1904 feature definition
- Standardized TR DataFrame with unique word identifiers
- Understanding of N1904 embedded clause handling

**Entry Criteria:** Project started
**Exit Criteria:** Schema fully documented, TR data loaded and indexed

---

## Phase 2: The Great Alignment
**Folder:** `.planning/phases/02-alignment/`

**Objective:** Map N1904 syntax trees onto TR text where words are identical (~98%).

**Key Deliverables:**
- Verse-level alignment script
- ID translation table (`N1904_NodeID` -> `TR_NodeID`)
- Transplanted syntax data for matching words
- "Gaps" file listing all unaligned TR text

**Entry Criteria:** Phase 1 complete (schema + data ready)
**Exit Criteria:** All matching text has transplanted syntax; gaps isolated

---

## Phase 3: Delta Patching (AI Processing)
**Folder:** `.planning/phases/03-delta-patching/`

**Objective:** Generate syntax trees for TR-exclusive readings using NLP/LLM.

**Key Deliverables:**
- Stanza-generated dependency trees for gaps
- UD-to-N1904 label mapping ("Rosetta Stone")
- LLM-reviewed high-profile verses

**Entry Criteria:** Phase 2 complete (gaps identified)
**Exit Criteria:** All gaps have valid syntax annotations

---

## Phase 4: Compilation & Build
**Folder:** `.planning/phases/04-compilation/`

**Objective:** Serialize the combined data into valid Text-Fabric files.

**Key Deliverables:**
- Merged DataFrame (Phase 2 + Phase 3 data)
- Generated `.tf` files for all features
- Configured otype hierarchy

**Entry Criteria:** Phase 3 complete (all syntax data ready)
**Exit Criteria:** Valid TF dataset that loads without errors

---

## Phase 5: Quality Assurance
**Folder:** `.planning/phases/05-qa/`

**Objective:** Verify dataset integrity and correctness.

**Key Deliverables:**
- Cycle check results (no circular dependencies)
- Orphan check results (no dangling nodes)
- Spot-check verification of major variants

**Entry Criteria:** Phase 4 complete (TF dataset built)
**Exit Criteria:** All checks pass; dataset ready for use

---

## Phase Dependency Graph

```
Phase 1 (Reconnaissance)
    │
    ▼
Phase 2 (Alignment)
    │
    ▼
Phase 3 (Delta Patching)
    │
    ▼
Phase 4 (Compilation)
    │
    ▼
Phase 5 (QA)
```

All phases are strictly sequential due to data dependencies.

---

## Current Status

| Phase | Status | Progress |
|-------|--------|----------|
| Phase 1: Reconnaissance | Not Started | 0% |
| Phase 2: Alignment | Not Started | 0% |
| Phase 3: Delta Patching | Not Started | 0% |
| Phase 4: Compilation | Not Started | 0% |
| Phase 5: QA | Not Started | 0% |
