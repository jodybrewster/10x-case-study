import csv
import os
import sys
import tempfile
import unittest
from collections import defaultdict

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
DATA = os.path.join(HERE, "..", "..", "data")

from identity import normalize as N  # noqa: E402
from identity import pipeline  # noqa: E402
from identity.records import Record  # noqa: E402
from identity.scoring import AUTO, score_pair  # noqa: E402


def rec(system, rid, first, last, bd=None, emails=(), phone="", hh="", weak=False):
    em = {N.norm_email(e) for e in emails}
    return Record(system, rid, first, last, N.canon_first(first), N.norm_name(last), N.norm_birthdate(bd),
                  em, {N.email_dot_key(e) for e in em}, N.norm_phone(phone), "", hh, weak)


class Normalise(unittest.TestCase):
    def test_email(self):
        self.assertEqual(N.norm_email("  Jane.Doe@Example.COM "), "jane.doe@example.com")
        self.assertEqual(N.email_dot_key("j.ane.doe@example.com"), "janedoe@example.com")
        self.assertNotEqual(N.email_dot_key("jane+x@example.com"), N.email_dot_key("jane@example.com"))
        self.assertEqual(N.email_plus_base("jane+x@example.com"), "jane@example.com")
        self.assertEqual(N.email_plus_base("jane@example.com"), "")
        self.assertEqual(N.norm_email("nope"), "")

    def test_phone_formats(self):
        for p in ("(906) 783-4829", "906.783.4829", "+1 906 783 4829", "9067834829", "906-783-4829"):
            self.assertEqual(N.norm_phone(p), "9067834829")
        self.assertEqual(N.norm_phone("12345"), "")
        # another country code must not collide with a US number that shares its last ten digits
        self.assertNotEqual(N.norm_phone("+44 906 783 4829"), N.norm_phone("906 783 4829"))

    def test_birthdate_unknown(self):
        self.assertIsNone(N.norm_birthdate(""))
        self.assertIsNone(N.norm_birthdate("1920-01-01"))
        self.assertEqual(N.norm_birthdate("1975-07-11"), "1975-07-11")

    def test_nicknames(self):
        for nick, full in (("Tony", "Anthony"), ("Rick", "Richard"), ("Bob", "Robert"), ("Jess", "Jessica"),
                           ("Bill", "William"), ("Matt", "Matthew"), ("Joe", "Joseph"), ("Drew", "Andrew"),
                           ("Jen", "Jennifer")):
            self.assertEqual(N.canon_first(nick), N.canon_first(full))
        self.assertNotEqual(N.canon_first("Thomas"), N.canon_first("Elizabeth"))

    def test_household_key(self):
        self.assertEqual(N.household_key("273 Oak St", "33157-1234"), "273|33157")


class Scoring(unittest.TestCase):
    def test_birthdate_veto_even_when_everything_else_agrees(self):
        a = rec("crm", "a", "Kevin", "Adams", "1970-08-08", ["k@x.com"], "9684624459", "1|2")
        b = rec("portal", "b", "Kevin", "Adams", "1998-10-26", ["k@x.com"], "9684624459", "1|2")
        s, why, veto = score_pair(a, b)
        self.assertTrue(veto)
        self.assertEqual(s, 0.0)

    def test_transposed_birthdate_is_still_a_veto(self):
        a = rec("crm", "a", "Ann", "Lee", "1970-08-12")
        b = rec("portal", "b", "Ann", "Lee", "1970-12-08")
        self.assertTrue(score_pair(a, b)[2])

    def test_nickname_agreement_links(self):
        a = rec("crm", "a", "Tony", "Rossi", "1980-02-02", ["t@x.com"])
        b = rec("portal", "b", "Anthony", "Rossi", "1980-02-02", ["t@x.com"])
        self.assertGreaterEqual(score_pair(a, b)[0], AUTO)

    def test_relatives_do_not_merge(self):
        a = rec("crm", "a", "Elizabeth", "Hall", None, ["h@x.com"], "5551112222", "9|1")
        b = rec("crm", "b", "Thomas", "Hall", None, ["h@x.com"], "5551112222", "9|1")
        s, why, veto = score_pair(a, b)
        self.assertLess(s, 0.6)
        self.assertIn("first_name_differs", why)

    def test_household_alone_is_not_identity(self):
        a = rec("ecommerce", "a", "Sam", "Fox", None, ["a@x.com"], "5551112222", "9|1")
        b = rec("ecommerce", "b", "Sam", "Fox", None, ["b@x.com"], "5551112222", "9|1")
        self.assertLess(score_pair(a, b)[0], AUTO)


