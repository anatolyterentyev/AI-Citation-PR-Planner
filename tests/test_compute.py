import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import compute  # noqa: E402

FIXTURE = os.path.join(HERE, "fixtures", "run.json")


class DomainTests(unittest.TestCase):
    def test_registrable_domain(self):
        self.assertEqual(compute.registrable_domain("https://www.travel.example.co.uk/a?b=1"), "example.co.uk")
        self.assertEqual(compute.registrable_domain("https://blog.acmeguide.test/posts/x"), "acmeguide.test")
        self.assertEqual(compute.registrable_domain("medium.com/some-blog/post"), "medium.com")
        self.assertEqual(compute.registrable_domain(""), "")

    def test_clean_url_strips_tracking(self):
        self.assertEqual(compute.clean_url("https://a.test/x/?utm_source=openai"), "https://a.test/x/")
        self.assertEqual(compute.clean_url("https://a.test/x?id=3&utm_source=openai"), "https://a.test/x?id=3")

    def test_clean_url_merges_www_and_case(self):
        self.assertEqual(compute.clean_url("https://WWW.Travelblog.test/Best/"), "https://travelblog.test/Best/")

    def test_parse_count(self):
        self.assertEqual(compute.parse_count("12.31K"), 12310)
        self.assertEqual(compute.parse_count("1.6M"), 1600000)
        self.assertEqual(compute.parse_count(28), 28)
        self.assertIsNone(compute.parse_count("N/A"))


class ComputeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = compute.load(FIXTURE)
        cls.plan = compute.cmd_compute(cls.data)
        cls.rows = {r["domain"]: r for r in cls.plan["pr"]}

    def test_cited_drops_stores_own_site_and_competitors(self):
        cited = compute.cmd_cited(self.data)
        domains = [d["domain"] for d in cited["domains"]]
        self.assertEqual(domains[0], "travelblog.test")  # cited by two engines
        for dropped in ("apple.com", "acmeguide.test", "rivalapp.test"):
            self.assertNotIn(dropped, domains)
        self.assertEqual(cited["unresolved_links"], 2)  # redirect link + UNRESOLVED

    def test_citation_proof_and_priority(self):
        row = self.rows["travelblog.test"]
        self.assertEqual(row["source"], "cited")
        self.assertEqual(row["engines_citing"], 2)
        self.assertEqual(row["citation_count"], 2)
        self.assertEqual({c["label"] for c in row["citations"]}, {"Claude", "Gemini"})
        self.assertEqual(row["trust_avg"], 65.0)
        self.assertEqual(row["priority"], 73)  # 0.6*65 + 15*2 + 2*2

    def test_missing_trust_is_never_substituted(self):
        row = self.rows["bigmag-fixture.co.uk"]
        self.assertIsNone(row["trust"]["gemini"])
        self.assertEqual(row["trust_avg"], 80.0)  # mean of the scores actually given
        self.assertIn("Nofollow link", row["flags"])

    def test_flags_inflated_traffic_and_notes(self):
        flags = self.rows["linkfarm.test"]["flags"]
        self.assertTrue(any(f.startswith("Inflated traffic") for f in flags))
        self.assertIn("Do not buy", flags)

    def test_catalog_rows_have_no_citations(self):
        row = self.rows["catalogsite.test"]
        self.assertEqual(row["source"], "catalog")
        self.assertEqual(row["citations"], [])
        self.assertEqual(row["priority"], 33)  # 0.6*55
        self.assertEqual(row["added"], "last_month")

    def test_link_insertions_and_not_available(self):
        li = self.plan["li"]
        self.assertEqual(li[0]["article_url"], "https://travelblog.test/best-museum-apps/")
        self.assertEqual(li[0]["engines_citing"], 2)
        self.assertEqual(li[0]["suggested_anchor"], "Acme Guide audio app")
        self.assertNotIn("catalogsite.test", [r["domain"] for r in li])
        self.assertEqual([r["domain"] for r in self.plan["na"]], ["onlycited.test"])

    def test_summary(self):
        s = self.plan["summary"]
        self.assertEqual(s["answers"], 4)
        self.assertEqual(s["prompts"], 2)
        self.assertEqual(s["product_mentioned"], {"claude": 1, "gemini": 0})
        self.assertEqual(s["available_on_collaborator"], 3)
        self.assertEqual(s["catalog_candidates"], 1)

    def test_cli_writes_plan_and_data_js(self):
        with tempfile.TemporaryDirectory() as out:
            subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "compute.py"), "compute", FIXTURE,
                            "--out", out], check=True, capture_output=True)
            with open(os.path.join(out, "data.js"), encoding="utf-8") as handle:
                text = handle.read()
            self.assertTrue(text.startswith("window.PLAN = "))
            plan = json.loads(text[len("window.PLAN = "):].rstrip().rstrip(";"))
            self.assertEqual(plan["pr"][0]["domain"], "travelblog.test")


if __name__ == "__main__":
    unittest.main()
