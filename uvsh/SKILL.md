---
name: uvsh
description: "Python + uv heredoc / PEP 723 脚本执行规范（2025-2026 顶级库组合）。TRIGGER when: Bash 中执行 Python（uv run、--with、inline script metadata、# /// script、uv init --script、uv add --script、from...import、polars、pydantic、httpx、duckdb、jc、数据科学、PDF/Excel、CLI 结构化）。BLOCKING: 在 Bash 中执行 Python 代码前必须调用此 skill。SKIP: TypeScript/Bun、纯 shell、已有项目 venv 的常规开发命令（pytest/ruff 等）、Bun 任务。"
compatibility: "Requires shell and uv; network for package installs and APIs as needed"
metadata:
  author: rayh4c
  version: "2.0.0"
  user-invocable: "true"
  effort: "low"
---

# uvsh — Python + uv 执行规范

少量多行代码（5-30 行）+ 强力库组合 = 完成真实复杂任务。

## 两种执行模式

| 模式 | 何时用 | 启动方式 |
|------|--------|----------|
| **A. Ephemeral heredoc**（默认） | 一次性分析、管道步骤 | `uv run -q - << 'PY' … PY` |
| **B. 文件脚本 + PEP 723** | 要复用、进 PATH、固定版本 | `uv run -q script.py` 或 `./script`（shebang） |

依赖声明二选一：
1. **PEP 723 内联元数据**（推荐）— 依赖与版本跟代码走
2. **CLI `--with`** — 极短一次性调用：`uv run -q --with httpx,polars -`

> 使用内联元数据时，即使在项目目录内执行，**也会忽略项目依赖**。

## 执行约束

0. **未核实的不当事实用** — 参数先 `uv [subcmd] --help` 确认；搜 ctx/atuin 找先例
1. **一律 `uv run`** — 禁止裸 `python`/`pip install`
2. **依赖声明** — 优先 `# /// script` 元数据；极短调用可用 `--with`
3. **quoted heredoc** — `<< 'PY'`。**勿用** `<<<`
4. **代码意图注释** — `# task:` + `# step: N.`
5. **禁止单行 hack** — 禁止 `python -c`
6. **安静运行** — 加 `-q`

### A. Ephemeral heredoc（默认）

```bash
uv run -q - << 'PY'
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx", "polars"]
# ///
# task: 查询 API 数据
# step: 1. 获取并用 DataFrame 展示
import httpx, polars as pl
data = httpx.get("https://api.example.com/data", timeout=10).json()
print(pl.DataFrame(data))
PY
```

**连续 heredoc**：之间禁止输出文字解释，用 `# step:` 串联上下文。错误恢复在下一步 `# step:` 写原因与调整。

### B. 文件脚本 + PEP 723（可复用）

```bash
uv init --script example.py --python 3.12
uv add --script example.py 'httpx' 'polars>=1.0'
uv run -q example.py
```

脚本头部：

```python
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx", "polars>=1.0"]
# ///
```

**Shebang 可执行文件**：

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx"]
# ///
import httpx
print(httpx.get("https://example.com", timeout=10).status_code)
```

```bash
chmod +x script && ./script
```

Agent 落盘脚本：`uv init --script` + PEP 723 + `uv run -q`。不要 `pip install`。

## 输出约束

1. **只输出用户问的** — 不"顺便"打印额外信息
2. **截断长输出** — `[:20]` + 总结
3. **禁止** debug 输出、banner/装饰线
4. **数值格式化** — 大数字千分位
5. **结构化优先** — rich Table / JSON
6. **错误静默** — 异常只输出 `{"error": "简短描述"}`

## 核心库速查

| 领域 | 首选 |
|------|------|
| HTTP | httpx |
| HTML 解析 | selectolax |
| 数据校验 | pydantic v2 |
| 数据查询 | polars / duckdb |
| CLI 结构化 | jc |
| PDF | pymupdf (fitz) |
| 日期 | zoneinfo + dateutil |

> 完整库推荐见 [references/libs.md](references/libs.md)

## 典型模式

并发 HTTP + DuckDB、psutil、PDF、编码修复、asyncio 等见 [references/patterns.md](references/patterns.md)。

## 进阶能力

- **`uv audit`** — 依赖安全审计（CVE 扫描）
- **`uv check --script <file.py>`** — 检查 PEP 723 脚本的依赖/类型问题
- **`uv format --check --diff`** — 内置 ruff 格式化预览（不修改文件）
- **`uv tool run <pkg>`** — 一次性跑 CLI 工具（等价 npx/pipx run，不污染环境）

## 避坑清单

| 问题 | 解决 |
|------|------|
| 内联元数据下项目依赖"失踪" | 预期行为；脚本依赖写进 `dependencies` |
| 元数据块缺 `dependencies` | 始终写出（可为空列表） |
| `ZoneInfoNotFoundError` on Windows | 依赖加 `tzdata` |
| DuckDB `generate_series` 列名 | `SELECT * FROM generate_series(1,5) t(n)` |
| here-string `<<<` | 一律 `<< 'PY'` |
| 混用 `--with` 与元数据 | 同一脚本只选一种 |
