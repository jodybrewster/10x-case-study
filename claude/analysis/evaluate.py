"""Report the false-match rate of auto links from a hand-labelled pairs_to_label.csv.

Usage: python3 analysis/evaluate.py analysis/pairs_to_label.csv
Fill the label column with: same, different or unsure. Blank rows are skipped.

What the numbers mean. The auto bucket is a simple random sample of every record pair at
or above the auto threshold, so the Wilson interval below is a valid 95% interval for the
false-match rate in that population, provided every sampled row is labelled. Rows left
blank or marked unsure break that guarantee, so they are counted and reported. The other
two buckets are random samples of their own populations and say nothing about auto links.
"""
import csv
import math
import sys


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, (c - m) / d), min(1.0, (c + m) / d))


def main(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    by, drawn, pop = {}, {}, {}
    for r in rows:
        drawn[r["bucket"]] = drawn.get(r["bucket"], 0) + 1
        pop[r["bucket"]] = r.get("bucket_population", "?")
        lab = r["label"].strip().lower()
        if lab in ("same", "different", "unsure"):
            by.setdefault(r["bucket"], []).append(lab)
    if not by:
        print("No labels found. Fill the label column first.")
        return
    for bucket in ("auto", "review", "rejected_near_threshold"):
        labs = by.get(bucket, [])
        s, d, u = labs.count("same"), labs.count("different"), labs.count("unsure")
        n = s + d
        print(f"{bucket}: sampled {drawn.get(bucket, 0)} of {pop.get(bucket, '?')}, "
              f"labelled {len(labs)} (same {s}, different {d}, unsure {u})")
        if n == 0:
            continue
        if bucket == "auto":
            lo, hi = wilson(d, n)
            print(f"  false-match rate: {d / n:.4f} (95% interval {lo:.4f} to {hi:.4f}, n={n})")
            print(f"  precision:        {s / n:.4f}")
            missing = drawn.get(bucket, 0) - n
            if missing:
                print(f"  WARNING: {missing} sampled auto links are unlabelled or unsure. The interval assumes "
                      "a complete random sample, so resolve them before quoting it.")
            print(f"  The upper bound {hi:.4f} is the number to hold against a rollout gate, not the point estimate.")
        elif bucket == "review":
            print(f"  share that are the same person: {s / n:.3f} (what a reviewer would approve)")
        else:
            print(f"  share that are the same person: {s / n:.3f} (links missed just under the threshold)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "analysis/pairs_to_label.csv")
