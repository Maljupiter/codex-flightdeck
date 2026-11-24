# Codex Flightdeck

An independent Codex skill for orchestrating work across Astra, Sol, Terra and Luna. Finish coherent tasks in the active session. Delegate when an independent outcome or a different capability improves the result.

| Model family | Typical assignment |
| --- | --- |
| Astra | Architecture, hard cross-system diagnosis and consequential review |
| Sol | End-to-end implementation, debugging and tests |
| Terra | Visual QA, screenshots, writing and supported app workflows |
| Luna | Structured extraction, focused lookups and repeatable checks |

Codex chooses among models and tools exposed by the current session. Model access and delegation options vary. See [OpenAI's model guide](https://learn.chatgpt.com/docs/models).

## Install

Clone this repository with the folder name `codex-flightdeck`. Copy `SKILL.md`, `agents/`, `references/`, `scripts/check_review_quorum.py` (inside a `scripts/` folder), and `LICENSE` into a skill directory named `codex-flightdeck`. Use `~/.agents/skills/` for a user skill or `.agents/skills/` for a project skill. Open a new Codex session if the skill has not appeared.

```sh
git clone https://github.com/Maljupiter/codex-flightdeck.git
cd codex-flightdeck
destination="$HOME/.agents/skills/codex-flightdeck"
mkdir -p "$HOME/.agents/skills"
mkdir "$destination" &&
  mkdir "$destination/scripts" &&
  cp -R SKILL.md agents references LICENSE "$destination/" &&
  cp scripts/check_review_quorum.py "$destination/scripts/"
```

## Use

- **Plan only** · “Use $codex-flightdeck in plan-only mode to route this cross-module refactor.”
- **Execute** · “Use $codex-flightdeck to implement the approved settings flow and verify it.”
- **Quorum** · “Use $codex-flightdeck in execute and quorum modes to implement this feature.” For a read-only review, say “Use $codex-flightdeck in execute mode with quorum to review this plan.”

Flightdeck keeps the upstream **direct → decision → batch → integration** architecture. It uses the decision and batch stages when the scope calls for them. See [the skill](SKILL.md) for the routing and [the execution contract](references/execution-contract.md) for handoffs and recovery.

Quorum adds three independent reviews of the same candidate, a correction loop capped at three rounds per gate, and a fresh review after any relevant change. The native mode uses three distinct OpenAI models. Request **quorum lineage** for the original Codex, Gemini and OpenCode arrangement with distinct underlying model families. It requires already configured and authorized review routes. The coordinator records a gate as incomplete when a required reviewer or its identity cannot be verified. See [review modes and receipts](references/review-quorum.md).

## Verification

```sh
python3 scripts/validate_eval_cases.py
python3 scripts/check_skill_files.py
python3 -m unittest discover -s tests
```

These offline checks cover the packaged skill files, the routing scenarios' structure and quorum receipt logic. A separate live evaluation is needed to measure routing quality and model access. See [evaluation guidance](evals/README.md).

## Credits

Forked from [JashinYang/codex-multi-model-orchestrator](https://github.com/JashinYang/codex-multi-model-orchestrator) at `70696f4`. The plan, implement, bug-fix and review-quorum workflow is adapted from [99xAgency/GodModeSkill](https://github.com/99xAgency/GodModeSkill/tree/a62fcf55e9dbc84545e0631ae45446cdd1d49879). Both upstream MIT notices are included in [LICENSE](LICENSE). Flightdeck is a community project.
