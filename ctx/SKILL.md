---
name: ctx
description: "搜索本地 coding-agent 会话历史（ctx CLI → SQLite 索引）。TRIGGER when: 涉及之前做过的事（上次、之前、历史、以前试过、earlier session）、需要查找过去的决策/失败/命令/代码补丁、用户说 ctx/ctx search/搜历史/查记录、需要引用先前 agent 会话上下文、跨 session 追溯问题时间线。也在任务开始前主动检索相关历史（retrieval before work）。BLOCKING: 1) 通过 herdr 启动其他 agent 前必须先 ctx search；2) 开始非简单任务前应先搜历史确认有无前人经验。SKIP: 当前会话内的信息（已在上下文中）、纯 git log/blame 能回答的代码变更历史、不涉及 agent 会话的操作、明显简单的单步操作。支持 Claude Code / Codex / Grok / Pi 四个 provider。"
compatibility: "Requires ctx CLI (raystyle/ctx fork with Grok/Pi support). Install: gh release download -R raystyle/ctx -p ctx-linux-x86_64.tar.gz -O - | tar xz -C ~/.local/bin/. Local SQLite index, no network needed for search."
metadata:
  author: rayh4c
  version: "2.1.0"
  upstream: "raystyle/ctx (fork of ctxrs/ctx, adds Grok Build + Pi provider)"
  user-invocable: "true"
  effort: "low"
---

# ctx — 核心记忆基础设施

ctx 是多 agent 协作的**记忆层**——所有 agent（Claude Code / Codex / Grok / Pi）的会话历史都索引在本地 SQLite 中，任何 agent 都能搜到其他 agent 之前做过的事。

**万事先 ctx**：开始新任务前搜历史、遇到 bug 搜之前的经验、启动 agent（herdr）前**强制**搜索、用户说「之前/上次/历史」时自动触发。

## 前置条件

```bash
# 安装（若缺失）
gh release download -R raystyle/ctx -p 'ctx-linux-x86_64.tar.gz' -O - | tar xz -C ~/.local/bin/

# 确认就绪
ctx --help
ctx status
ctx sources
```

ctx 不可用时：向用户说明，建议安装，然后**继续工作**（不阻塞任务）。

## 搜索（核心步骤）

参数未核实时先查 `ctx [subcmd] --help`（如 `ctx search --help`、`ctx show event --help`）。

```bash
# 推荐：先按 workspace 收敛，避免跨项目噪音
ctx search "<query>" --workspace /mnt/d/skills

# 按 provider 过滤
ctx search "<query>" --workspace <cwd> --provider claude
ctx search "<query>" --workspace <cwd> --provider codex
ctx search "<query>" --workspace <cwd> --provider grok
ctx search "<query>" --workspace <cwd> --provider pi

# 进一步收窄
ctx search "<query>" --workspace <cwd> --since 30d --file <path> --limit 10

# 按事件类型过滤（message/tool_call/tool_output/command_started/file_touched 等）
ctx search "<query>" --workspace <cwd> --event-type tool_call

# 密集事件级结果（默认是 session 去重；加 --events 返回每条匹配事件）
ctx search "<query>" --workspace <cwd> --events

# 纯只读搜索（不触发重索引，确定性查询用）
ctx search "<query>" --workspace <cwd> --refresh off

# 扩大召回：--term 是 OR 式拓宽（非 AND），用于补充同义词
ctx search "<query>" --workspace <cwd> --term "<同义词>" --term "<相关关键词>"

# 聚焦单个 session
ctx search "<query>" --session <ctx-session-id>

# 详细输出
ctx search "<query>" --verbose
```

**Provider 命名与 ctx sources 的关系**：
- `ctx sources` 显示 `grok-build`，但搜索时用 `--provider grok`（CLI alias，效果一样）
- `ctx sources` 显示 `pi`，搜索时用 `--provider pi`
- sources 状态 `available` = 可搜索，`missing` = 路径不存在或未产生 session

**特殊字符转义**：query 中 `-` 开头的文本会被误解析为 ctx flag，用 `--term` 包裹：

