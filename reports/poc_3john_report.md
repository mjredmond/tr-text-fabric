# Proof of Concept Alignment Report: 3John

## Summary

| Metric | Value |
|--------|-------|
| TR Words | 218 |
| N1904 Words | 219 |
| Aligned Words | 189 |
| TR Gaps (unmatched) | 29 |
| N1904 Gaps (unmatched) | 19 |
| **Alignment Rate** | **86.7%** |

## Verse-Level Details

| Ch:Vs | TR | N1904 | Aligned | TR Gaps | N1904 Gaps |
|-------|---:|------:|--------:|--------:|-----------:|
| 1:1 | 10 | 10 | 10 | 0 | 0 |
| 1:2 | 13 | 13 | 13 | 0 | 0 |
| 1:3 | 15 | 15 | 15 | 0 | 0 |
| 1:4 | 13 | 14 | 13 | 0 | 1 |
| 1:5 | 13 | 12 | 11 | 2 | 1 |
| 1:6 | 14 | 14 | 13 | 1 | 1 |
| 1:7 | 10 | 10 | 7 | 3 | 3 |
| 1:8 | 11 | 11 | 10 | 1 | 1 |
| 1:9 | 11 | 12 | 9 | 2 | 3 |
| 1:10 | 33 | 33 | 33 | 0 | 0 |
| 1:11 | 21 | 20 | 18 | 3 | 2 |
| 1:12 | 21 | 21 | 19 | 2 | 2 |
| 1:13 | 12 | 13 | 9 | 3 | 4 |
| 1:14 | 21 | 10 | 9 | 12 | 1 |

## Interpretation

The alignment rate of 86.7% indicates 
the feasibility of the graft-and-patch approach. Gaps represent words 
that need syntax annotation via NLP (Phase 3).

### Next Steps

1. Run full alignment on all books (p2_04)
2. Build ID translation table (p2_05)
3. Transplant syntax features (p2_06)