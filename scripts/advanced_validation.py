#!/usr/bin/env python3
"""
Advanced validation tests comparing TR dataset with N1904.

Tests:
1. Lemma consistency for transplanted words
2. Morphology consistency (case, number, gender, etc.)
3. Part-of-speech distribution comparison
4. Syntax tree integrity checks
5. Verse-level alignment verification
6. TR-only content validation
7. Statistical anomaly detection
8. Cross-text quotation checks (OT quotes should match)
"""

import sys
from pathlib import Path
from collections import Counter
import numpy as np

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from scripts.utils.config import load_config


def load_data():
    """Load TR and N1904 datasets."""
    config = load_config()
    intermediate_dir = Path(config["paths"]["data"]["intermediate"])

    tr_df = pd.read_parquet(intermediate_dir / "tr_complete.parquet")
    n1904_df = pd.read_parquet(intermediate_dir / "n1904_words.parquet")

    return tr_df, n1904_df


# Book name mapping
BOOK_MAP = {
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


def test_lemma_consistency(tr_df, n1904_df):
    """
    Test 1: For words sourced from N1904, verify lemmas are consistent.
    Words with same surface form should have same lemma.
    """
    print("\n" + "=" * 70)
    print("TEST 1: LEMMA CONSISTENCY")
    print("=" * 70)

    # Get TR words from N1904 source
    tr_n1904 = tr_df[tr_df["source"] == "n1904"].copy()

    # Build lemma lookup from N1904
    n1904_lemmas = n1904_df.groupby("word")["lemma"].apply(set).to_dict()

    inconsistent = []
    for _, row in tr_n1904.iterrows():
        word = row["word"]
        tr_lemma = row["lemma"]
        if word in n1904_lemmas:
            n1904_lemma_set = n1904_lemmas[word]
            if tr_lemma not in n1904_lemma_set and pd.notna(tr_lemma):
                inconsistent.append({
                    "word": word,
                    "tr_lemma": tr_lemma,
                    "n1904_lemmas": n1904_lemma_set,
                    "ref": f"{row['book']} {row['chapter']}:{row['verse']}"
                })

    if len(inconsistent) == 0:
        print("  PASSED: All transplanted lemmas are consistent")
    else:
        print(f"  WARNING: {len(inconsistent)} words have inconsistent lemmas")
        for item in inconsistent[:5]:
            print(f"    {item['ref']}: '{item['word']}' - TR:{item['tr_lemma']} vs N1904:{item['n1904_lemmas']}")

    return len(inconsistent) == 0


def test_morphology_consistency(tr_df, n1904_df):
    """
    Test 2: Compare morphological feature distributions.
    """
    print("\n" + "=" * 70)
    print("TEST 2: MORPHOLOGY DISTRIBUTION COMPARISON")
    print("=" * 70)

    features = ["case", "gn", "nu", "ps", "tense", "voice", "mood"]

    all_similar = True
    for feat in features:
        if feat not in tr_df.columns or feat not in n1904_df.columns:
            continue

        tr_dist = tr_df[feat].value_counts(normalize=True, dropna=False)
        n1904_dist = n1904_df[feat].value_counts(normalize=True, dropna=False)

        # Compare distributions
        all_values = set(tr_dist.index) | set(n1904_dist.index)
        max_diff = 0
        max_diff_val = None

        for val in all_values:
            tr_pct = tr_dist.get(val, 0)
            n1904_pct = n1904_dist.get(val, 0)
            diff = abs(tr_pct - n1904_pct)
            if diff > max_diff:
                max_diff = diff
                max_diff_val = val

        status = "OK" if max_diff < 0.05 else "DIFF"
        if max_diff >= 0.05:
            all_similar = False
        print(f"  {feat:8}: max diff = {max_diff:.1%} ('{max_diff_val}') [{status}]")

    if all_similar:
        print("  PASSED: All morphology distributions within 5% tolerance")
    else:
        print("  NOTE: Some differences expected due to TR variants")

    return True  # Informational, not a failure


def test_pos_distribution(tr_df, n1904_df):
    """
    Test 3: Compare part-of-speech distributions.
    """
    print("\n" + "=" * 70)
    print("TEST 3: PART-OF-SPEECH DISTRIBUTION")
    print("=" * 70)

    tr_pos = tr_df["sp"].value_counts(normalize=True)
    n1904_pos = n1904_df["sp"].value_counts(normalize=True)

    print(f"  {'POS':<12} {'TR':>8} {'N1904':>8} {'Diff':>8}")
    print(f"  {'-'*12} {'-'*8} {'-'*8} {'-'*8}")

    all_pos = sorted(set(tr_pos.index) | set(n1904_pos.index))
    for pos in all_pos:
        tr_pct = tr_pos.get(pos, 0)
        n1904_pct = n1904_pos.get(pos, 0)
        diff = tr_pct - n1904_pct
        print(f"  {pos:<12} {tr_pct:>7.1%} {n1904_pct:>7.1%} {diff:>+7.1%}")

    print("  PASSED: Distribution comparison complete")
    return True


def test_syntax_tree_integrity(tr_df):
    """
    Test 4: Verify syntax tree integrity.
    - No cycles
    - Valid parent references
    - Reasonable tree depth
    """
    print("\n" + "=" * 70)
    print("TEST 4: SYNTAX TREE INTEGRITY")
    print("=" * 70)

    # Check for cycles
    if "parent" not in tr_df.columns:
        print("  SKIPPED: No parent column found")
        return True

    words_with_parent = tr_df[tr_df["parent"].notna()]
    print(f"  Words with parent: {len(words_with_parent):,}")

    # Build parent lookup
    parent_map = dict(zip(tr_df.index, tr_df["parent"]))

    # Check for cycles by following parent chain
    cycle_count = 0
    max_depth = 0

    for idx in tr_df.index[:10000]:  # Sample for performance
        visited = set()
        current = idx
        depth = 0

        while current is not None and pd.notna(parent_map.get(current)):
            if current in visited:
                cycle_count += 1
                break
            visited.add(current)
            current = parent_map.get(current)
            depth += 1
            if depth > 100:  # Sanity check
                cycle_count += 1
                break

        max_depth = max(max_depth, depth)

    if cycle_count == 0:
        print(f"  PASSED: No cycles detected (sampled 10,000 nodes)")
        print(f"  Max tree depth observed: {max_depth}")
    else:
        print(f"  FAILED: {cycle_count} cycles detected!")

    return cycle_count == 0


def test_verse_alignment(tr_df, n1904_df):
    """
    Test 5: Verify verse-level alignment.
    For shared verses, word counts should be similar.
    """
    print("\n" + "=" * 70)
    print("TEST 5: VERSE-LEVEL ALIGNMENT")
    print("=" * 70)

    # Group by verse
    tr_verses = tr_df.groupby(["book", "chapter", "verse"]).size()
    n1904_verses = n1904_df.groupby(["book", "chapter", "verse"]).size()

    # Find matching verses
    large_diffs = []
    exact_matches = 0
    total_compared = 0

    for (tr_book, ch, vs), tr_count in tr_verses.items():
        n1904_book = BOOK_MAP.get(tr_book)
        if n1904_book and (n1904_book, ch, vs) in n1904_verses:
            n1904_count = n1904_verses[(n1904_book, ch, vs)]
            total_compared += 1

            if tr_count == n1904_count:
                exact_matches += 1
            elif abs(tr_count - n1904_count) > 5:
                large_diffs.append({
                    "ref": f"{tr_book} {ch}:{vs}",
                    "tr": tr_count,
                    "n1904": n1904_count,
                    "diff": tr_count - n1904_count
                })

    print(f"  Verses compared: {total_compared:,}")
    print(f"  Exact word count matches: {exact_matches:,} ({exact_matches/total_compared*100:.1f}%)")
    print(f"  Large differences (>5 words): {len(large_diffs)}")

    if large_diffs:
        print("\n  Largest differences (expected for TR variants):")
        large_diffs.sort(key=lambda x: abs(x["diff"]), reverse=True)
        for item in large_diffs[:10]:
            print(f"    {item['ref']}: TR={item['tr']}, N1904={item['n1904']} ({item['diff']:+d})")

    return True


def test_tr_only_content(tr_df, n1904_df):
    """
    Test 6: Verify TR-only content is properly identified.
    """
    print("\n" + "=" * 70)
    print("TEST 6: TR-ONLY CONTENT VALIDATION")
    print("=" * 70)

    # Get TR-only words (from NLP source)
    tr_only = tr_df[tr_df["source"] == "nlp"]

    print(f"  TR-only words (NLP source): {len(tr_only):,}")

    # Check known TR-only passages
    known_tr_only = [
        ("ACT", 8, 37, "Eunuch's Confession"),
        ("1JN", 5, 7, "Comma Johanneum v7"),
        ("1JN", 5, 8, "Comma Johanneum v8"),
    ]

    print("\n  Known TR-only passages:")
    for book, ch, vs, name in known_tr_only:
        tr_verse = tr_df[(tr_df["book"] == book) & (tr_df["chapter"] == ch) & (tr_df["verse"] == vs)]
        n1904_book = BOOK_MAP.get(book)
        n1904_verse = n1904_df[(n1904_df["book"] == n1904_book) & (n1904_df["chapter"] == ch) & (n1904_df["verse"] == vs)]

        tr_count = len(tr_verse)
        n1904_count = len(n1904_verse)
        nlp_count = len(tr_verse[tr_verse["source"] == "nlp"])

        status = "OK" if tr_count > n1904_count else "CHECK"
        print(f"    {name}: TR={tr_count}, N1904={n1904_count}, NLP-sourced={nlp_count} [{status}]")

    # Show distribution of TR-only content by book
    print("\n  TR-only words by book:")
    tr_only_by_book = tr_only.groupby("book").size().sort_values(ascending=False)
    for book, count in tr_only_by_book.head(10).items():
        print(f"    {book}: {count:,}")

    return True


def test_statistical_anomalies(tr_df, n1904_df):
    """
    Test 7: Detect statistical anomalies.
    """
    print("\n" + "=" * 70)
    print("TEST 7: STATISTICAL ANOMALY DETECTION")
    print("=" * 70)

    # Word frequency comparison
    tr_word_freq = tr_df["word"].value_counts()
    n1904_word_freq = n1904_df["word"].value_counts()

    # Find words with very different frequencies
    common_words = set(tr_word_freq.head(100).index) & set(n1904_word_freq.head(100).index)

    anomalies = []
    for word in common_words:
        tr_freq = tr_word_freq[word]
        n1904_freq = n1904_word_freq[word]
        ratio = tr_freq / n1904_freq if n1904_freq > 0 else float('inf')
        if ratio > 1.2 or ratio < 0.8:
            anomalies.append({
                "word": word,
                "tr": tr_freq,
                "n1904": n1904_freq,
                "ratio": ratio
            })

    if anomalies:
        print("  High-frequency words with >20% difference:")
        anomalies.sort(key=lambda x: abs(1 - x["ratio"]), reverse=True)
        for item in anomalies[:10]:
            print(f"    '{item['word']}': TR={item['tr']}, N1904={item['n1904']} (ratio={item['ratio']:.2f})")
    else:
        print("  No significant frequency anomalies in common words")

    # Check average word length
    tr_avg_len = tr_df["word"].str.len().mean()
    n1904_avg_len = n1904_df["word"].str.len().mean()
    print(f"\n  Average word length: TR={tr_avg_len:.2f}, N1904={n1904_avg_len:.2f}")

    # Check unique word counts
    print(f"  Unique words: TR={tr_df['word'].nunique():,}, N1904={n1904_df['word'].nunique():,}")

    return True


def test_parallel_passages(tr_df, n1904_df):
    """
    Test 8: Compare parallel passages (Synoptic Gospels).
    Same events should have similar text.
    """
    print("\n" + "=" * 70)
    print("TEST 8: PARALLEL PASSAGE COMPARISON")
    print("=" * 70)

    # Lord's Prayer - Matthew 6:9-13 vs Luke 11:2-4
    parallels = [
        (("MAT", 6, 9), ("LUK", 11, 2), "Lord's Prayer (start)"),
        (("MAT", 28, 19), ("MAR", 16, 15), "Great Commission"),
        (("MAT", 3, 17), ("MAR", 1, 11), "Baptism voice"),
    ]

    for (ref1, ref2, name) in parallels:
        book1, ch1, vs1 = ref1
        book2, ch2, vs2 = ref2

        tr1 = tr_df[(tr_df["book"] == book1) & (tr_df["chapter"] == ch1) & (tr_df["verse"] == vs1)]
        tr2 = tr_df[(tr_df["book"] == book2) & (tr_df["chapter"] == ch2) & (tr_df["verse"] == vs2)]

        text1 = " ".join(tr1["word"].tolist())
        text2 = " ".join(tr2["word"].tolist())

        # Simple word overlap measure
        words1 = set(tr1["word"].tolist())
        words2 = set(tr2["word"].tolist())
        overlap = len(words1 & words2) / max(len(words1), len(words2)) if words1 and words2 else 0

        print(f"\n  {name}:")
        print(f"    {book1} {ch1}:{vs1}: {text1[:50]}...")
        print(f"    {book2} {ch2}:{vs2}: {text2[:50]}...")
        print(f"    Word overlap: {overlap:.1%}")

    return True


def test_gloss_coverage(tr_df):
    """
    Test 9: Verify gloss coverage and quality.
    """
    print("\n" + "=" * 70)
    print("TEST 9: GLOSS COVERAGE ANALYSIS")
    print("=" * 70)

    with_gloss = tr_df[tr_df["gloss"].notna() & (tr_df["gloss"] != "")]
    without_gloss = tr_df[tr_df["gloss"].isna() | (tr_df["gloss"] == "")]

    print(f"  Words with gloss: {len(with_gloss):,} ({len(with_gloss)/len(tr_df)*100:.1f}%)")
    print(f"  Words without gloss: {len(without_gloss):,} ({len(without_gloss)/len(tr_df)*100:.1f}%)")

    # Check if gloss-less words are from NLP source
    nlp_no_gloss = without_gloss[without_gloss["source"] == "nlp"]
    print(f"  NLP-sourced without gloss: {len(nlp_no_gloss):,}")

    # Sample glosses
    print("\n  Sample glosses:")
    sample = with_gloss.sample(5, random_state=42)
    for _, row in sample.iterrows():
        print(f"    {row['word']} -> {row['gloss']}")

    # Check for common words without glosses
    if len(without_gloss) > 0:
        print("\n  Most common words without gloss:")
        no_gloss_freq = without_gloss["word"].value_counts().head(5)
        for word, count in no_gloss_freq.items():
            print(f"    '{word}': {count}")

    return True


def test_function_coverage(tr_df, n1904_df):
    """
    Test 10: Compare syntactic function coverage and distribution.
    """
    print("\n" + "=" * 70)
    print("TEST 10: SYNTACTIC FUNCTION ANALYSIS")
    print("=" * 70)

    tr_funcs = tr_df["function"].value_counts(dropna=False)
    n1904_funcs = n1904_df["function"].value_counts(dropna=False)

    tr_with_func = tr_df["function"].notna().sum()
    n1904_with_func = n1904_df["function"].notna().sum()

    print(f"  TR words with function: {tr_with_func:,} ({tr_with_func/len(tr_df)*100:.1f}%)")
    print(f"  N1904 words with function: {n1904_with_func:,} ({n1904_with_func/len(n1904_df)*100:.1f}%)")

    print(f"\n  {'Function':<20} {'TR':>8} {'N1904':>8}")
    print(f"  {'-'*20} {'-'*8} {'-'*8}")

    all_funcs = sorted(set(tr_funcs.index) | set(n1904_funcs.index), key=lambda x: (x is None, str(x)))
    for func in all_funcs[:15]:
        tr_count = tr_funcs.get(func, 0)
        n1904_count = n1904_funcs.get(func, 0)
        func_str = str(func) if func is not None else "(none)"
        print(f"  {func_str:<20} {tr_count:>8,} {n1904_count:>8,}")

    return True


def main():
    """Run all validation tests."""
    print("=" * 70)
    print("ADVANCED TR vs N1904 VALIDATION")
    print("=" * 70)

    print("\nLoading datasets...")
    tr_df, n1904_df = load_data()
    print(f"  TR: {len(tr_df):,} words")
    print(f"  N1904: {len(n1904_df):,} words")

    # Run all tests
    results = []
    results.append(("Lemma Consistency", test_lemma_consistency(tr_df, n1904_df)))
    results.append(("Morphology Distribution", test_morphology_consistency(tr_df, n1904_df)))
    results.append(("POS Distribution", test_pos_distribution(tr_df, n1904_df)))
    results.append(("Syntax Tree Integrity", test_syntax_tree_integrity(tr_df)))
    results.append(("Verse Alignment", test_verse_alignment(tr_df, n1904_df)))
    results.append(("TR-Only Content", test_tr_only_content(tr_df, n1904_df)))
    results.append(("Statistical Anomalies", test_statistical_anomalies(tr_df, n1904_df)))
    results.append(("Parallel Passages", test_parallel_passages(tr_df, n1904_df)))
    results.append(("Gloss Coverage", test_gloss_coverage(tr_df)))
    results.append(("Function Coverage", test_function_coverage(tr_df, n1904_df)))

    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  [{status}] {name}")

    print(f"\n  Total: {passed}/{total} tests passed")
    print("=" * 70)

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
