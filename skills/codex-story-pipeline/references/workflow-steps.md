# Workflow Steps

Run enabled steps sequentially through Codex worker subagents. `Run when status
is` determines where a resumed pipeline begins. After each subagent completes,
re-read the story status before evaluating the next row.

| Enabled | Step | Codex skill | Run when status is | Expected result |
|---|---|---|---|---|
| yes | Create story | `$bmad-create-story` | `backlog` | Story file exists and status is `ready-for-dev` |
| yes | Generate ATDD tests | `$bmad-testarch-atdd` | `ready-for-dev` | Red-phase acceptance tests and ATDD checklist exist |
| yes | Develop story | `$bmad-dev-story` | `ready-for-dev`, `in-progress` | Implementation complete, 0 skipped tests, 100% coverage on changed code, all tests pass; status is `review` |
| yes | Code review | `$bmad-code-review` | `review` | Review gates pass and status is `done` |
| yes | Trace coverage | `$bmad-testarch-trace` | `done` | Traceability matrix and quality-gate decision exist; no untraced AC-to-test gaps remain |

## Configuration Rules

- Reorder rows to change execution order.
- Change `yes` to `no` to disable a step.
- Use an installed Codex skill name in `Codex skill`.
- Each enabled row must be executed by a fresh Codex `worker` subagent.
- Keep expected status transitions aligned with the project's
  `sprint-status.yaml` definitions.
- Do not add Claude Code slash commands, `Task(...)`, or `yolo` arguments.
- The pipeline orchestrator enforces a Test Quality Gate after Develop story: 0 skipped tests and 100% coverage on changed code are mandatory. Skipped tests or coverage gaps halt the pipeline until resolved or explicitly overridden by the user.