class RealData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.res = pipeline.run(DATA)
        cls.key = {(s, i): k for s, i, k, c in cls.res["rows"]}

    def test_row_count_and_every_record_once(self):
        rows = self.res["rows"]
        self.assertEqual(len(rows), 1994)
        self.assertEqual(len({(s, i) for s, i, _, _ in rows}), 1994)
        counts = defaultdict(int)
        for s, _, _, _ in rows:
            counts[s] += 1
        self.assertEqual(dict(counts), {"ecommerce": 533, "crm": 689, "portal": 433, "ehr": 339})

    def test_confidence_range(self):
        for _, _, _, c in self.res["rows"]:
            self.assertTrue(0 <= c <= 1)

    def test_no_cluster_with_two_known_birthdates(self):
        by = self.res["by"]
        for m in self.res["clusters"].values():
            self.assertLessEqual(len({by[u].bd for u in m if by[u].bd}), 1)

    def test_no_cluster_with_two_first_names(self):
        by = self.res["by"]
        for m in self.res["clusters"].values():
            self.assertEqual(len({by[u].canon_first for u in m}), 1)

    def test_no_cluster_with_two_ehr_charts(self):
        for m in self.res["clusters"].values():
            self.assertLessEqual(sum(1 for u in m if u[0] == "ehr"), 1)

    def test_lab_result_links_hold(self):
        # every registration with a matching lab result sits in the same cluster as its chart
        det = [x for x in self.res["auto"] if "lab_result_kit_barcode" in x[3]]
        self.assertGreater(len(det), 300)
        for a, b, _, _ in det:
            self.assertEqual(self.key[a], self.key[b])

    def test_spot_checks(self):
        k = self.key
        tyler = [("ecommerce", "7000326"), ("ecommerce", "7000327"), ("ecommerce", "7000328"),
                 ("crm", "001A000213"), ("crm", "001A000497"), ("portal", "R000285"),
                 ("portal", "R000286"), ("ehr", "CH050205")]
        self.assertEqual(len({k[u] for u in tyler}), 1)
        self.assertNotEqual(k[("crm", "001A000417")], k[("crm", "001A000652")])
        self.assertNotEqual(k[("crm", "001A000551")], k[("crm", "001A000686")])

    def test_review_queue_has_no_pii(self):
        with tempfile.TemporaryDirectory() as d:
            pipeline.write(self.res, d)
            with open(os.path.join(d, "review_queue.csv")) as f:
                header = next(csv.reader(f))
                rows = list(csv.reader(f))
            self.assertEqual(header, pipeline.REVIEW_COLUMNS)
            pairs = [(r[0], r[1]) for r in rows]
            self.assertEqual(len(pairs), len(set(pairs)), "one review item per pair of persons")
            self.assertTrue(all(a != b for a, b in pairs))

    def test_plus_tag_is_review_only(self):
        from identity.scoring import REVIEW_ONLY
        a = rec("portal", "R1", "Jane", "Example", "1980-01-01", ["jane@example.com"], "9065550101")
        b = rec("portal", "R2", "Jane", "Example", "1980-01-01", ["jane+kit@example.com"], "9065550101")
        b.email_bases = {N.email_plus_base("jane+kit@example.com")}
        _, why, veto = score_pair(a, b)
        self.assertFalse(veto)
        self.assertIn(REVIEW_ONLY, why)

    def test_label_sample_is_random_and_repeatable(self):
        from identity import sample
        with tempfile.TemporaryDirectory() as d:
            p1, p2 = os.path.join(d, "a.csv"), os.path.join(d, "b.csv")
            sample.write_sample(self.res, p1)
            sample.write_sample(self.res, p2)
            with open(p1, "rb") as f1, open(p2, "rb") as f2:
                self.assertEqual(f1.read(), f2.read())
            with open(p1) as f:
                rows = list(csv.DictReader(f))
            auto = [r for r in rows if r["bucket"] == "auto"]
            self.assertEqual(len(auto), 100)
            self.assertEqual(int(auto[0]["bucket_population"]), len(self.res["auto"]))

    def test_deterministic(self):
        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            pipeline.write(pipeline.run(DATA), d1)
            pipeline.write(pipeline.run(DATA), d2)
            for name in ("identities.csv", "review_queue.csv"):
                with open(os.path.join(d1, name), "rb") as f1, open(os.path.join(d2, name), "rb") as f2:
                    self.assertEqual(f1.read(), f2.read())


if __name__ == "__main__":
    unittest.main()
