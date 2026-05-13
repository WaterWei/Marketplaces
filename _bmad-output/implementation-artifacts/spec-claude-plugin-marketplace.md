---
title: 'Claude Code Plugin 市场支持'
type: 'feature'
created: '2026-05-13'
status: 'done'
route: 'one-shot'
---

# Claude Code Plugin 市场支持

## Intent

**Problem:** 项目缺少 `.claude-plugin` 目录，无法在 Claude Code Marketplaces 中被发现和安装。

**Approach:** 参考 terryso/claude-bmad-skills 的 `.claude-plugin` 结构，创建 `plugin.json`（技能清单）和 `marketplace.json`（市场元数据），使项目支持 Claude Code 插件市场。

## Suggested Review Order

1. [plugin.json](../../.claude-plugin/plugin.json) — 插件声明：名称、版本、技能路径、关键词
2. [marketplace.json](../../.claude-plugin/marketplace.json) — 市场清单：owner、元数据、plugin 条目
