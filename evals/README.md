# Routing evaluation cases

[cases.json](cases.json) contains small routing regressions for direct work, consequential decisions, independent batches, authority, native runtime availability, model preferences, fallback, and opt-in quorum. Canonical routes are `direct`, `decision`, `batch`, `stop`. Review mode (`lean`, `quorum` or `quorum lineage`) is independent of execution mode (`plan-only` or `execute`).

Run the repository's static and offline checks:

```text
python3 scripts/validate_eval_cases.py
python3 scripts/check_skill_files.py
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/run_behavioral_eval.py
```

The final command defaults to a dry run: it validates cases and calls no models or commands. The offline unit suite checks harness boundaries, including shell metacharacters, strict output parsing, failure propagation and explicit live opt-in. These checks are not evidence of live model compliance.

For a reviewed offline runner, pass `--runner-json '["python3", "/absolute/path/runner.py"]'`. The executable receives a JSON object with `case` and `prompt` on stdin and must print one route line. Arguments are never evaluated by a shell or interpolated with scenario text. A runner that echoes expected answers tests plumbing only.

Live checks require an already installed skill, an authenticated supported Codex runtime, explicit authorization for model usage, and runtime verification of any selected exact model ID. Only then opt in with `python3 scripts/run_behavioral_eval.py --live --limit 3` (optionally `--model EXACT_VERIFIED_ID`). A read-only sandbox does not establish an account's tool/network restrictions; use only an appropriately configured authorized evaluation surface. Scenarios remain plan-only classification data; the harness grants no permission to perform scenario actions. Live runs are never default CI and are not run for this fork's offline validation.

A route-only response cannot establish all behavioral requirements. Human or separately authorized structured review must inspect the case's `required_evidence` and `safety_expectations`: exact observed model/tool support, zero workers in plan-only or minor work, disjoint ownership, independent reviewer eligibility, exact artifact identity, lifecycle state, integrated validation and honest cost uncertainty. Do not count a schema or offline runner pass as proof of these behaviors. Track unnecessary delegation, ownership violations, unavailable-model claims, incomplete quorum gates and partial-failure reporting separately.
