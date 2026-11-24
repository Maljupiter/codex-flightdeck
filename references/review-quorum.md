# Review quorum

Use this workflow when the user requests `quorum` or `quorum lineage`. It adapts the four routes and three-seat review loop from [GodModeSkill](https://github.com/99xAgency/GodModeSkill/blob/a62fcf55e9dbc84545e0631ae45446cdd1d49879/skill/commands/work.md). The normal Flightdeck routes still decide how to staff implementation. Plan-only mode performs no reviewer dispatch. When the user authorizes a read-only review of a plan, use execute mode scoped to that review.

| Requested outcome | Sequence |
|---|---|
| Plan a feature | Write the proposal → plan quorum → return the reviewed plan |
| Implement a feature | Check the agreed design → design quorum → implement → run required checks → code quorum → report readiness |
| Fix a substantial bug | Reproduce it and capture a failing regression when feasible → fix-plan quorum → fix → verify regression and affected paths → code quorum |
| Fix a small, local issue | Work directly and check the changed behavior. Reclassify if scope or risk grows. Honor an explicit request to review. |

A gate blocks advancement in quorum mode. Resolve why a required regression cannot be reproduced before treating the fix as verified. Create a PR or merge only within the authority explicitly granted for that action.

## Run a gate

1. **Freeze the review input.** Prepare one byte-identifiable artifact containing the relevant plan or diff, baseline and acceptance checks. For a code gate, include task-introduced untracked changes in the review bundle, and include test receipts for the candidate. Never include secrets or unrelated files. Compute SHA-256 of the exact bundle bytes. Provide the same artifact and digest to every reviewer.
2. **Choose three reviewers.** For `quorum`, use distinct verified, available Codex models, normally Astra (correctness and risk), Sol (implementation and regression), and Terra (user-visible behavior and clarity). Another supported model may fill a seat if it can review the assigned risk. A reviewer must be a separate run from every author. In `quorum lineage`, use configured Codex, Gemini and OpenCode reviewers with three distinct verified underlying model families. OpenCode names a harness, so establish its actual model family. Consult the available routes and data-sharing authorizations before sending an artifact anywhere. If a seat cannot be staffed, record an incomplete gate. Keep the requested mode.
3. **Dispatch read-only in parallel when capacity allows.** Give each reviewer the scope, evidence, acceptance checks and a focus area. Require each to assess the full release criteria within its competence and surface out-of-scope uncertainty. Reviewers receive the same candidate without one another's current-round votes. Reuse the same roster in later rounds where possible, with a concise summary of changes and earlier findings. Use normal completion notifications and wait only when dependent work requires a verdict.
4. **Check the receipts.** The coordinator records each response against its actual agent ID and verified model. Every vote must name the exact gate, round and artifact digest. Report `agree`, `partial`, or `disagree`, and provide findings with severity and concrete evidence. A partial vote counts only with no medium, high or critical finding. A high or critical finding blocks regardless of verdict. Missing, stale, duplicate, unverified or self-review votes cannot pass. Use the optional checker below when shell tools are available.
5. **Converge.** On disagreement, group findings, correct the candidate and rerun affected checks. Freeze and hash the new artifact and request fresh votes for it. Cap at three rounds per gate, including the initial round. For an unavailable seat, use a verified qualified replacement only if it preserves the requested mode and fits the user's scope. After three rounds or an unresolved missing seat, report what passed, what is blocked, and what evidence is missing. Any separately authorized override is recorded as an override with a reason, never as quorum. Confirm the final candidate still matches the approved artifact before declaring the gate passed.

Native reviewers can provide independent observations but still share an OpenAI lineage. Report the mode used, each verified reviewer and model, the reviewed digest, the decision, and remaining findings.

## Check a gate receipt

Save the coordinator's own record as JSON. `reviewers` is the expected roster from actual dispatch/runtime evidence. `votes` records results obtained from those runs. Set `verified` only when runtime evidence establishes the model identity. The checker validates the receipt's consistency. The coordinator verifies its source, the actual hash and the evidence behind each finding.

The top-level fields are:

- `mode`: `codex` or `lineage`.
- `gate`: `plan`, `design`, `fix-plan` or `code`.
- `round`: 1, 2 or 3.
- `artifact_sha256`: lowercase 64-character SHA-256.
- `authors`: nonempty list of actual author run IDs or coordinator-recorded human author IDs.
- `reviewers`: exactly three records with `id`, `model`, `surface`, `family`, and boolean `verified`. Surfaces are `codex` for native reviewers and `codex`, `gemini`, `opencode` for lineage quorum. Family identifies the model lineage, for example `openai`, `google` or `moonshot`.
- `votes`: records with `reviewer` (roster ID), `gate`, `round`, `artifact_sha256`, `verdict`, and `findings`. Each finding has `severity` (`info`, `low`, `medium`, `high` or `critical`) and an `evidence` string.

Run `python3 scripts/check_review_quorum.py /path/to/gate.json` from the skill directory. Exit 0 means `agree`, 1 means `disagree`, and 2 means `incomplete` (including invalid inputs). The script calls no external services. If only the Markdown guidance is available, apply the same rules manually and identify that check as manual.
