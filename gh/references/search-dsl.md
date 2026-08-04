# GitHub 搜索 DSL 与参数详细参考

## 参数速查

所有搜索命令共享 `--limit`（默认 30）。

**gh search repos**: `--language` `--owner` `--topic` `--stars` `--created` `--updated` `--match`（name/description/readme）`--sort`（stars/forks/updated/help-wanted-issues）`--order`（asc/desc）`--license` `--visibility` `--archived` `--followers` `--forks` `--size` `--good-first-issues` `--help-wanted-issues` `--include-forks`（false/true/only）`--number-topics`

**gh search code**: `--language` `--filename` `--extension` `--owner` `--repo` `--match`（file/path）`--size`

> **注意**：引号短语对 code search 无效（Legacy API 不支持精确短语匹配），自动降级为关键字 AND。

> **Fork 搜索策略**：GitHub code search **默认排除所有 fork 仓库**。搜索代码结果为空时：先 `gh api repos/<repo> --jq '.fork'` 确认是否 fork → 若是 fork，在 query 中加 `fork:true` → 仍空则 GitHub 未索引该 fork，用 `gh api repos/.../contents/` 直接读文件。

**gh search commits**: `--author` `--author-date` `--author-email` `--author-name` `--committer` `--committer-date` `--committer-email` `--committer-name` `--hash` `--merge` `--parent` `--tree` `--owner` `--repo` `--sort`（author-date/committer-date）`--order`（asc/desc）`--visibility`

**gh search issues**: `--owner` `--repo` `--author` `--assignee` `--label` `--state`（open/closed）`--created` `--updated` `--closed` `--comments` `--match`（title/body/comments）`--sort`（created/updated/comments/reactions/interactions）`--order`（asc/desc）`--archived` `--visibility` `--app` `--commenter` `--include-prs` `--interactions` `--involves` `--language` `--locked` `--mentions` `--milestone` `--no-assignee` `--no-label` `--no-milestone` `--no-project` `--project` `--reactions` `--team-mentions`

**gh search prs**: issues 全部 flags + `--base` `--head` `--checks`（pending/success/failure）`--draft` `--merged` `--merged-at` `--review`（none/required/approved/changes_requested）`--review-requested` `--reviewed-by`

**gh skill search**: `--owner` `--limit`（默认 15）`--page`

**gh release list**: `--repo`（必填）`--limit`（默认 10）`--exclude-drafts` `--exclude-pre-releases` `--order`（asc/desc）

## DSL 语法

在搜索 query 中可用的完整 DSL。

### 逻辑运算

- `OR`：`cli OR shell`
- `NOT`（前缀 `-`）：`hello NOT world`、`panic -label:bug`

### 比较和范围

- `stars:>100`、`stars:>=100`
- `stars:100..500`（闭区间）
- `created:>2024-01-01`
- `created:2024-01-01..2024-12-31`
- `size:<1000`（KB）

### 布尔限定符

`is:open`、`is:closed`、`is:archived`、`is:fork`、`is:vendored`、`is:generated`、`is:locked`、`is:merged`、`is:draft`、`is:unmerged`

### 代码搜索专用

- **正则**：`'/sparse.*index/'`、`'/^App\/src\//'`、`'/(?-i)True/'`
- **符号搜索**：`symbol:WithContext`、`symbol:/^String::to_.*/`
- **路径通配符**：`path:*.toml`、`path:/src/**/*.rs`
- **内容限定符**：`content:`、`filename:`、`extension:`

**限制**：正则不支持 look-around；代码搜索必须含关键词（纯 `language:java` 不合法，需 `something language:java`）；结果上限 1000 条。

### Code search qualifier 互斥

`language:`、`path:` 等 qualifier 在 query 中与 `repo:` 同时出现会返回空。必须用独立 flag：

```bash
# BAD: qualifier + repo: 互斥，返回空
gh search code "Learner repo:dmlc/xgboost language:cpp" --json path,repository

# GOOD: 用独立 flag
gh search code "Learner" --repo dmlc/xgboost --language cpp --json path,repository
gh search code "RegTree" --repo dmlc/xgboost --filename tree_model.h --json path,repository
```

### `gh search repos` 过滤条件用 flag

`gh search repos` 把 `language:rust` 写进 query 时，qualifier 可能被忽略（仍 exit 0，结果却不是目标语言）。语言、stars 范围、owner 等**一律用独立 flag**；REST `gh api search/repositories -f q='...'` 的 query DSL 仍可靠。

