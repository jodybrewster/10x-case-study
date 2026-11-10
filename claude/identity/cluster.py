"""Constrained union-find over auto links."""


class Clusters:
    def __init__(self, recs):
        self.parent = {r.uid: r.uid for r in recs}
        self.attrs = {}
        for r in recs:
            self.attrs[r.uid] = {
                "bd": {r.bd} if r.bd else set(),
                "first": {r.canon_first},
                "ehr": 1 if r.system == "ehr" else 0,
            }
        self.tree = {r.uid: [] for r in recs}   # accepted edges (neighbor, score)

    def find(self, u):
        while self.parent[u] != u:
            self.parent[u] = self.parent[self.parent[u]]
            u = self.parent[u]
        return u

    def conflict(self, a, b):
        """Reason string if merging would break a cluster rule, else ''."""
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return ""
        A, B = self.attrs[ra], self.attrs[rb]
        if len(A["bd"] | B["bd"]) > 1:
            return "cluster_conflict_birthdate"
        if len(A["first"] | B["first"]) > 1:
            return "cluster_conflict_first_name"
        if A["ehr"] + B["ehr"] > 1:
            return "cluster_conflict_two_ehr_charts"
        return ""

    def union(self, a, b, score):
        ra, rb = self.find(a), self.find(b)
        A, B = self.attrs[ra], self.attrs[rb]
        self.parent[rb] = ra
        A["bd"] |= B["bd"]; A["first"] |= B["first"]; A["ehr"] += B["ehr"]
        self.tree[a].append((b, score))
        self.tree[b].append((a, score))
