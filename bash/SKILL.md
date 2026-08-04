---
name: bash
description: "Bash 命令与脚本执行规范（agent 安全模式 + 管道编排）。TRIGGER when: 在 Bash 中执行 shell 命令（非 Python/TS 脚本）、管道组合、文件操作、git 操作、进程管理、文本处理（sed/awk/jq，管道内 grep）、目录遍历（find）、文件检查（test -f）。BLOCKING: 执行多行 bash 脚本或复杂管道前必须调用此 skill。SKIP: Python 脚本（uvsh）、TS/JS 脚本（bunsh）、gh 数据查询（gh skill）、herdr 控制（herdr skill）、agent 会话历史（ctx skill）。"
compatibility: "Requires bash 4.x+. ShellCheck recommended for scripts >10 lines."
metadata:
  author: rayh4c
  version: "1.1.0"
  user-invocable: "true"
  effort: "low"
---

# bash — 命令与脚本执行规范

Agent 的通用执行面：编排、探索、管道组合。复杂数据处理下沉到 uv/bun，bash 只做胶水。

## 执行约束

0. **未核实的不当事实用** — 参数先 `<tool> [subcmd] --help` 确认；搜 ctx/atuin 找先例；不确定就小范围实测
1. **单行优先** — 能一行管道解决的不写多行脚本
2. **`2>&1` 捕获 stderr** — 需要 JSON 解析时分离：`cmd 2>/tmp/err | jq ...`
3. **输出控制** — `| head -N` / `| tail -N` / `--limit` 截断，超 50 行必截
4. **禁止交互** — 不用 `read`/`select`/`less`/`vim`/`git add -i`
5. **复杂逻辑用 uvsh/bunsh** — bash 超 10 行考虑换语言，禁止写超 100 行 bash

## 安全模式

```bash
# 多行脚本头部必加
set -euo pipefail
```

**硬规则**：
- **工作区边界** — 默认只操作当前 repo/workspace，出界（`~`、`/`、他仓）先确认
- **强制 timeout** — 网络/编译/find/测试等长命令必须 `timeout N cmd`
- **密钥不进 argv** — 避免 `TOKEN=xxx cmd`（进 atuin + process list）；用 env 文件或已有 secret 机制
- **mutating 前侦察** — 先只读确认（ls/cat/git status），再修改
- **破坏性操作需确认** — `rm -rf`（非空目录）、`git reset --hard`、`git push --force`
- **输出预算** — 超 50 行截断，不让无界输出淹没 context

**不要做**：
- `eval` / `curl | bash` / `chmod 777` / 写 `/etc`
- 反引号 `` `cmd` `` → 用 `$(cmd)`
- `[ ]` → 用 `[[ ]]`
- `which cmd` → 用 `command -v cmd`
- 无 timeout 的死循环 / `find /`

## 管道编排（高频模式）

```bash
# JSON 处理（stderr 分离，避免污染 jq）
gh api endpoint 2>/dev/null | jq -r '.field'
herdr pane get w4:p1 2>&1 | jq -r '.result.pane.agent_status'

# 文本统计
find . -name "*.md" | wc -l
grep -rn "pattern" --include="*.md" | head -20

# 批量操作
for f in dir/*/SKILL.md; do echo "$(wc -l < "$f") $f"; done | sort -rn

# 条件链
test -f file && echo "exists" || echo "missing"
cd /target || { echo "dir missing"; exit 1; }

# 并行（显式收集退出码）
cmd1 & p1=$!; cmd2 & p2=$!; wait "$p1"; wait "$p2"
```

## 变量与引号

```bash
"$VAR"                 # 始终双引号
"${array[@]}"          # 数组展开
local name="value"     # 局部变量
"${VAR:-default}"      # 默认值
"${path##*/}"          # basename
"${file%.*}"           # 去扩展名
```

## 常用模式

| 场景 | 命令 |
|------|------|
| 文件存在 | `test -f path && ...` |
| 目录递归 | `find . -name "*.ext" -exec cmd {} \;` |
| 文本替换 | `sed 's/old/new/g' file`（macOS 需 `sed -i ''`） |
| JSON 提取 | `jq -r '.key'` |
| 行数统计 | `wc -l < file` |
| 去重计数 | `sort \| uniq -c \| sort -rn` |
| 超时控制 | `timeout 30 command` |
| 命令存在 | `command -v cmd \|\| echo "not found"` |
| 安全 cd | `cd /dir \|\| exit 1` |
| 预览再删 | `find . -name '*.tmp' -print` → 确认后 `-delete` |

## 与其他 skill 的分工

| 需求 | 用什么 |
|------|--------|
| 纯 shell 命令/管道/文件操作 | **bash**（本 skill） |
| Python 数据处理/API/库 | uvsh |
| TS/JS 数据处理/API/库 | bunsh |
| GitHub 搜索/查看 | gh |
| 终端复用/agent 控制 | herdr |
| agent 历史搜索 | ctx |
| agent 命令历史 | atuin（详见 [atuin skill](../atuin/SKILL.md)） |

**判断标准**：需要外部库 → uvsh/bunsh。纯文本/文件/进程/git → bash。JSON 超 3 层嵌套 → jq 或 uvsh/bunsh。

## 避坑清单

| 问题 | 解决 |
|------|------|
| 猜参数报错 | 先查 `--help` |
| 输出太长 | `\| head -20` 或 `--limit` |
| 管道中间失败静默 | `set -o pipefail` |
| 变量 word splitting | 始终 `"$var"` |
| `find /` 扫全盘 | 从 `.` 或具体路径开始 |
| heredoc 内 `$` 被展开 | 用 `<< 'EOF'`（quoted） |
| `grep` 无匹配 exit 1 | `grep ... \|\| true`（`set -e` 下） |
| `sed -i` 跨平台 | Linux `sed -i 's//'`，macOS `sed -i '' 's//'` |
| `cd` 失败继续执行 | `cd /dir \|\| exit 1` |
| git 操作前未检查 | 先 `git status --short` |

> 完整风格规范与安全清单见 [references/style-and-safety.md](references/style-and-safety.md)
