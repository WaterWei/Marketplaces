# Agent 启动完整流程

## 0. 强制：ctx 搜索历史（启动任何 agent 前必做）

**在分屏启动 agent 之前，必须先用 ctx 搜索相关历史**，避免重复工作、继承之前的决策和失败经验。

```bash
which ctx || { echo "ctx 未安装，历史搜索不可用"; }
ctx search "<即将交给 agent 的任务关键词>"

# 如有相关历史，导出给新 agent 参考
ctx show session <ctx-session-id> --format markdown --out /tmp/prior-context.md

# 如无相关历史，在后续 pane run 任务描述中注明「ctx 未找到相关历史」
```

**ctx 未安装时**：向用户说明历史搜索不可用，建议安装（`gh release download -R raystyle/ctx -p 'ctx-linux-x86_64.tar.gz' -O - | tar xz -C ~/.local/bin/`），然后继续后续步骤。不要因 ctx 缺失而完全阻塞 agent 启动。

搜索时可按 provider 缩小范围：`--provider claude`、`--provider codex`、`--provider grok`。

## 1. 判断分屏方向

```bash
herdr pane layout --pane "$HERDR_PANE_ID"
```

- 宽 pane → `--direction right`
- 窄/高 pane → `--direction down`
- 避免同方向反复分屏（会创建不可用的窄列/矮行）

## 2. 分屏（不抢焦点）

```bash
herdr pane split --current --direction right --no-focus
```

从 JSON response 读取 `result.pane.pane_id`。

## 3. 命名 + 启动 Agent

```bash
herdr pane rename <pane-id> "reviewer"
herdr pane run <pane-id> "<agent-command>"
```

**默认交互式启动**——不传任务作为 argv，不加 non-interactive flag。`-m`/`--model` 只改模型，不改交互模式。

模型指定详见 [references/models.md](models.md)。

## 4. 等待就绪 + 发任务

```bash
herdr pane get <pane-id>
herdr wait agent-status <pane-id> --status idle --timeout 30000
herdr pane run <pane-id> "Review the current diff and report only actionable findings."
```

## 5. 等待完成 + 读取结果

```bash
herdr wait agent-status <pane-id> --status working --timeout 30000
herdr wait agent-status <pane-id> --status done --timeout 120000
herdr pane read <pane-id> --source recent-unwrapped --lines 120
```

**判断等 idle 还是 done**：
- 后台 tab → 等 `--status done`
- 前台 tab → 等 `--status idle`
- 不确定 → 先等 `done`（timeout 60s）→ 超时后 `herdr pane get` 看状态

**超时处置**：

```bash
herdr pane get <pane-id>          # 看当前 agent_status
herdr pane read <pane-id> --source recent-unwrapped --lines 30
# working → 加大 timeout 重试
# blocked → 见 Step 6
# idle → 已完成（前台 tab）
```

## 6. 处理 blocked 状态

```bash
herdr pane get <pane-id>   # agent_status = "blocked"
herdr pane read <pane-id> --source recent-unwrapped --lines 30

# 能自动回答（确认 y/n、选择选项）：
herdr pane run <pane-id> "y"
# 需要用户决策 → 报告给用户，等指示后再 pane run

herdr wait agent-status <pane-id> --status idle --timeout 120000
```

## 7. 发送后续指令

```bash
herdr pane run <pane-id> "Now check the failing test."
```

## 8. 收尾：关闭自己创建的 pane

```bash
herdr pane close <pane-id>
```

只关闭你自己 split 创建的 pane。不确定是否是自己创建的 → 不关闭。
