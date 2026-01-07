# N1904 Feature Parity Plan

This document tracks progress toward feature parity between the TR Text-Fabric dataset and the N1904 dataset.

## Current Status

### Word-Level Features

| Feature | N1904 | TR | Status |
|---------|-------|-----|--------|
| unicode | ✓ | ✓ | Complete |
| lemma | ✓ | ✓ | Complete |
| sp | ✓ | ✓ | Complete |
| strong | ✓ | ✓ | Complete |
| morph | ✓ | ✓ | Complete |
| case | ✓ | ✓ | Complete |
| gender | ✓ | ✓ | Complete (partial coverage) |
| number | ✓ | ✓ | Complete (partial coverage) |
| person | ✓ | ✓ | Complete (partial coverage) |
| tense | ✓ | ✓ | Complete |
| voice | ✓ | ✓ | Complete |
| mood | ✓ | ✓ | Complete |
| function | ✓ | ✓ | Complete (41% coverage) |
| role | ✓ | ✓ | Complete (76% coverage) |
| gloss | ✓ | ✓ | Complete |
| translit | ✓ | ✓ | Complete |
| lemmatranslit | ✓ | ✓ | Complete |
| unaccent | ✓ | ✓ | Complete |
| after | ✓ | ✓ | Complete |
| ln | ✓ | ✓ | Complete (97% coverage) |
| bookshort | ✓ | ✓ | Complete |
| text | ✓ | ✓ | Complete |
| normalized | ✓ | ✓ | Complete |
| trailer | ✓ | ✓ | Complete |
| num | ✓ | ✓ | Complete |
| ref | ✓ | ✓ | Complete |
| id | ✓ | ✓ | Complete |
| cls | ✓ | ✓ | Complete |
| trans | ✓ | ✓ | Complete (97% coverage) |
| domain | ✓ | ✓ | Complete (90% coverage) |
| typems | ✓ | ✓ | Complete (32% - applies to nouns/pronouns) |

### Hierarchical Structure (Node Types)

| Node Type | N1904 | TR | Status |
|-----------|-------|-----|--------|
| word (w) | ✓ | ✓ | Complete |
| verse | ✓ | ✓ | Complete |
| chapter | ✓ | ✓ | Complete |
| book | ✓ | ✓ | Complete |
| clause | ✓ | ✗ | TODO - Option B/C |
| phrase | ✓ | ✗ | TODO - Option B/C |
| sentence | ✓ | ✗ | TODO - Option B/C |
| group | ✓ | ✗ | TODO - Option B/C |
| subphrase | ✓ | ✗ | TODO - Option B/C |
| wg | ✓ | ✗ | TODO - Option B/C |

---

## Phase 1: Easy Word-Level Features

**Goal**: Add remaining word-level features that can be computed algorithmically.

### Features to Add

1. **bookshort** - Abbreviated book name
   - Source: Existing `book` column (already abbreviated)
   - Transform: Direct copy

2. **text** - Surface word form
   - Source: `unicode` feature
   - Transform: Direct copy (alias)

3. **normalized** - Unicode-normalized form
   - Source: `unicode` feature
   - Transform: Apply NFC normalization

4. **trailer** - Material after word
   - Source: `after` feature
   - Transform: Direct copy (alias for compatibility)

5. **num** - Word position in verse
   - Source: `word_rank` column
   - Transform: Direct copy

6. **ref** - Reference string
   - Format: `{bookshort} {chapter}:{verse}!{num}`
   - Example: `MAT 1:1!1`

7. **id** - Unique word identifier
   - Format: `n{book_num:02d}{chapter:03d}{verse:03d}{num:03d}`
   - Example: `n40001001001` (Matthew 1:1 word 1)

8. **cls** - Word class
   - Source: `sp` feature
   - Transform: Map sp values to cls values (noun, verb, adj, etc.)

### Implementation

Script: `scripts/phase4/p4_01e_add_compat_features.py`

---

## Phase 2: Hard Word-Level Features (Lookup-Based)

**Goal**: Add features that require N1904 lookup tables.

### Features to Add

1. **trans** - Contextual English translation
   - Different from `gloss` - includes articles, prepositions in context
   - Source: Build lookup from N1904 (lemma, strong, context) -> trans
   - Coverage: Expected ~89% (aligned words only)

2. **domain** - Semantic domain codes
   - Format: Space-separated codes like `033005` or `010002 033003`
   - Source: Build lookup from N1904
   - Coverage: Expected ~89%

3. **typems** - Morphological subtype
   - Values: common, proper, ordinal, cardinal, etc.
   - Source: Build lookup from N1904 or derive from morph codes
   - Coverage: Expected ~89%

### Implementation

Script: `scripts/phase4/p4_01f_add_lookup_features.py`

---

## Phase 3: Hierarchical Structure

**Goal**: Add clause, phrase, sentence, and word-group nodes with their features.

### Option B: 100%-Aligned Verses Only

**Approach**: Only create syntactic structure for verses where ALL words align with N1904.

**Pros**:
- High confidence in structure accuracy
- No heuristic guesswork
- Clear provenance

**Cons**:
- Partial coverage (~60-70% of verses estimated)
- TR-only content remains flat
- Inconsistent dataset structure

**Implementation Steps**:

1. Identify verses with 100% word alignment
2. For each aligned verse:
   - Copy clause/phrase/wg structure from N1904
   - Remap node IDs to TR node space
   - Remap word slots to TR slots
3. Add `structure_source` feature to indicate provenance
4. Leave non-aligned verses without syntactic structure

### Option C: Full Structure with Heuristics

**Approach**: Attempt to adapt N1904 structures even with partial alignment.

**Pros**:
- More complete coverage
- All verses have some structure

**Cons**:
- Risk of incorrect structures
- Complex heuristics needed
- Harder to validate

**Implementation Steps**:

1. For 100%-aligned verses: Same as Option B
2. For partially-aligned verses:
   - Copy structure nodes that span only aligned words
   - For structure nodes with mixed alignment:
     - Option C1: Extend to include TR-only words (risky)
     - Option C2: Create partial structures, mark as incomplete
     - Option C3: Use NLP to generate structure for TR-only segments
3. Add confidence scores to structure nodes
4. Add `structure_source` feature (n1904/heuristic/nlp)

### Structure Features to Add

For clause/phrase/wg nodes:
- `clausetype` - Type of clause
- `cltype` - Clause type code
- `rela` - Relation to parent
- `typ` - Phrase type
- `rule` - Syntactic rule applied
- `junction` - Coordination type
- `domain` - Discourse domain

### Estimated Effort

| Option | Complexity | Coverage | Risk |
|--------|------------|----------|------|
| B | Medium | 60-70% | Low |
| C | High | 85-95% | Medium-High |

---

## Implementation Order

1. ✅ Phase 1a: translit, lemmatranslit, unaccent, after, ln (DONE)
2. ✅ Phase 1b: bookshort, text, normalized, trailer, num, ref, id, cls (DONE)
3. ✅ Phase 2: trans, domain, typems (DONE - lookup-based)
4. ⬜ Phase 3: Hierarchical structure (Option B or C)

---

## Progress Tracking

- [x] translit - 100%
- [x] lemmatranslit - 100%
- [x] unaccent - 100%
- [x] after - 100%
- [x] ln - 97%
- [x] bookshort - 100%
- [x] text - 100%
- [x] normalized - 100%
- [x] trailer - 100%
- [x] num - 100%
- [x] ref - 100%
- [x] id - 100%
- [x] cls - 100%
- [x] trans - 97%
- [x] domain - 90%
- [x] typems - 32%
- [ ] Hierarchical structure
