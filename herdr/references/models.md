# Agent 模型目录

## 默认四角色

| 角色 | Agent | 默认模型 | 替补模型 | ctx provider |
|------|-------|---------|---------|--------------|
| 主力开发/协调 | Claude Code | opus 4.6 | glm-5.2[1m] | `claude` |
| 深度推理/review | Pi (omp) | deepseek-v4-pro | — | `pi` |
| 快速评估/测试 | Codex | gpt-5.5 | glm-5.2 | `codex` |
| 独立视角/验证 | Grok | grok-4.5 | grok-composer-2.5-fast | `grok` |

## 启动命令

```bash
# Claude Code（默认 opus，交互式）
herdr pane run <pane-id> "claude"
herdr pane run <pane-id> "claude --model 'glm-5.2[1m]'"

# Pi/OMP（必须带 cpa/ 前缀）
herdr pane run <pane-id> "omp --model cpa/deepseek-v4-pro"
herdr pane run <pane-id> "omp --model cpa/glm-5.2"

# Codex（默认 gpt-5.5）
herdr pane run <pane-id> "codex"
herdr pane run <pane-id> "codex -m glm-5.2"
```

## Claude Code 模型

**CPA 网关模型必须带 `[1m]` 后缀**才能启用 1M context。不带 `[1m]` 只有 200K。

CPA 网关可用：`glm-5.2[1m]`, `deepseek-v4-pro[1m]`, `gpt-5.5[1m]`
原生别名（自带 1M）：`fable`, `opus`, `sonnet`, `haiku`
原生完整名：`claude-fable-5`, `claude-opus-4-8`, `claude-sonnet-5`

## Pi (omp) 模型

通过 CPA 网关，模型名必须带 `cpa/` 前缀。所有内置 provider 已禁用。

```bash
omp --model cpa/deepseek-v4-pro
omp --model cpa/deepseek-v4-flash
omp --model cpa/glm-5.2
omp --model cpa/glm-5-turbo
omp --model cpa/gpt-5.5
```

atuin hook：extension 方式（`~/.pi/agent/extensions/atuin.ts`）
ctx provider：`pi`（搜历史用 `ctx search "<query>" --provider pi`）

## Codex 模型

通过 CLIProxyAPI 网关，不需要 `[1m]`。

```bash
codex -m gpt-5.5
codex -m glm-5.2
codex -m deepseek-v4-pro
```

查看可用模型：`cat ~/.codex/model-catalog.json | jq '.models[].name'`

## Grok 模型

```bash
herdr pane run <pane-id> "grok"
herdr pane run <pane-id> "grok -m grok-4.5"
herdr pane run <pane-id> "grok -m grok-composer-2.5-fast"
```

查看可用模型：`grok models`
ctx provider：`grok`（搜历史用 `ctx search "<query>" --provider grok`）
