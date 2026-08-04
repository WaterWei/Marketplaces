---
name: gh
description: "GitHub CLI 结构化搜索与代码分析。TRIGGER when: gh search repos/code/issues/prs/commits、gh repo/issue/pr view、gh api、gh release list、gh --json/--jq 结构化输出、GitHub 数据过滤/排序/聚合、commit diff 查看、branch/tag 列表。注意：gh search releases 不存在，用 gh release list。BLOCKING: 执行任何 gh 数据查询命令前必须调用此 skill。SKIP: 纯 git 操作（git log/blame/diff 等）、不涉及 gh 命令或 GitHub API 的操作。"
compatibility: "Requires shell and gh (authenticated); network for GitHub API. External jq optional (gh has built-in --jq)"
metadata:
  author: rayh4c
  version: "3.0.0"
  argument-hint: "<repos|code|issues|prs|skills|release-list|commit|branches|tags|api> [query]"
  user-invocable: "true"
  effort: "low"
---

# gh — GitHub CLI 搜索与代码分析

直接用 `gh` CLI 完成 GitHub 搜索、查看、列表、API 调用。塑形用 **`gh` 内置 `--jq`**，**不需要**外置 `jq`。

## 执行约束

0. **未核实的不当事实用** — 参数/字段名先 `gh [subcmd] --help` 确认，字段名省略值让 gh 列出（`gh search repos --json`）；搜 ctx/atuin 找先例
1. **`--json <fields>`** — 搜索/查看/列表先取结构化字段（camelCase）。字段名不确定时省略值即列出可用字段：`gh search repos --json`
2. **塑形用 `gh --jq`** — 与 `--json` 同命令。**禁止**默认 `| jq`
3. **`--limit` 控量** — 默认 30，按需调整
4. **只输出用户问的** — 截断长输出，禁止 banner
5. **mutating 无 dry-run**（repo delete / pr merge / release delete）— 执行前先用只读命令（view / list / api GET）确认目标

## 搜索命令

| 类型 | 命令 | 关键 --json 字段 |
|------|------|-----------------|
| 仓库 | `gh search repos` | fullName, stargazersCount, language, url |
| 代码 | `gh search code` | path, repository.nameWithOwner, url |
| Commit | `gh search commits` | sha, commit.message, author.login |
| Issue | `gh search issues` | title, url, state, commentsCount |
| PR | `gh search prs` | title, url, state, isDraft, author.login |

### 查询构建

过滤条件优先用**独立 flag**，勿写进 query 字符串：

```bash
gh search repos "cli" --stars ">1000" --language rust --json fullName,stargazersCount --limit 5
```

**搜索 flags**：repos 用 `--language --owner --stars --sort`，code 用 `--language --filename --repo`，issues/prs 用 `--owner --repo --state --label --sort`。完整 flags 见 [references/search-dsl.md](references/search-dsl.md)。

## 查看 / 列表

```bash
gh repo view <owner/repo> --json nameWithOwner,description,stargazerCount,url
gh issue view <N> --repo <o/r> --json title,body,state,comments
gh pr view <N> --repo <o/r> --json title,body,state,files,additions,deletions

gh release list --repo <o/r> --json tagName,publishedAt --limit 10
gh api repos/<o>/<r>/branches --jq '.[].name'
gh api "repos/<o>/<r>/contents/<path>?ref=<ref>" --jq '.content' | base64 -d
```

## API 调用

```bash
gh api <endpoint> --jq '<filter>'
gh api repos/nushell/nushell --jq '.stargazers_count'
gh api rate_limit --jq '.resources | {search: .search.remaining, code: .code_search.remaining}'

# 分页（结果超 30 条时）：--paginate 自动翻页；加 --slurp 合并为单一数组
gh api repos/<o>/<r>/contributors --paginate --jq '.[].login'
```

Rate limit：search 30/min，code_search 10/min，core 5000/hr。

## 陷阱速查

| 问题 | 解决 |
|------|------|
| `language:rust` 写进 query 无效 | 用 `--language rust` flag |
| 误装外置 `jq` | gh 自带 `--jq` |
| code search 搜 fork 空 | query 加 `fork:true` 或用 `contents` 直读 |
| `--json` 字段名错 | camelCase：search 用 `stargazersCount`，view 用 `stargazerCount`（不同！） |
| `gh search releases` 不存在 | 用 `gh release list --repo` |
| 引号短语对 code search 无效 | 多关键字 AND 替代 |

> 更多典型用法（项目分析工作流、批量筛选、jq 聚合统计）见 [references/recipes.md](references/recipes.md)，搜索 DSL 完整语法见 [references/search-dsl.md](references/search-dsl.md)。
