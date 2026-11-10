"""Run the whole slice: load, block, score, cluster, write."""
import csv
import hashlib
import itertools
import os
from collections import defaultdict

from . import records as R
from .cluster import Clusters
from .scoring import AUTO, REVIEW, REVIEW_ONLY, score_pair

MAX_BLOCK = 60


def person_key(uid):
    """PROTOTYPE SHORTCUT. A key derived from the smallest member record is repeatable for a
    batch run, which is what a one-command slice needs, but it is guessable from the record
    id and it changes if a lower-sorting record joins the cluster. The target design mints a
    random opaque key once, stores it and never derives it from source data."""
    h = hashlib.sha256(f"{uid[0]}:{uid[1]}".encode()).hexdigest()[:12]
    return f"P{h}"


def candidate_pairs(recs):
    blocks = defaultdict(list)
    for r in recs:
        for e in r.emails:
            blocks[("email", e)].append(r)
        for k in r.email_keys:
            blocks[("emailkey", k)].append(r)
        for k in r.email_bases | (r.emails if r.email_bases else set()):
            blocks[("emailbase", k)].append(r)
        if r.phone:
            blocks[("phone", r.phone)].append(r)
        if r.last_norm and r.zip:
            blocks[("sz", r.last_norm, r.zip)].append(r)
        if r.last_norm and r.bd:
            blocks[("sb", r.last_norm, r.bd)].append(r)
    pairs = set()
    for key, members in blocks.items():
        if len(members) < 2 or len(members) > MAX_BLOCK:
            continue
        for a, b in itertools.combinations(members, 2):
            if a.uid != b.uid:
                pairs.add(tuple(sorted((a.uid, b.uid))))
    return pairs


def run(data_dir):
    recs, det = R.load(data_dir)
    by = {r.uid: r for r in recs}
    scored = {}   # (uidA, uidB) -> (score, reasons, vetoed, deterministic)
    for a, b in candidate_pairs(recs):
        s, why, veto = score_pair(by[a], by[b])
        scored[(a, b)] = [s, why, veto, False]
    # deterministic: registration -> chart through the lab result, only if identity fields also agree
    for reg, chart, lab in det:
        ra, rc = by[reg], by[chart]
        agree = (ra.canon_first == rc.canon_first and ra.last_norm == rc.last_norm and ra.bd == rc.bd)
        key = tuple(sorted((reg, chart)))
        if agree:
            scored[key] = [1.0, ["lab_result_kit_barcode", "first_name_agree", "surname_agree", "birthdate_agree"], False, True]
        else:
            s, why, veto = score_pair(ra, rc)
            scored[key] = [min(s, REVIEW + 0.01) if not veto else 0.0, ["lab_result_identity_mismatch"] + why, veto, False]

    cl = Clusters(recs)
    auto_pairs, review, rejected = [], [], []
    order = sorted(scored.items(), key=lambda kv: (-kv[1][0], kv[0]))
    for (a, b), (s, why, veto, det_) in order:
        if veto or s < REVIEW:
            rejected.append((a, b, s, why))
            continue
        ra, rb = by[a], by[b]
        extra = []
        if ra.system == "ehr" and rb.system == "ehr":
            extra.append("two_ehr_charts_never_auto_merged")
        if REVIEW_ONLY in why and "unvalidated_rule" not in extra:
            extra.append("unvalidated_rule")
        if s >= AUTO and not extra:
            c = cl.conflict(a, b)
            if cl.find(a) == cl.find(b):
                auto_pairs.append((a, b, s, why)); continue
            if not c:
                cl.union(a, b, s)
                auto_pairs.append((a, b, s, why)); continue
            extra.append(c)
        review.append((a, b, s, why + extra))

    # review pairs whose records ended up in the same cluster need no decision
    review = [x for x in review if cl.find(x[0]) != cl.find(x[1])]

    members = defaultdict(list)
    for r in recs:
        members[cl.find(r.uid)].append(r.uid)
    anchor = {root: min(m) for root, m in members.items()}
    conf, key = {}, {}
    for root, m in members.items():
        anc = anchor[root]
        pk = person_key(anc)
        if len(m) == 1:
            conf[anc] = 1.0; key[anc] = pk; continue
        conf[anc] = max(s for _, s in cl.tree[anc])
        key[anc] = pk
        stack = [(anc, 1.0)]
        seen = {anc}
        while stack:
            u, floor = stack.pop()
            for v, s in sorted(cl.tree[u]):
                if v in seen:
                    continue
                seen.add(v)
                conf[v] = min(floor, s); key[v] = pk
                stack.append((v, conf[v]))
    rows = [(r.system, r.rid, key[r.uid], round(conf[r.uid], 4)) for r in recs]
    rows.sort(key=lambda x: (R.SYSTEMS.index(x[0]), x[1]))

    # One review item per pair of persons. A reviewer decides "are these two people one
    # person" once; the record pairs that raised the question are kept as its evidence.
    groups = defaultdict(list)
    for a, b, s, why in review:
        ka, kb = key[a], key[b]
        if ka > kb:
            a, b, ka, kb = b, a, kb, ka
        groups[(ka, kb)].append((a, b, s, why))
    review_groups = []
    for (ka, kb), items in groups.items():
        items.sort(key=lambda x: (-x[2], x[0], x[1]))
        a, b, s, _ = items[0]
        reasons = []
        for it in items:
            for code in it[3]:
                if code not in reasons:
                    reasons.append(code)
        review_groups.append({"ka": ka, "kb": kb, "a": a, "b": b, "score": s, "reasons": reasons, "items": items})
    review_groups.sort(key=lambda g: (-g["score"], g["ka"], g["kb"]))
    return {"recs": recs, "by": by, "rows": rows, "auto": auto_pairs, "review": review,
            "review_groups": review_groups, "rejected": rejected, "clusters": members, "scored": scored,
            "key": key}


REVIEW_COLUMNS = ["person_key_a", "person_key_b", "system_a", "record_id_a", "system_b", "record_id_b",
                  "score", "reason", "supporting_pairs", "supporting_records"]


def write(result, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "identities.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["system", "record_id", "person_key", "confidence"])
        w.writerows(result["rows"])
    with open(os.path.join(out_dir, "review_queue.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(REVIEW_COLUMNS)
        for g in result["review_groups"]:
            a, b = g["a"], g["b"]
            support = "|".join(f"{x[0]}:{x[1]}~{y[0]}:{y[1]}" for x, y, _, _ in g["items"])
            w.writerow([g["ka"], g["kb"], a[0], a[1], b[0], b[1], f"{g['score']:.4f}",
                        ";".join(g["reasons"]), len(g["items"]), support])


def summary(result):
    sizes = [len(m) for m in result["clusters"].values()]
    span = defaultdict(int)
    for m in result["clusters"].values():
        n = len({u[0] for u in m})
        if n >= 2:
            span[n] += 1
    return [
        f"records:            {len(result['rows'])}",
        f"persons:            {len(sizes)}",
        f"auto links:         {len(result['auto'])} record pairs at or above the provisional threshold",
        f"review items:       {len(result['review_groups'])} person pairs ({len(result['review'])} record pairs)",
        f"largest cluster:    {max(sizes)}",
        f"clusters spanning 2 systems: {span[2]}, 3 systems: {span[3]}, 4 systems: {span[4]}",
    ]
