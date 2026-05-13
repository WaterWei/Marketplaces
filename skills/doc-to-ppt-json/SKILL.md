---
name: doc-to-ppt-json
description: '将大型结构化 Markdown 文档分割、并发处理、聚合生成 PPT Deck JSON。Use when user says "文档转ppt", "大文档生成json", "doc to ppt json", "split and convert", or wants to process a large structured markdown into presentation JSON.'
---

# Doc to PPT JSON

**Goal:** 将大型结构化 Markdown 文档（如教育材料、长篇报告）转换为 PPT Deck JSON。通过 Python 分割脚本 + subagent 并发处理 + Python 聚合验证的流水线，突破单次 LLM 上下文限制。

**Your Role:** 文档结构分析师 + 流水线调度器。你擅长理解文档层级结构、调度并行任务、处理异常和修复。

## Conventions

- Bare paths (e.g. `steps/step-01-input.md`) resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory.
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.

## JSON Schema Reference

生成的 JSON 必须严格符合 `{skill-root}/schema.md` 中定义的格式。在开始工作前，**必须先读取** `./schema.md` 了解完整的类型定义和字段说明。

## Pipeline Architecture

```
输入文档 (.md)
    │
    ▼
[Step 1] 读取输入 & 收集元数据
    │
    ▼
[Step 2] Python split_document.py → chunk_001.md ~ chunk_NNN.md + manifest.json
    │
    ▼
[Step 3] Subagent 并发处理 → chunk_001.json ~ chunk_NNN.json
    │   (每个 subagent 接收: 片段内容 + 完整 schema + layout_hint)
    │
    ▼
[Step 4a] Python aggregate_json.py --repair → 自动修复引号/逗号等问题
[Step 4b] Python aggregate_json.py --validate → 逐片验证报告
    │   失败? → 重试 subagent → 仍失败? → AI 修复
    ▼
[Step 4c] Python aggregate_json.py --aggregate → 合并 + 重编号 → 最终 JSON
```

## Key Rules

- 分片文件必须带编号命名：`chunk_001.md` → `chunk_001.json`
- 空分片是错误，分割阶段即应报错
- 验证在聚合之前，精确定位失败分片
- 聚合遇到异常立即中断，不静默跳过
- subagent prompt 中必须包含完整 schema

## Customization

本 skill 支持通过 `customize.toml` 定制行为：

| 层级 | 路径 | 作用域 |
|------|------|--------|
| 基础 | `{skill-root}/customize.toml` | skill 默认值 |
| 团队 | `{project-root}/_bmad/custom/doc-to-ppt-json.toml` | 团队共享覆盖 |
| 个人 | `{project-root}/_bmad/custom/doc-to-ppt-json.user.toml` | 个人偏好覆盖 |

关键配置项：
- `split.max_concurrency` — subagent 最大并发数
- `split.section_types` — 文档分段模式（正则 + 层级 + 布局建议）
- `split.section_order` — 匹配优先级

## WORKFLOW ARCHITECTURE

- **Micro-file Design**: Each step is self-contained and followed exactly
- **Just-In-Time Loading**: Only load the current step file
- **Sequential Enforcement**: Complete steps in order, no skipping

### Step Processing Rules

1. **READ COMPLETELY**: Read the entire step file before acting
2. **FOLLOW SEQUENCE**: Execute sections in order
3. **WAIT FOR INPUT**: Halt at checkpoints and wait for human
4. **LOAD NEXT**: When directed, read fully and follow the next step file

### Critical Rules

- **NEVER** load multiple step files simultaneously
- **ALWAYS** read entire step file before execution
- **NEVER** skip steps or optimize the sequence
- **ALWAYS** follow the exact instructions in the step file
- **ALWAYS** halt at checkpoints and wait for human input

## FIRST STEP

Read fully and follow: `./steps/step-01-input.md`
