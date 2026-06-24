---
name: bmad-story-pipeline
description: Orchestrate a BMAD story from backlog through creation, ATDD, implementation, code review, and traceability by delegating each configured BMAD stage to a Codex worker subagent. Use when the user asks to run the full story pipeline, deliver a BMAD story end to end, resume a story pipeline, or invokes $bmad-story-pipeline with an optional story ID such as 3-2.
---

# BMAD Story Pipeline

Deliver one BMAD story through the configured workflow. The parent agent is the
orchestrator: it resolves the story, launches one Codex worker subagent per
BMAD stage, waits for the result, verifies artifacts, then starts the next
stage.

Invoking this skill requests subagent execution for the configured pipeline
steps.

## Resolve The Target Story

Treat the text after `$bmad-story-pipeline` as the requested story selector. It
may be an `X-Y` ID, a full story key, or a story-file path.

1. Locate sprint status in this order:
   - `_bmad-output/implementation-artifacts/sprint-status.yaml`
   - `docs/sprint/sprint-status.yaml`
2. Read the complete selected sprint-status file before choosing a story.
3. If the user supplied a selector, resolve it to the matching story key and
   story file. Do not silently select another story.
4. Otherwise select the first story in file order using this priority:
   `in-progress`, `review`, `ready-for-dev`, then `backlog`.
5. Ignore epic and retrospective entries.
6. If no eligible story exists, report that no runnable story was found and
   stop.

Record `STORY_ID`, `STORY_KEY`, `STORY_FILE`, and current status. Story IDs use
`X-Y`; story keys may include a title suffix.

## Load Workflow Configuration

Read [references/workflow-steps.md](references/workflow-steps.md) completely
before execution. Treat its ordered table as configuration. Run only enabled
steps, in order, and apply each step's `Run when status is` rule.

When resuming, skip steps that precede the current story status. Never move a
story backward merely to make a step runnable. Status alone may not prove that
a step completed because some steps do not change it. Before rerunning such a
step, inspect the story file and expected artifacts; skip it only when its
expected result is clearly complete and valid.

## Execute A Step With A Subagent

For each runnable step:

1. Announce concise progress as `[current/total] Step name`.
2. Locate the named skill, preferring the project's `.agents/skills/<skill>/`
   directory, then the active Codex skill registry.
3. Use Codex multi-agent tools to spawn a fresh `worker` subagent for this
   step. If the multi-agent tools are not currently exposed, discover them with
   tool search before proceeding.
4. Pass the target BMAD skill to the subagent, preferably as a structured
   `skill` item using the resolved skill path.
5. Pass the resolved `STORY_ID`, `STORY_KEY`, `STORY_FILE`, current status,
   project root, and expected result in the subagent prompt.
6. Tell the subagent that it is not alone in the codebase, must not revert
   unrelated changes, must follow the provided `$bmad-*` skill, must stop on
   that skill's HALT conditions, and must return:
   - completion status
   - changed or created files
   - validations/tests run
   - resulting story status
   - issues or follow-up work
7. Wait for the subagent to finish before starting the next step. Pipeline
   steps are dependent and must not run in parallel.
8. Review the subagent result. If the subagent returned changes as an uploaded
   patch or forked-workspace result, integrate and inspect those changes before
   continuing.
9. Re-read sprint status, the story file, and expected artifacts. Proceed only
   if the step's expected result is satisfied.
10. Close the completed subagent once its result has been reviewed.
11. For nested workflows that offer Create/Resume/Validate/Edit without the
    user choosing a mode, choose Create for a new step and Resume only when an
    interrupted artifact clearly exists.

### High-Autonomy Checkpoint Handling

The story pipeline is expected to run with the most completion-oriented safe
defaults. If a subagent stops at a nested BMAD checkpoint, inspect the checkpoint
text before deciding whether to ask the user.

Automatically answer and continue when the checkpoint is an operational choice
with an unambiguous completion-oriented default:

- Code review scope confirmation: continue when the resolved story, diff base,
  and review mode match the pipeline target.
- Code review prompt-file fallback: if the code-review worker cannot launch its
  reviewer subagents and writes Blind Hunter / Edge Case Hunter / Acceptance
  Auditor prompt files, the parent orchestrator must launch fresh Codex
  subagents for those prompts, collect their findings, and send them back to the
  code-review worker. Do not ask the user to run those prompts manually.
- Code review patch handling: when asked how to handle `patch` findings, choose
  **Apply every patch** (`1`) without asking the user. This applies only to
  findings already classified as `patch`, meaning the fix is supposed to be
  unambiguous and does not require product judgment.
- Code review post-completion next-step menu: choose **Done** unless the
  pipeline itself needs to continue to the next configured step.

Do not auto-answer checkpoints that require real product or safety judgment:

- `decision-needed` findings whose correct behavior is ambiguous.
- destructive operations, credential/secret access, external account changes,
  or data deletion.
- validation failures, unmet gates, unresolved HIGH/MEDIUM findings, or
  conflicts that make the expected result unclear.

If the same auto-answerable checkpoint repeats, answer it once more only after
checking that the worker made progress. If it repeats without progress, stop and
report the loop.

Use this prompt shape for each worker:

