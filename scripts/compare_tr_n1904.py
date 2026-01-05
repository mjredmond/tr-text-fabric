#!/usr/bin/env python3
"""Compare TR dataset with N1904 to validate correctness."""
import sys
from pathlib import Path

# Get project root (parent of scripts directory)
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent

sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from scripts.utils.config import load_config

# Load config to get paths
config = load_config()
intermediate_dir = Path(config["paths"]["data"]["intermediate"])

# Load TR data
tr_path = intermediate_dir / "tr_complete.parquet"
tr_df = pd.read_parquet(tr_path)

# Load N1904 data
n1904_path = intermediate_dir / "n1904_words.parquet"
n1904_df = pd.read_parquet(n1904_path)

print("=" * 70)
print("TR vs N1904 COMPARISON TEST")
print("=" * 70)

# 1. Overall word counts
print("\n1. OVERALL WORD COUNTS")
print("-" * 40)
print(f"   TR words:    {len(tr_df):,}")
print(f"   N1904 words: {len(n1904_df):,}")
print(f"   Difference:  {len(tr_df) - len(n1904_df):+,}")

# 2. Book-level comparison
print("\n2. BOOK-LEVEL WORD COUNTS (significant differences only)")
print("-" * 40)

# Map TR book codes to N1904 names
book_map = {
    "MAT": "Matthew", "MAR": "Mark", "LUK": "Luke", "JHN": "John",
    "ACT": "Acts", "ROM": "Romans",
    "1CO": "I_Corinthians", "2CO": "II_Corinthians",
    "GAL": "Galatians", "EPH": "Ephesians", "PHP": "Philippians",
    "COL": "Colossians", "1TH": "I_Thessalonians", "2TH": "II_Thessalonians",
    "1TI": "I_Timothy", "2TI": "II_Timothy", "TIT": "Titus", "PHM": "Philemon",
    "HEB": "Hebrews", "JAS": "James",
    "1PE": "I_Peter", "2PE": "II_Peter",
    "1JN": "I_John", "2JN": "II_John", "3JN": "III_John",
    "JUD": "Jude", "REV": "Revelation",
}

print(f"   {'Book':<8} {'TR':>8} {'N1904':>8} {'Diff':>8}")
print(f"   {'-'*8} {'-'*8} {'-'*8} {'-'*8}")

total_diff = 0
for tr_code, n1904_name in sorted(book_map.items()):
    tr_count = len(tr_df[tr_df["book"] == tr_code])
    n1904_count = len(n1904_df[n1904_df["book"] == n1904_name])
    diff = tr_count - n1904_count
    total_diff += diff
    if abs(diff) > 10:  # Only show significant differences
        print(f"   {tr_code:<8} {tr_count:>8,} {n1904_count:>8,} {diff:>+8}")

print(f"   {'TOTAL':<8} {len(tr_df):>8,} {len(n1904_df):>8,} {total_diff:>+8}")

# 3. Verse-level comparison for a sample verse
print("\n3. VERSE COMPARISON: JOHN 3:16")
print("-" * 40)

tr_jn316 = tr_df[(tr_df["book"] == "JHN") & (tr_df["chapter"] == 3) & (tr_df["verse"] == 16)]
n1904_jn316 = n1904_df[(n1904_df["book"] == "John") & (n1904_df["chapter"] == 3) & (n1904_df["verse"] == 16)]

print(f"   TR ({len(tr_jn316)} words):")
print(f"   {' '.join(tr_jn316['word'].tolist())}")
print()
print(f"   N1904 ({len(n1904_jn316)} words):")
print(f"   {' '.join(n1904_jn316['word'].tolist())}")

# 4. Check syntax transplant - verify matching lemmas
print("\n4. SYNTAX TRANSPLANT VALIDATION")
print("-" * 40)

# For words sourced from N1904, check if lemmas match
tr_from_n1904 = tr_df[tr_df["source"] == "n1904"].copy()
print(f"   Words with transplanted syntax: {len(tr_from_n1904):,}")

# Sample check: compare lemmas for Romans 8:28
print("\n   Sample: Romans 8:28")
tr_rom828 = tr_df[(tr_df["book"] == "ROM") & (tr_df["chapter"] == 8) & (tr_df["verse"] == 28)]
n1904_rom828 = n1904_df[(n1904_df["book"] == "Romans") & (n1904_df["chapter"] == 8) & (n1904_df["verse"] == 28)]

