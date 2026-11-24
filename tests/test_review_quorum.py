import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_review_quorum.py"


def receipt(mode="codex"):
    roles = [("astra", "gpt-6.2-astra", "codex", "openai"),
             ("sol", "gpt-6.1-sol", "codex", "openai"),
             ("terra", "gpt-6.1-terra", "codex", "openai")]
    if mode == "lineage":
        roles[1:] = [("gem", "gemini-fixture", "gemini", "google"),
                     ("kimi", "kimi-fixture", "opencode", "moonshot")]
    reviewers = [dict(id=i, model=m, surface=s, family=f, verified=True) for i, m, s, f in roles]
    digest = "a" * 64
    votes = [dict(reviewer=r["id"], verdict="agree", gate="code", round=1,
                  artifact_sha256=digest, findings=[]) for r in reviewers]
    return dict(authors=["author-run"], mode=mode, gate="code", round=1,
                artifact_sha256=digest, reviewers=reviewers, votes=votes)


class QuorumTest(unittest.TestCase):
    def check(self, data, status, decision):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "receipt.json"
            path.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")
            p = subprocess.run([sys.executable, str(SCRIPT), str(path)], check=False,
                               text=True, capture_output=True)
        self.assertEqual(p.returncode, status, p.stderr or p.stdout)
        result = json.loads(p.stdout)
        self.assertEqual(result["decision"], decision)
        return result

    def test_native_and_lineage_can_pass(self):
        for mode in ("codex", "lineage"):
            with self.subTest(mode=mode):
                self.check(receipt(mode), 0, "agree")

    def test_same_family_does_not_satisfy_lineage(self):
        data = receipt("lineage")
        data["reviewers"][-1]["family"] = "OPENAI"
        self.check(data, 2, "incomplete")

    def test_missing_vote_is_incomplete(self):
        data = receipt()
        data["votes"].pop()
        self.assertEqual(self.check(data, 2, "incomplete")["missing"], ["terra"])

    def test_stale_or_cross_gate_vote_cannot_pass(self):
        for key, value in [("artifact_sha256", "b" * 64), ("gate", "plan"), ("round", 2)]:
            with self.subTest(key=key):
                data = receipt()
                data["votes"][-1][key] = value
                self.check(data, 2, "incomplete")

    def test_duplicate_reviewer_vote_or_author_cannot_pass(self):
        data = receipt()
        data["votes"][1] = data["votes"][0]
        self.check(data, 2, "incomplete")
        data = receipt()
        data["authors"].append("astra")
        self.check(data, 2, "incomplete")

    def test_unverified_or_duplicate_model_cannot_pass(self):
        data = receipt()
        data["reviewers"][0]["verified"] = False
        self.check(data, 2, "incomplete")
        data = receipt()
        data["reviewers"][1]["model"] = data["reviewers"][0]["model"].upper()
        self.check(data, 2, "incomplete")

    def test_severity_can_block_regardless_of_verdict(self):
        for verdict, severity, status, decision in [
            ("agree", "high", 1, "disagree"),
            ("partial", "medium", 1, "disagree"),
            ("partial", "low", 0, "agree"),
            ("disagree", "info", 1, "disagree"),
        ]:
            with self.subTest(verdict=verdict, severity=severity):
                data = receipt()
                data["votes"][0].update(verdict=verdict, findings=[dict(severity=severity, evidence="test evidence")])
                self.check(data, status, decision)

    def test_invalid_json_is_incomplete(self):
        self.check('{"mode":"codex","mode":"lineage"}', 2, "incomplete")


if __name__ == "__main__":
    unittest.main()
