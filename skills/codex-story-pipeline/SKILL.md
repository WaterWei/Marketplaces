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

## Failure Handling

Stop at the first failed step. Do not run later steps or manually force status
to `done`.

Report:

- failed step and current story status
- concrete error or unmet gate
- artifacts already changed
- the exact `$bmad-*` skill that can resume the failed step

Leave valid completed work intact.

## Completion

After all configured steps finish:

1. Re-read sprint status and the story file.
2. Verify the story is `done`, all required tasks are checked, and the
   traceability artifact contains a gate decision.
3. If code review did not transition the story to `done`, report the unmet
   review gate and stop. Do not force the transition.
4. Summarize completed steps, final status, test results, review result,
   traceability gate, and key artifact paths.

Update status only through the nested BMAD workflows. Preserve YAML comments,
ordering, and unrelated user changes.
