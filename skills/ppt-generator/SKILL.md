---
name: ppt-generator
description: '将演讲稿/文稿转换为 PPT Deck JSON 格式。Use when user says "生成ppt", "convert to ppt", "演讲稿转ppt", "create presentation json", or wants to turn a script/draft into slide JSON.'
---

# PPT Generator

**Goal:** 将用户的演讲稿、文稿、大纲等内容，转换为 PPT Deck 项目可渲染的标准 JSON 文件。

**Your Role:** 演示文稿结构分析师 + JSON 工程师。你擅长从非结构化文本中提取逻辑结构，将其映射为最佳的幻灯片布局，并生成符合规范的 JSON。

## Conventions

- Bare paths (e.g. `steps/step-01-input.md`) resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory.
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.

## JSON Schema Reference

生成的 JSON 必须严格符合 `{skill-root}/schema.md` 中定义的格式。在开始工作前，**必须先读取** `./schema.md` 了解完整的类型定义和字段说明。

## Customization（自定义）

本 skill 支持通过 `customize.toml` 定制行为。配置有三层，优先级从低到高：

| 层级 | 路径 | 作用域 |
|------|------|--------|
| 基础 | `{skill-root}/customize.toml` | skill 默认值 |
| 团队 | `{project-root}/_bmad/custom/ppt-generator.toml` | 团队共享覆盖 |
| 个人 | `{project-root}/_bmad/custom/ppt-generator.user.toml` | 个人偏好覆盖 |

可配置项详见 `./customize.toml` 中的注释和示例。常用场景：
- **约束内容风格** — 通过 `persistent_facts` 注入规则（如"所有卡片 description 不超过 50 字"）
- **限制布局类型** — 如"只用 cover / cards / list / content"
- **统一品牌模板** — 引用公司规范文件作为持久化事实
- **自定义完成行为** — 如自动启动预览或复制文件路径

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for disciplined execution:

- **Micro-file Design**: Each step is self-contained and followed exactly
- **Just-In-Time Loading**: Only load the current step file
- **Sequential Enforcement**: Complete steps in order, no skipping
- **Append-Only Building**: Build the JSON incrementally

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
