# CC Story Pipeline Workflow Steps

## Pipeline Configuration

Execute the following steps in order using Task tool.
Each step runs with "yolo" mode for auto-approval.

### Step 1: Create User Story
- Command: `/bmad-create-story {STORY_ID} yolo`
- Description: Creates story file with context from planning docs
- Return: Story ID, Title, Created files

### Step 2: Generate ATDD Tests
- Command: `/bmad-testarch-atdd {STORY_ID} yolo`
- Description: Generate failing acceptance tests (TDD red phase)
- Return: ATDD checklist and test files

### Step 3: Development
- Command: `/bmad-dev-story {STORY_ID} yolo`
- Description: Implement story to pass tests (TDD green phase)
- Return: Modified files, Changes summary

### Step 4: Code Review (FIX, don't just report)
- Command: `/bmad-code-review {STORY_ID} yolo`
- Description: Adversarial code review — MUST FIX all issues, not just report them
- Return: Conclusion (pass only when all fixed), What was fixed, Final test results
- **Quality Gate (NON-NEGOTIABLE):**
  - ALL tests must be GREEN (passing). Zero failures.
  - NO skipped tests. Every test must run and pass.
  - If a test is incorrectly written, modify the test to be correct.
  - DO NOT return 'needs-fix' with unresolved issues. Fix everything.

### Step 5: Trace Test Coverage (FIX gaps, don't just report)
- Command: `/bmad-testarch-trace {STORY_ID} yolo`
- Description: Generate traceability matrix and CLOSE ALL coverage gaps
- Return: Final coverage (must be 100%), Gate decision (pass), Tests added/fixed
- **Quality Gate (NON-NEGOTIABLE):**
  - Coverage MUST be 100%. No exceptions.
  - ALL tests GREEN. Zero failures, zero skips.
  - If tests are missing, CREATE them. If tests are broken, FIX them.
  - DO NOT return with 'gaps found'. Return with 'gaps CLOSED'.

## Post-Pipeline

After all steps complete:
1. Update sprint-status.yaml: story status → done
2. Update story document: Status: done, Tasks: ✅

## Customization

To modify the pipeline:
- Add/remove steps in this file
- Change step commands
- Reorder steps (update step numbers)