```text
Use $<skill-name> at <skill-path> to execute "<step name>" for BMAD story:
- STORY_ID: <story-id>
- STORY_KEY: <story-key>
- STORY_FILE: <story-file-or-empty>
- Current status: <status>
- Expected result: <expected-result>

Work in <project-root>. You are not alone in the codebase; do not revert
unrelated changes, and adapt to existing changes. Follow the skill exactly,
including its required files, checkpoints, validation gates, and HALT
conditions. Pipeline autonomy preference: for non-ambiguous operational choices,
use the most completion-oriented option; for code-review `patch` findings,
apply every patch. Return completion status, changed/created files, validations
run, resulting story status, and any issues.
```

Do not emulate Claude Code slash commands, the `Task(...)` syntax, or a `yolo`
argument. The Codex equivalent of the old Claude `Task(...)` calls is
`spawn_agent` plus `wait_agent` plus verification by the parent orchestrator.

Nested skill instructions and Codex safety rules take precedence over pipeline
automation. Honor hard HALTs, approval requirements, mandatory user
checkpoints, and validation failures unless the checkpoint matches the explicit
High-Autonomy Checkpoint Handling rules above.

## Test Quality Gate

After the **Develop story** step completes, the orchestrator MUST enforce a
zero-skip, full-coverage quality gate. The pipeline does not accept skipped
tests or sub-100% coverage. The orchestrator owns this check regardless of what
the subagent reports.

### Zero-Skipped-Test Enforcement

1. Run the project's full test suite (infer the test command from project
   structure — the same command the dev-story subagent should have used).
2. Parse the test output for skipped tests (`skip`, `skipped`, `xit`, `xdescribe`,
   `it.skip`, `test.skip`, `@unittest.skip`, `@pytest.mark.skip`, or equivalent
   framework-specific skip markers).
3. If **any** skipped test is detected:
   - **HALT the pipeline.** Do not proceed to code review.
   - Report: the exact count of skipped tests, which test files contain them,
     and the skip reason if extractable.
   - The pipeline is blocked until every skipped test is either unskipped
     (implemented), removed, or explicitly justified as intentional by the user.
   - Do NOT auto-accept or ignore skipped tests.

### Full-Coverage Enforcement

1. Run the project's coverage tool if one is configured (infer from
   `package.json`, `pyproject.toml`, `Cargo.toml`, `build.gradle`, `Makefile`,
   or project conventions).
2. If the project has **no** coverage tooling configured, skip this check but
   note it in the completion summary as a gap.
3. If a coverage tool exists, run it and parse the coverage report. The target
   is **100% line/branch coverage on all code changed or added by this story**.
   At minimum, overall project coverage must not decrease.
4. If coverage is below 100% on changed code:
   - **HALT the pipeline.** Do not proceed to code review.
   - Report: coverage percentage, uncovered lines/files, and a concrete
     suggestion (e.g., "add tests for `src/auth/login.ts:42-58`").
   - The pipeline is blocked until coverage reaches 100% on changed code, or
     the user explicitly accepts the gap.

### Quality Gate Decision

After both checks pass (or the user explicitly overrides a failure), record a
**quality-gate decision** in the story file's Dev Agent Record:

```
Quality Gate: PASS | OVERRIDDEN
- Skipped tests: 0
- Coverage (changed code): XX%
- Decision: [auto-passed | user-override: <reason>]
```

## Residual Problem Escalation

When the pipeline cannot resolve an issue automatically and a quality gate
would otherwise be violated, the orchestrator MUST NOT silently accept the
deficiency. Instead, escalate residual problems at the final report.

### Escalation Rules

1. **Collect** all unresolved issues across every pipeline step:
   - Skipped tests that remain skipped
   - Coverage gaps below 100% on changed code
   - Code-review findings left as `decision-needed` or unresolved
   - Traceability gaps (ACs without matching tests)
   - Any validation gate that was user-overridden
2. **Categorize** each issue:
   - `BLOCKER`: should prevent merge/deploy (skipped tests, coverage < 100%,
     unresolved HIGH review findings)
   - `WARNING`: acceptable with user acknowledgment (unresolved MEDIUM findings,
     missing coverage tooling)
   - `INFO`: noted for awareness
3. **Escalate** in the final completion report: present every residual problem
   with its category, what it affects, and a concrete remediation action.
4. **Do NOT transition** the story to `done` if any `BLOCKER` remains without
   explicit user override. The pipeline must report `BLOCKER` items and stop.

## Failure Handling

Stop at the first failed step. This includes Test Quality Gate failures and
any unmet subagent validation gates. Do not run later steps or manually force
status to `done`.

Report:

- failed step and current story status
- concrete error or unmet gate
- test quality status (skipped count, coverage percentage) if applicable
- artifacts already changed
- the exact `$bmad-*` skill that can resume the failed step

Leave valid completed work intact.

## Completion

After all configured steps finish:

1. Re-read sprint status and the story file.
2. Run the **final quality audit**:
   - Confirm 0 skipped tests in the full suite.
   - Confirm 100% coverage on changed code (or that coverage tooling absence
     was documented as a `WARNING`).
   - Confirm the traceability artifact contains a quality-gate decision.
3. Collect and present all **residual problems** per the Residual Problem
   Escalation rules above.
4. Verify the story is `done`, all required tasks are checked, and the
   traceability artifact contains a gate decision.
5. If code review did not transition the story to `done`, report the unmet
   review gate and stop. Do not force the transition.
6. If any `BLOCKER`-category residual problem remains without user override,
   report it prominently and stop. Do not silently mark the story complete.
7. Summarize completed steps, final status, test results (skipped count,
   coverage %), review result, traceability gate, residual problems, and key
   artifact paths.

Update status only through the nested BMAD workflows. Preserve YAML comments,
ordering, and unrelated user changes.
