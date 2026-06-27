---
name: cc-story-pipeline
description: Run configurable CC pipeline for story delivery using subagent —追求全绿测试、零跳过、100% 覆盖
argument-hint: <story-number> e.g., 1-1 or 2-3 (optional, auto-selects if omitted)
---

# CC Story Pipeline

Complete the delivery pipeline for story `{ARGUMENT}` using configurable workflow.

## 质量门禁 — 核心原则 (Quality Gate — Core Principles)

**这个 pipeline 的唯一目标是交付完美代码，不是生成报告。**

每个 subagent 必须理解并遵守以下 NON-NEGOTIABLE 原则：

| 原则 | 要求 | 不可接受 |
|------|------|----------|
| 测试状态 | ALL GREEN | 任何 failure 或 error |
| 跳过测试 | ZERO skipped | 任何 skip/ignore/xit/xdescribe |
| 覆盖率 | 100% | 任何未覆盖的代码路径 |
| 问题处理 | 主动修复 | 仅报告问题 |
| 测试修改 | 允许修改错误的测试 | 禁用或跳过测试 |

**关键行为准则：**
- 发现问题 → 直接修复代码/测试 → 验证修复 → 继续
- 绝不允许：发现 bug 后只写报告，期待人类去修
- 如果测试本身写错了，修改测试使其正确，而不是跳过它
- Code review 的结论只能是 "pass"（已修复完毕），不能是 "needs-fix"（待修复）
- Trace 的结论只能是 "100% coverage, pass"，不能是 "有 gap"

---

## Pre-step: Determine Story Number

If `{ARGUMENT}` is empty or not provided:

1. Read `_bmad-output/implementation-artifacts/sprint-status.yaml` (or `docs/sprint/sprint-status.yaml`) to find stories
2. Find the first story with status "todo" or "in-progress"
3. Use that story number as `{STORY_ID}`
4. If no story found, ask user to specify story number

The story number format is typically `X-Y` (e.g., `1-1`, `2-3`).

## Execution Strategy

1. Read workflow steps from **references/workflow-steps.md**
2. Execute each step sequentially using Task tool (general-purpose agent)
3. Output progress after each step
4. After pipeline, update status to done

## Workflow Steps

Read and execute steps from **references/workflow-steps.md**.

For each step defined there, you MUST use the **Task tool** to execute in a subagent:

```
Task(
  subagent_type: "general-purpose",
  description: "<Step description>",
  prompt: "Execute the command: <COMMAND_WITH_STORY_ID>
Return: 1) Step completion status 2) Key outputs 3) Any issues to note"
)
```

### Example Invocations

**Step 1 - Create Story:**
```
Task(
  subagent_type: "general-purpose",
  description: "Create user story {STORY_ID}",
  prompt: "Execute /bmad-bmm-create-story {STORY_ID} yolo to create story file. Return: 1) Story ID and Title 2) Created files 3) Any issues"
)
```

**Step 2 - ATDD Tests:**
```
Task(
  subagent_type: "general-purpose",
  description: "Generate ATDD tests for {STORY_ID}",
  prompt: "Execute /bmad-tea-testarch-atdd {STORY_ID} yolo to generate acceptance tests. Return: 1) ATDD checklist 2) Test files created 3) Any issues"
)
```

**Step 3 - Development:**
```
Task(
  subagent_type: "general-purpose",
  description: "Develop user story {STORY_ID}",
  prompt: "Execute /bmad-bmm-dev-story {STORY_ID} yolo to implement story code. Return: 1) Modified files 2) Summary of changes 3) Any issues"
)
```

**Step 4 - Code Review (FIX, don't just report):**
```
Task(
  subagent_type: "general-purpose",
  description: "Code review and FIX for {STORY_ID}",
  prompt: "Execute /bmad-bmm-code-review {STORY_ID} yolo for adversarial review.

⚠️ CRITICAL INSTRUCTIONS — YOU MUST FIX, NOT JUST REPORT:
- Your job is NOT to report issues. Your job is to FIX ALL issues found.
- If code has bugs, FIX the code directly. Do not just describe the problem.
- If tests fail, FIX the tests or the code until ALL tests pass.
- DO NOT stop with 'needs-fix' conclusion and leave issues unresolved.
- ONLY return 'pass' when ALL issues have been actually fixed in the codebase.

QUALITY GATE — NON-NEGOTIABLE:
- ALL tests must be GREEN (passing). Zero failures allowed.
- NO skipped tests. Every test must run and pass.
- If a test is incorrectly written, modify the test to be correct.
- Do not disable or skip tests to make them pass.

Return: 1) Conclusion (pass — only if truly all fixed) 2) What you fixed (not what you found) 3) Final test results confirming all GREEN"
)
```

**Step 5 - Trace Coverage (FIX gaps, don't just report):**
```
Task(
  subagent_type: "general-purpose",
  description: "Trace and FIX coverage for {STORY_ID}",
  prompt: "Execute /bmad-tea-testarch-trace {STORY_ID} yolo for traceability matrix.

⚠️ CRITICAL INSTRUCTIONS — YOU MUST ACHIEVE 100% COVERAGE:
- Your job is NOT to report coverage gaps. Your job is to CLOSE ALL gaps.
- If coverage is below 100%, WRITE additional tests to reach 100%.
- If tests are missing for any requirement, CREATE those tests.
- If a test is skipped, UNSKIP it or rewrite it to actually work.
- DO NOT return with 'gaps found' — return with 'gaps CLOSED'.

QUALITY GATE — NON-NEGOTIABLE:
- Coverage MUST be 100%. No exceptions.
- ALL tests GREEN. Zero failures, zero skips.
- If a test is wrong/broken, fix or rewrite it — never skip it.
- If traceability matrix shows untested requirements, write tests for them NOW.

Return: 1) Final coverage percentage (must be 100%) 2) Gate decision (pass) 3) What tests you added/fixed to achieve 100%"
)
```

### Execution Flow

For each step:
1. Replace `{STORY_ID}` with the actual story number in the prompt
2. Call Task tool with the step's description and prompt
3. Wait for completion and capture result
4. Output progress: `[X/5] Step Name - Status`
5. If step fails, stop and report error

## Progress Display

After each step, output progress:

```
📊 Pipeline Progress: [X/5] ████████░░░░ 40%

✅ Step X: <Step Name>
   Result: <Brief result summary>
```

## Error Handling

If any step fails:
1. Stop executing subsequent steps
2. Output error information:
   ```
   ❌ Pipeline Failed at Step X: <Step Name>

   Error: <Error details>

   💡 Suggested actions:
   - Check the story file for issues
   - Run the failed step manually: <command>
   - Fix the issue and restart pipeline
   ```
3. Do NOT proceed to next steps

## Post-Pipeline: Update Status

After ALL steps complete successfully:

1. **Update sprint-status.yaml**:
   - Find the story entry
   - Change status from `in-progress` to `done`

2. **Update story document** (if exists):
   - Change `Status:` to `done`
   - Mark all tasks with ✅

Output final summary:
```
🎉 Pipeline Complete!

Story: {STORY_ID}
Status: done

📋 Steps completed: 5/5
✅ Create User Story
✅ Generate ATDD Tests
✅ Development
✅ Code Review
✅ Trace Test Coverage
```

## Configuration

To customize the pipeline workflow, edit:
**references/workflow-steps.md**

Changes supported:
- Add/remove steps
- Modify step commands
- Reorder steps
- Change descriptions
