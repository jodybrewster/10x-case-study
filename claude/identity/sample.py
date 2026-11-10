"""Write pairs for hand labelling (IDs, scores and reason codes only).

The auto bucket is a simple random sample, without replacement, of every record pair
that scored at or above the auto threshold. That is the population the precision claim
is about, so an interval computed from it is valid. The seed is fixed so the same data
gives the same sample.

The review and near-threshold buckets are also random samples of their own populations.
They describe those populations only and say nothing about auto-link precision.
"""
import csv
import random

from .scoring import REVIEW

SEED = 20261109


def _draw(items, n, rng):
    items = sorted(items, key=lambda x: (x[0], x[1]))
    return items if len(items) <= n else sorted(rng.sample(items, n), key=lambda x: (x[0], x[1]))


def write_sample(result, path, n_auto=100, n_review=30, n_rej=20, seed=SEED):
    rng = random.Random(seed)
    auto_pop = result["auto"]
    review_pop = [(g["a"], g["b"], g["score"], g["reasons"]) for g in result["review_groups"]]
    near_pop = [x for x in result["rejected"] if "birthdate_conflict" not in x[3] and 0.02 <= x[2] < REVIEW]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["bucket", "bucket_population", "system_a", "record_id_a", "system_b", "record_id_b",
                    "score", "reason", "label"])
        for bucket, pop, n in (("auto", auto_pop, n_auto), ("review", review_pop, n_review),
                               ("rejected_near_threshold", near_pop, n_rej)):
            for a, b, s, why in _draw(pop, n, rng):
                w.writerow([bucket, len(pop), a[0], a[1], b[0], b[1], f"{s:.4f}", ";".join(why), ""])
