# 典型用法

一律 `gh --json` + `--jq` 结构化输出。

## 搜索仓库 + 塑形

```bash
# 基础搜索（过滤用独立 flag）
gh search repos "cli tool" --stars ">1000" --language rust \
  --json fullName,stargazersCount,language --limit 10 \
  --jq '.[] | {repo: .fullName, stars: .stargazersCount, lang: .language}'

# 按 stars 排序找热门项目
gh search repos "web framework" --language python --sort stars --limit 15 \
  --json fullName,stargazersCount,forksCount,updatedAt,description \
  --jq '.[] | {name: .fullName, stars: .stargazersCount, forks: .forksCount, updated: .updatedAt, desc: .description}'

# 最近活跃的高质量项目
gh search repos "async" --language python --stars ">=2000" --sort updated --limit 20 \
  --json fullName,stargazersCount,pushedAt,description \
  --jq '.[] | select(.pushedAt > "2025-01-01") | {name: .fullName, stars: .stargazersCount, pushed: .pushedAt}'
```

### 常用搜索 qualifiers

| qualifier | 示例 | 说明 |
|-----------|------|------|
| `--language` | `--language python` | 语言过滤 |
| `--stars` | `--stars ">1000"` | star 数量 |
| `--sort` | `--sort stars` / `--sort updated` | 排序 |
| `--topic` | `--topic cli` | 按 topic |
| `--created` | `--created ">2024-01-01"` | 创建时间 |
| `--updated` | `--updated ">2025-01-01"` | 最近更新 |
| `--owner` | `--owner google` | 按所有者 |

## 项目分析

```bash
# 单个项目结构化信息（注意：view 字段名与 search 不同）
gh repo view psf/requests --json name,description,stargazerCount,forkCount,updatedAt,pushedAt,licenseInfo,primaryLanguage,repositoryTopics,url

# 搜索结果批量分析（按 star 降序 + 筛选活跃项目）
gh search repos "http client" --language python --stars ">=1000" --limit 50 \
  --json fullName,stargazersCount,pushedAt,description,licenseInfo \
  --jq 'map(select(.pushedAt > "2025-01-01")) | sort_by(.stargazersCount) | reverse | .[] | {name: .fullName, stars: .stargazersCount, license: .licenseInfo.name, desc: .description}'

# License 分布统计
gh search repos "data processing" --language python --limit 100 \
  --json licenseInfo \
  --jq 'group_by(.licenseInfo.name) | map({license: .[0].licenseInfo.name, count: length}) | sort_by(.count) | reverse'

# TSV 表格输出（便于管道处理）
gh search repos --language rust --sort stars --limit 20 \
  --json fullName,stargazersCount,description \
  --jq '.[] | [.fullName, (.stargazersCount | tostring), .description] | @tsv'
```

## 搜索代码

```bash
# 基础
gh search code "nushell" --json path,repository --limit 20 \
  --jq '[.[] | {repo: .repository.nameWithOwner, path: .path}]'

# 按仓库聚合
gh search code "AsyncClient" --language python --json repository --limit 30 \
  --jq '[.[] | .repository.nameWithOwner] | group_by(.) | map({repo: .[0], count: length}) | sort_by(.count) | reverse'

# 在特定项目内搜索
gh search code "关键词" --repo owner/repo --json path,textMatches --limit 20
```

## Issues / PR 过滤

```bash
# Issues 按评论数筛选
gh search issues "bug" --repo nushell/nushell --state open \
  --json title,url,commentsCount --limit 20 \
  --jq '.[] | select(.commentsCount > 5) | {title: .title, comments: .commentsCount, url: .url}'

# Draft PR
gh search prs --repo vercel/next.js --state open --draft \
  --json title,author,updatedAt --limit 10 \
  --jq '.[] | {title: .title, author: .author.login, updated: .updatedAt}'
```

## 文件 / commit / release

```bash
# 读文件内容（指定 ref）
gh api "repos/nginx/nginx/contents/src/http/ngx_http_core_module.c?ref=release-1.30.1" --jq '.content' | base64 -d | head -50

# commit 详情
gh api repos/nginx/nginx/commits/2046b45aa0 \
  --jq '{sha: .sha, msg: .commit.message, author: .commit.author.name, files: [.files[] | {f: .filename, add: .additions, del: .deletions}]}'

# release 列表
gh release list --repo nushell/nushell --json tagName,publishedAt --limit 5 \
  --jq '.[] | {tag: .tagName, date: .publishedAt}'

# fork 检测
gh api repos/user/forked-repo --jq '.fork'
```

## Rate Limit

```bash
gh api rate_limit --jq '.resources | {search: .search.remaining, code: .code_search.remaining, core: .core.remaining}'
```

## 项目分析工作流

1. **发现**：`gh search repos "关键词" --language <lang> --sort stars`
2. **筛选**：jq 过滤 stars/pushed/license
3. **深入**：`gh repo view owner/repo` + `gh search code "关键词" --repo owner/repo`
4. **决策**：看 pushedAt（活跃度）、stars/forks（社区）、licenseInfo（许可）、topics（分类）