print(f"   TR words:    {' '.join(tr_rom828['word'].head(10).tolist())}...")
print(f"   TR lemmas:   {' '.join(str(l) for l in tr_rom828['lemma'].head(10).tolist())}...")
print(f"   N1904 words: {' '.join(n1904_rom828['word'].head(10).tolist())}...")
print(f"   N1904 lemmas:{' '.join(str(l) for l in n1904_rom828['lemma'].head(10).tolist())}...")

# 5. TR-only variants check
print("\n5. TR-ONLY VARIANTS (not in N1904)")
print("-" * 40)

# Acts 8:37 - should be in TR, not in N1904
tr_acts837 = tr_df[(tr_df["book"] == "ACT") & (tr_df["chapter"] == 8) & (tr_df["verse"] == 37)]
n1904_acts837 = n1904_df[(n1904_df["book"] == "Acts") & (n1904_df["chapter"] == 8) & (n1904_df["verse"] == 37)]

print(f"   Acts 8:37:")
print(f"      TR: {len(tr_acts837)} words - {' '.join(tr_acts837['word'].head(8).tolist())}...")
print(f"      N1904: {len(n1904_acts837)} words")

# 1 John 5:7-8 - Comma Johanneum
tr_1jn57 = tr_df[(tr_df["book"] == "1JN") & (tr_df["chapter"] == 5) & (tr_df["verse"].isin([7, 8]))]
n1904_1jn57 = n1904_df[(n1904_df["book"] == "I_John") & (n1904_df["chapter"] == 5) & (n1904_df["verse"].isin([7, 8]))]

print(f"\n   1 John 5:7-8 (Comma Johanneum):")
print(f"      TR: {len(tr_1jn57)} words")
print(f"      N1904: {len(n1904_1jn57)} words")
print(f"      Difference: {len(tr_1jn57) - len(n1904_1jn57):+} words (TR has extra text)")

# 6. Gloss coverage check
print("\n6. GLOSS COVERAGE (transplanted from N1904)")
print("-" * 40)
with_gloss = tr_df[tr_df["gloss"].notna() & (tr_df["gloss"] != "")]
print(f"   Words with English gloss: {len(with_gloss):,} ({len(with_gloss)/len(tr_df)*100:.1f}%)")
print(f"   Words from N1904:         {len(tr_from_n1904):,} ({len(tr_from_n1904)/len(tr_df)*100:.1f}%)")
print(f"   Match: {'YES' if len(with_gloss) == len(tr_from_n1904) else 'NO'}")

# 7. Syntactic function coverage
print("\n7. SYNTACTIC FUNCTION DISTRIBUTION")
print("-" * 40)
tr_functions = tr_df[tr_df["function"].notna()]["function"].value_counts().head(5)
print("   TR top functions:")
for func, count in tr_functions.items():
    print(f"      {func}: {count:,}")

n1904_functions = n1904_df[n1904_df["function"].notna()]["function"].value_counts().head(5)
print("   N1904 top functions:")
for func, count in n1904_functions.items():
    print(f"      {func}: {count:,}")

# 8. Random sample comparison
print("\n8. RANDOM VERSE COMPARISON")
print("-" * 40)

import random
random.seed(42)

# Pick a few random verses to compare
sample_refs = [
    ("MAT", "Matthew", 5, 3),   # Beatitudes
    ("ROM", "Romans", 3, 23),   # All have sinned
    ("PHP", "Philippians", 4, 13),  # I can do all things
    ("1CO", "I_Corinthians", 13, 4),  # Love is patient
]

for tr_book, n1904_book, ch, vs in sample_refs:
    tr_verse = tr_df[(tr_df["book"] == tr_book) & (tr_df["chapter"] == ch) & (tr_df["verse"] == vs)]
    n1904_verse = n1904_df[(n1904_df["book"] == n1904_book) & (n1904_df["chapter"] == ch) & (n1904_df["verse"] == vs)]

    tr_text = " ".join(tr_verse["word"].tolist())
    n1904_text = " ".join(n1904_verse["word"].tolist())

    match = "MATCH" if tr_text == n1904_text else "DIFF"
    print(f"   {tr_book} {ch}:{vs} - {match}")
    if tr_text != n1904_text:
        print(f"      TR:    {tr_text[:60]}...")
        print(f"      N1904: {n1904_text[:60]}...")

print("\n" + "=" * 70)
print("VALIDATION COMPLETE")
print("=" * 70)