```bash
# BAD
ctx search "--model deepseek"
# GOOD
ctx search "codex" --term "--model" --term "deepseek"
```

**搜索策略（逐步升级）**：

1. `--workspace` 收敛到当前项目
2. `--provider` / `--since` / `--file` 进一步收窄
3. 换措辞 / 换英文 / 换同义词
4. `--term` 扩大召回（OR 式，补充关键词）
5. `--session` 聚焦单个 session
6. `--include-subagents` 包含子 agent 信息

**搜不到时排查**：
- `ctx doctor` — 健康检查排障第一步
- `ctx sources` 确认 provider 状态为 `available`（非 `missing`）
- `ctx import --provider <p>` — source 显示 missing 时手动导入（或 `ctx import --all` 全量扫描）
- `ctx status` 看 indexed_items 数量
- 换更短/更泛的关键词
- `ctx sql "SELECT * FROM ctx_sessions WHERE provider='codex' ORDER BY started_at_ms DESC LIMIT 5"` 确认 session 存在

**常见 warning**：
- `refreshed <provider> with N rejected history record(s)` — 源数据有格式问题，ctx 已跳过。不影响搜索已索引的内容，可忽略。持续出现可检查源目录是否有损坏的 session 文件。

**Codex 环境**：ctx 默认排除当前 session tree。需要搜当前 session 时加 `--include-current-session`。

**Grok 环境**：当前 session **不会**被自动排除（与 Codex 不同）。搜索时可能搜到自己，用 `--workspace` + `--since` 收窄或排除当前 session ID 可缓解。

**输出约束**：默认文本输出。**不要**默认加 `--json`（太大，消耗 context）。

## 查看详情

```bash
ctx show event <ctx-event-id> --window 5    # 事件 + 上下文（需要更多时用 --window 20）
ctx show session <ctx-session-id>            # session 摘要（默认 --mode lite）
ctx show session <id> --mode full            # 完整 transcript（导出给其他 agent 用这个）
ctx locate event <ctx-event-id>              # 定位原始文件
ctx show session <id> --format markdown --out /tmp/ctx-session.md  # 导出
```

## ctx sql（高级查询）

仅当普通搜索无法表达时用 SQL（计数、聚合、跨表 join）。**不要**用 SQL 做全文搜索。

```bash
ctx docs show sql                # 查阅 SQL 文档
ctx sql "SELECT name FROM sqlite_schema WHERE type IN ('table','view') ORDER BY name"  # schema 探索
ctx sql "SELECT provider, COUNT(*) AS sessions FROM ctx_sessions GROUP BY provider"
ctx sql "SELECT path, provider FROM ctx_files_touched WHERE path LIKE '%AGENTS.md%' LIMIT 20"
```

## 历史研究报告

用户要求调查历史话题时：多角度搜索（变换关键词/provider/时间范围）→ 引用前 `ctx show event` 检查原始内容 → 跨 session 比对 → 产出报告。

报告格式：结论 → 支撑 ctx ID → 注意事项/空白 → 可选下一步建议。

搜不到时也要报告搜索范围：query、provider、workspace、since，以及未覆盖的 provider/source。

## 与 herdr 联动

通过 herdr 启动任何 agent 前，**必须先 ctx search**。完整联动流程见 [references/herdr-workflow.md](references/herdr-workflow.md)。

**分工**：herdr = 实时 pane 内容，ctx = 过去已完成 session 历史。两者互补。

## 引用规则

- **引用前必须检查原文**：`ctx show event <id> --window 5` 确认内容，不可仅凭搜索摘要引用
- ctx 内容影响了回答/实现时，**必须引用**。格式：`provider=<provider>, session=<ctx_session_id>, event=<ctx_event_id>`
- 跨片段综合时，标注为 synthesis 并列出支撑片段
- 引用不可用时，说明"原始源无法打开"

## 安全规则

- 默认文本输出，JSON 仅用于脚本/精确字段
- **不要**声称 ctx 推断出了未明确写出的决策
- **不要**在用户报告中粘贴 raw transcript、secrets、私有路径
- `~/.ctx` 及 provider transcript 路径视为私有