```bash
# BAD: language: 进 query，结果可能不是 Rust
gh search repos "stars:>50000 language:rust" --json fullName,language --limit 5

# GOOD
gh search repos "stars:>50000" --language rust --json fullName,language --limit 5
gh search repos "cli" --stars ">1000" --language rust --json fullName,stargazersCount --limit 5
```

### Legacy Code Search API 限制总结

- 不支持 exact phrase（引号短语降级为 AND 关键字）
- qualifier 与 `repo:` 内联互斥（用独立 flag）
- 特殊字符（`- . / _` 等）匹配较弱，推荐用 regex：`'/setWindowBounds/'`

## 查询方式选择

| 场景 | 用法 |
|------|------|
| 多关键字 AND | `gh search repos "cli shell" ...` |
| 精确短语（repos/issues/prs） | `gh search repos '"vim plugin"' ...` |
| 精确短语（code search） | 不支持，改用多关键字：`"class Learner"` |
| OR/NOT 逻辑 | `gh search repos "cli OR shell" ...` |
| qualifier 过滤 | **优先独立 flag**：`--stars ">1000" --language rust`。`gh search repos` 勿在 query 写 `language:rust`（会被吞掉且仍 exit 0） |
| 否定限定符 | query 中 `-label:bug`，或 `--no-label` flag |
| PR 分支/审核状态 | `--base main --draft --merged` |
| 代码正则/符号/路径 | query 中 `"symbol:WithContext"` 或 `"'/regex/'"` |
| code search + repo + language | 用独立 flag：`--repo o/r --language cpp`（不要 query 内联） |
| 搜索 fork 仓库代码 | 先 `gh api repos/<r> --jq '.fork'` 确认 → query 加 `fork:true` → 仍空用 `gh api .../contents/` |

## --json 字段名参考（camelCase）

**repos**（`gh search repos --json`）:
fullName, description, stargazersCount, forksCount, updatedAt, createdAt, language, license, url, isArchived, isFork, homepage, size, owner

**code**（`gh search code --json`）:
path, repository（嵌套对象，含 `.nameWithOwner`）, textMatches, sha, url

**issues/prs**（`gh search issues/prs --json`）:
title, url, state, labels, author（嵌套 `.login`）, commentsCount, createdAt, updatedAt, closedAt, body, assignees, number, repository, isDraft（仅 prs）

**releases**（`gh release list --json`，非 search）:
tagName, name, isPrerelease, isDraft, isLatest, publishedAt, createdAt

> `gh search releases` **不存在**。必须用 `gh release list --repo o/r --json ...`。

## 塑形：优先 `gh --jq`（内置，无需外置 jq）

`gh` 对 `--json` 输出和 `gh api` 响应提供 **`-q` / `--jq`**（jq 语法），见 `gh help formatting`。单条 `gh` 命令**不要**再 `| jq`。

```bash
# 提取字段 + 重命名
gh search repos "cli" --json fullName,stargazersCount --limit 10 \
  --jq '[.[] | {repo: .fullName, stars: .stargazersCount}]'

# 过滤
gh search repos "cli" --json fullName,stargazersCount --limit 30 \
  --jq '[.[] | select(.stargazersCount > 1000)]'

# 嵌套字段（code search）
gh search code "nushell" --json path,repository --limit 20 \
  --jq '[.[] | {repo: .repository.nameWithOwner, path: .path}]'

# 排序
gh search repos "cli" --json fullName,stargazersCount --limit 20 \
  --jq 'sort_by(.stargazersCount) | reverse'

# 聚合
gh search code "AsyncClient" --language python --json repository --limit 30 \
  --jq '[.[] | .repository.nameWithOwner] | group_by(.) | map({repo: .[0], count: length}) | sort_by(.count) | reverse'

# 取前 N / labels
gh search issues "bug" --repo o/r --json title,labels --limit 20 \
  --jq '.[0:10]'
gh search issues "bug" --repo o/r --json title,labels --limit 20 \
  --jq '[.[] | {title: .title, labels: [.labels[].name] | join(",")}]'

# gh api 同样用 --jq
gh api rate_limit --jq '.resources.search.remaining'
```

外置 `jq` 仅用于：非 `gh` 的 JSON、或需把多条命令输出拼在一起再处理。