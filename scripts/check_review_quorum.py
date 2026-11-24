"""Check the consistency of a coordinator's review quorum receipt."""

import argparse
import json
import re
from pathlib import Path


GATES = {"plan", "design", "fix-plan", "code"}
VERDICTS = {"agree", "partial", "disagree"}
SEVERITIES = {"info", "low", "medium", "high", "critical"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def identifier(value):
    return isinstance(value, str) and bool(value) and value == value.strip()


def check(data):
    require(isinstance(data, dict), "expected a receipt object")
    mode = data.get("mode")
    gate = data.get("gate")
    digest = data.get("artifact_sha256")
    authors = data.get("authors")
    require(mode in ("codex", "lineage"), "unknown quorum mode")
    require(identifier(gate) and gate in GATES, "unknown gate")
    require(type(data.get("round")) is int and 1 <= data["round"] <= 3, "invalid review round")
    require(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest), "invalid artifact SHA-256")
    require(isinstance(authors, list) and authors and all(map(identifier, authors)), "author IDs missing")
    reviewers = data.get("reviewers")
    votes = data.get("votes")
    require(isinstance(reviewers, list) and len(reviewers) == 3, "expected three reviewer seats")
    require(isinstance(votes, list), "expected a vote list")

    roster = {}
    for reviewer in reviewers:
        require(isinstance(reviewer, dict), "invalid reviewer record")
        require(all(identifier(reviewer.get(key)) for key in ("id", "model", "surface", "family")),
                "reviewer identity, model, surface or family missing")
        run_id = reviewer["id"]
        require(run_id not in authors and run_id not in roster, "reviewer must be distinct from author and peers")
        require(reviewer.get("verified") is True, f"unverified review model for {run_id}")
        roster[run_id] = reviewer

    surfaces = {r["surface"] for r in roster.values()}
    families = {r["family"].casefold() for r in roster.values()}
    models = {r["model"].casefold() for r in roster.values()}
    require(len(models) == 3, "review seats must use distinct model IDs")
    if mode == "codex":
        require(surfaces == {"codex"} and families == {"openai"}, "expected native Codex reviewers")
    else:
        family_by_surface = {r["surface"]: r["family"].casefold() for r in roster.values()}
        require(surfaces == {"codex", "gemini", "opencode"} and len(families) == 3
                and family_by_surface.get("codex") == "openai" and family_by_surface.get("gemini") == "google",
                "expected Codex, Gemini and OpenCode on three distinct underlying families")

    seen, blockers = set(), []
    for vote in votes:
        require(isinstance(vote, dict), "invalid vote record")
        reviewer = vote.get("reviewer")
        verdict = vote.get("verdict")
        require(identifier(reviewer) and reviewer in roster and reviewer not in seen, "unknown or duplicate voter")
        require(vote.get("gate") == gate and vote.get("artifact_sha256") == digest, "vote is for another gate or artifact")
        require(type(vote.get("round")) is int and vote["round"] == data["round"], "vote is for another round")
        require(identifier(verdict) and verdict in VERDICTS, "invalid vote verdict")
        findings = vote.get("findings")
        require(isinstance(findings, list), "expected a findings list")
        levels = set()
        for finding in findings:
            require(isinstance(finding, dict), "invalid finding")
            severity = finding.get("severity")
            require(identifier(severity) and severity in SEVERITIES, "invalid finding severity")
            require(isinstance(finding.get("evidence"), str) and finding["evidence"].strip(), "finding evidence missing")
            levels.add(severity)
        if verdict == "disagree" or levels & {"critical", "high"} or (verdict == "partial" and "medium" in levels):
            blockers.append(reviewer)
        seen.add(reviewer)

    missing = sorted(roster.keys() - seen)
    decision = "disagree" if blockers else "incomplete" if missing else "agree"
    return {"decision": decision, "blockers": sorted(blockers), "missing": missing}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.receipt.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
        result = check(data)
    except (OSError, ValueError) as error:
        result = {"decision": "incomplete", "error": str(error)}
    print(json.dumps(result, sort_keys=True))
    return {"agree": 0, "disagree": 1, "incomplete": 2}[result["decision"]]


if __name__ == "__main__":
    raise SystemExit(main())
