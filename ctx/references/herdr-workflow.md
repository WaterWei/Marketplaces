# ctx + herdr 联动流程

## 从历史到行动：ctx → herdr（标准流程）

```bash
# 0. 强制：搜索历史（启动 agent 前必做）
ctx search "migration rollback" --workspace <cwd> --provider claude
ctx search "migration rollback" --workspace <cwd> --provider codex
ctx search "migration rollback" --workspace <cwd> --provider grok
ctx search "migration rollback" --workspace <cwd> --provider pi

# 1. 有相关历史 → 导出给新 agent 参考
ctx show event <ctx-event-id> --window 5
ctx show session <ctx-session-id> --format markdown --out /tmp/prior-context.md

# 2. 无相关历史 → 记录「ctx 未找到相关历史」，继续

# 3. 启动 agent（herdr 分屏流程见 herdr/references/agent-launch.md）
# 4. 发送任务时附带历史上下文
herdr pane run <pane-id> "继续 migration rollback，之前的工作记录在 /tmp/prior-context.md"
```

## 多 agent 上下文共享

用 ctx 为某个 agent 补充其他 agent 的历史经验：

```bash
# 搜索各 provider 的历史
ctx search "auth token refresh" --provider grok
ctx search "auth token refresh" --provider codex
ctx search "auth token refresh" --provider claude

# 综合历史发给目标 agent
herdr pane run <target-pane-id> "之前 Grok 处理过 auth token refresh，结论是 xxx（ctx session yyy）。请基于此继续。"
```

## 实时 vs 历史

| 需求 | 工具 | 命令 |
|------|------|------|
| 当前实时输出 | herdr | `herdr pane read <pane-id> --source recent-unwrapped --lines 120` |
| 过去会话历史 | ctx | `ctx search "<topic>" --provider claude --since 7d` |
| 全量导出 | ctx | `ctx show session <id> --format markdown --out /tmp/full-session.md` |
