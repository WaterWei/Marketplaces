---
name: atuin
description: "Agent shell 命令历史搜索与分析（atuin CLI）。TRIGGER when: 需要查看 agent 执行过什么 bash 命令、按 agent/目录/时间过滤命令历史、调试命令失败、复用之前的命令、分析命令模式。BLOCKING: 查询 agent 命令历史前必须调用此 skill。SKIP: agent 会话历史（用 ctx）、herdr pane 实时输出（用 herdr）、纯 git 历史（用 git log）。"
compatibility: "Requires atuin 18.x+ with agent hook support. Hooks auto-installed via atuin hook install <agent>."
metadata:
  author: rayh4c
  version: "1.0.0"
  user-invocable: "true"
  effort: "low"
---

# atuin — Agent 命令历史

所有 Agent（Claude Code / Codex / Pi / Grok）执行的 Bash 命令自动记录到 atuin shell 历史，通过 `--author` 标签区分人工与 agent 命令。

## 执行约束

0. **未核实的不当事实用** — 参数先 `atuin [subcmd] --help` 确认；搜 ctx 找先例

## 按 agent 搜索

```bash
# 指定 agent
atuin search --author 'claude-code' --cmd-only
atuin search --author 'codex' --cmd-only
atuin search --author 'pi' --cmd-only
atuin search --author 'grok' --cmd-only

# 特殊值（单引号防 shell 展开）
atuin search --author '$all-agent' --cmd-only    # 所有 agent 命令
atuin search --author '$all-user' --cmd-only     # 仅人工命令
```

## 过滤

```bash
# 按工作目录
atuin search --author '$all-agent' --cwd /mnt/d/project --cmd-only

# 按时间
atuin search --author 'claude-code' --after "2026-07-15" --cmd-only
atuin search --author 'codex' --before "2026-07-14" --cmd-only

# 按退出码（找失败命令）
atuin search --author 'claude-code' --exit 1 --cmd-only --limit 10

# 排除特定目录
atuin search --author '$all-agent' --exclude-cwd /tmp --cmd-only

# 关键词搜索
atuin search --cmd-only "git push"
atuin search --cmd-only "herdr plugin"

# 限制数量
atuin search --author '$all-agent' --cmd-only --limit 20
```

## 输出格式

```bash
# 默认（含时间和元数据）
atuin search --author 'claude-code' --limit 5

# 仅命令文本
atuin search --author 'claude-code' --cmd-only --limit 5

# 人类可读时间
atuin search --author 'claude-code' --human --limit 5

# 自定义格式
atuin search --author '$all-agent' -f "{author} | {time} | {command}" --limit 10

# 可用变量：{command} {directory} {duration} {user} {host} {time} {exit} {relativetime}
# 注：{author} 实测可用但未在 --help 中列出
```

## 统计

```bash
atuin stats    # 命令使用统计
```

## Hook 集成状态

| Agent | hook 安装 | author 标签 |
|-------|----------|------------|
| Claude Code | `atuin hook install claude-code` | `claude-code` |
| Codex | `atuin hook install codex` | `codex` |
| Pi (omp) | `atuin hook install pi` + `omp config set extensions` | `pi` |
| Grok | 自定义 `~/.grok/hooks.json` + `~/.grok/hooks/atuin-grok.sh` | `grok` |

## 与其他 skill 的分工

| 需求 | 用什么 |
|------|--------|
| agent 执行了什么 shell 命令 | **atuin**（本 skill） |
| agent 会话历史（对话/决策/代码） | ctx |
| 当前 pane 实时输出 | herdr `pane read` |
| git 代码变更历史 | `git log` / `git blame` |

## 避坑

| 问题 | 解决 |
|------|------|
| `$all-agent` 被 shell 展开 | 用单引号 `'$all-agent'` |
| heredoc 内容被记录为命令 | atuin 限制，搜索时用 `--cwd` 或 `--author` 过滤 |
| Pi 没记录 | 需 `omp config set extensions '["~/.pi/agent/extensions/atuin.ts"]'` |
| Grok 记录为 claude-code | 需自定义 `~/.grok/hooks.json`（默认加载了 claude 的 hooks） |
| atuin 没有 `-n` / `--dry-run` | 不要猜测，先查 `atuin search --help` |
