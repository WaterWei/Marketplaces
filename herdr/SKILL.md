---
name: herdr
description: "控制 Herdr 终端复用器（workspace/tab/pane/agent 管理）。TRIGGER when: 用户明确提到 Herdr、要在 Herdr 中控制 pane/tab/workspace/终端、要启动/检查/通信另一个 agent（codex/claude/grok）、要在旁边 pane 跑命令/测试/服务。BLOCKING: 涉及 Herdr 操作时必须先调用此 skill；启动 agent 前必须先 ctx search 搜索相关历史。SKIP: 不涉及 Herdr 的普通任务、仅因为「可以用后台终端」就触发（必须用户明确要求）。需要 HERDR_ENV=1。"
compatibility: "Requires HERDR_ENV=1 (running inside a Herdr-managed pane), herdr CLI in PATH, and ctx CLI for the mandatory pre-launch history search."
metadata:
  author: rayh4c
  version: "2.0.0"
  upstream: "ogulcancelik/herdr"
  user-invocable: "true"
  effort: "low"
---

# Herdr — 终端复用器 + Agent 运行时

Herdr 把终端组织成 workspace → tab → pane 层级，自动检测 agent 身份和状态，通过 `herdr` CLI 暴露控制能力。

## 前置检查（每次必做）

```bash
test "${HERDR_ENV:-}" = 1
```

**检查失败** → 不在 Herdr 内，停止操作。

## CLI 语法发现

```bash
herdr --help
herdr pane          # pane 相关命令
herdr workspace     # workspace 管理
herdr tab           # tab 管理
herdr wait          # 等待状态/输出
herdr terminal      # 终端信息
herdr notification  # 通知
herdr worktree      # git worktree
herdr session       # session 管理
```

**禁止**裸跑 `herdr`（会启动 TUI）。**禁止**探测性地省略参数跑 mutating 命令。

## ID 体系

| 类型 | 格式示例 |
|------|---------|
| workspace | `w1` |
| tab | `w1:t1` |
| pane | `w1:p1` |
| terminal | `term_...` |

**ID 是不透明字符串**——从 JSON response 解析，不要猜测拼接。

### 获取当前上下文

```bash
echo "$HERDR_WORKSPACE_ID"   # 当前 workspace
echo "$HERDR_TAB_ID"         # 当前 tab
echo "$HERDR_PANE_ID"        # 当前 pane
```

操作当前 pane 用 `--current`。不要依赖 UI 焦点 pane。

### 发现运行状态

```bash
herdr workspace list
herdr pane list --workspace "$HERDR_WORKSPACE_ID"
herdr pane current --current
```

## Agent 状态机

| 状态 | 含义 |
|------|------|
| `idle` | 空闲/就绪，结果已被看到 |
| `working` | 工作中 |
| `blocked` | 被阻塞，需要输入 |
| `done` | 完成，结果**未被**看到（后台 tab） |
| `unknown` | 未检测到 agent |

`idle` 和 `done` 都算完成，区别是注意力状态（前台→idle，后台→done）。

## 启动 Agent（核心操作）

默认在当前 tab 分兄弟 pane。**不要**创建 workspace/tab/worktree，除非用户明确要求。

**启动前强制 ctx search**——不可跳过。完整 8 步流程见 [references/agent-launch.md](references/agent-launch.md)。

精简骨架：

```bash
# 0. ctx search（强制）
ctx search "<任务关键词>"

# 1-2. 判断方向 + 分屏
herdr pane layout --pane "$HERDR_PANE_ID"
herdr pane split --current --direction right --no-focus

# 3. 命名 + 启动（模型详见 references/models.md）
herdr pane rename <pane-id> "reviewer"
herdr pane run <pane-id> "<agent-command>"

# 4. 等就绪 + 发任务
herdr wait agent-status <pane-id> --status idle --timeout 30000
herdr pane run <pane-id> "Review the diff."

# 5. 等完成 + 读结果
herdr wait agent-status <pane-id> --status done --timeout 120000
herdr pane read <pane-id> --source recent-unwrapped --lines 120

# 6. 如遇 blocked → 读输出判断原因，能自动回答则 pane run 回答
# 7. 发送后续指令 → herdr pane run <pane-id> "..."

# 8. 收尾
herdr pane close <pane-id>
```

## 在其他 Pane 跑普通命令

```bash
herdr pane split --current --direction right --no-focus
herdr pane run <pane-id> "cargo test"
herdr wait output <pane-id> --match "test result" --timeout 120000
herdr pane read <pane-id> --source recent-unwrapped --lines 120
```

**先 inspect 再 wait**：先读当前输出，再等未来状态变化。

### 读取模式

| `--source` | 用途 |
|------------|------|
| `visible` | 当前 viewport |
| `recent-unwrapped` | 近期 scrollback（软换行合并，**首选**） |
| `recent` | 近期 scrollback（含软换行） |
| `detection` | agent 检测用底部快照 |

需要颜色时用 `--format ansi`，否则 text。

## Agent 命令历史

所有 Agent 的 Bash 命令自动记录到 atuin。搜索用法见 [atuin skill](../atuin/SKILL.md)。

## 远程镜像（herdr-mirror）

通过 SSH 镜像远程 workspace/pane 到本地 sidebar，用标准 herdr 命令操作远程 pane。

```bash
herdr plugin action invoke mirror start       # 启动镜像
herdr plugin action invoke mirror status      # 查看状态
herdr pane run <remote-pane-id> "command"     # 操作远程
```

完整配置见 [references/mirror-plugin.md](references/mirror-plugin.md)。

## 与 ctx 联动

**分工**：herdr = 实时控制面（当前 pane），ctx = 历史记忆面（已索引 session），atuin = shell 命令历史。三者互补。

| 需求 | 工具 | 命令 |
|------|------|------|
| 当前实时输出 | herdr | `herdr pane read <pane-id> --source recent-unwrapped --lines N` |
| 过去会话历史 | ctx | `ctx search "<query>" --provider <claude/codex/grok>` |
| 具体 shell 命令 | atuin | `atuin search "<keyword>"` |

## 安全和协调规则

- **无 dry-run**：herdr 控制命令没有预览机制，mutating 前必须用只读命令（get/list/read/layout）侦察
- **`--no-focus`**：后台工作默认不抢焦点
- **`--current` 或显式 ID**：不依赖其他 client 的焦点 pane
- **从 JSON response 解析 ID**：不猜测拼接
- **先 inspect 再 wait**
- **不关闭**不是你创建的 workspace/tab/pane/session
- **不要** `herdr server stop`（除非用户明确要求）
- **不杀主 Herdr 进程**
