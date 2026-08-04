---
name: bunsh
description: "Bun + TypeScript heredoc / 单文件脚本执行规范（auto-install + 内置 API）。TRIGGER when: Bash 中执行 TS/JS（bun --silent run、import auto-install、shebang #!/usr/bin/env bun、fetch/Bun.file/bun:sqlite、zod、cheerio、零依赖 I/O、SQLite ETL、并发 HTTP）。BLOCKING: 在 Bash 中执行 TS/JS 代码前必须调用此 skill。SKIP: Python（from...import / uv）、纯 shell、已有项目 node_modules 的常规开发（bun test/lint）、polars/pydantic/jc/duckdb。注意：无 Bun.glob()，用 import { Glob } from 'bun' + new Glob('**/*.ts').scanSync({ cwd })。无 PEP 723 式 inline TOML；依赖靠 import 自动安装。"
compatibility: "Requires shell and bun; network for auto-install and APIs as needed"
metadata:
  author: rayh4c
  version: "2.0.0"
  user-invocable: "true"
  effort: "low"
---

# bunsh — Bun + TypeScript 执行规范

少量多行代码（5-30 行）+ Bun 内置 API + 极轻量库 = 完成真实复杂任务。

## 与 uv 的对照

| 特性 | uv（Python） | Bun（JS/TS） |
|------|--------------|--------------|
| 依赖声明 | PEP 723 `# /// script` TOML | **无**（import 时 auto-install） |
| Shebang | `#!/usr/bin/env -S uv run --script` | `#!/usr/bin/env bun` |

**结论**：不要写 `# /// script` 式 TOML——Bun 无效。依赖直接 `import "pkg"`。

## 两种执行模式

| 模式 | 何时用 | 启动方式 |
|------|--------|----------|
| **A. Ephemeral heredoc**（默认） | 一次性分析、管道步骤 | `bun --silent run - << 'TS' … TS` |
| **B. 文件脚本 + shebang** | 要复用、进 PATH | `./script.ts` 或 `bun --silent run script.ts` |

依赖模型：写在 `import` 里 → Bun auto-install。**禁止**为一次性脚本手写 `package.json`。

## 执行约束

0. **未核实的不当事实用** — 参数先 `bun [subcmd] --help` 确认；搜 ctx/atuin 找先例
1. **一律 `bun run`** — 禁止 `node`/`tsx`/`npx`
2. **依赖 = import** — 配合 `--silent` 降噪
3. **quoted heredoc** — `<< 'TS'`。**勿用** `<<<`
4. **代码意图注释** — `// task:` + `// step: N.`
5. **禁止单行 hack** — 禁止 `bun -e` / `node -e`
6. **内置 API 优先** — 能用 Bun 内置就不装包

### A. Ephemeral heredoc（默认）

```bash
bun --silent run - << 'TS'
// task: 抓取页面标题
// step: 1. cheerio 解析（auto-install）
import { load } from "cheerio"
const html = await fetch("https://example.com", { signal: AbortSignal.timeout(10000) }).then(r => r.text())
const $ = load(html)
console.log($("title").text().trim())
TS
```

**连续 heredoc**：之间禁止输出文字解释，用 `// step:` 写上下文串联。错误恢复在下一步 `// step:` 写原因与调整。

### B. 文件脚本 + shebang（可复用）

```typescript
#!/usr/bin/env bun
// task: 彩色问候
// step: 1. auto-install chalk 并打印
import chalk from "chalk"
console.log(chalk.green("Hello, Bun!"))
```

```bash
chmod +x script.ts && ./script.ts
```

Agent 落盘脚本：写 `.ts`（shebang + import），`chmod +x`。不要 `bun init`（用户已有项目除外）。

## 输出约束

1. **只输出用户问的** — 不"顺便"打印额外信息
2. **截断长输出** — `.slice(0, 20)` + 总结
3. **禁止** debug 输出、banner/装饰线
4. **数值格式化** — `toLocaleString()` 千分位
5. **结构化优先** — `console.table` / JSON
6. **错误静默** — catch 只输出 `{"error": "简短描述"}`

## Bun 内置 API（零依赖首选）

| 内置 API | 用途 |
|----------|------|
| `fetch` + `AbortSignal.timeout(ms)` | HTTP + 超时 |
| `bun:sqlite` | 内存 SQLite，SQL 聚合/ETL |
| `Bun.file(path)` / `Bun.write(path, data)` | 文件读写 |
| `new Glob("**/*.ts").scanSync({ cwd })` | 文件 glob（`import { Glob } from "bun"`） |
| `Bun.spawn([...])` | 子进程 |
| `` Bun.$`cmd` `` | shell 管道（`import { $ } from "bun"`） |
| `Bun.password.hash(pw, algo)` | argon2id / bcrypt |
| `Bun.serve({fetch, port})` | HTTP 服务 |
| `Bun.gzipSync` / `Bun.gunzipSync` | 压缩 |

## 核心库速查

| 领域 | 首选 |
|------|------|
| HTML 解析 | cheerio |
| 数据校验 | zod |
| 日期 | date-fns |
| CSV | papaparse |
| 并发控制 | p-limit |
| CLI 美化 | picocolors + cli-table3 |
| 数据分析 | bun:sqlite + arquero |

> 完整库推荐见 [references/libs.md](references/libs.md)

## 典型模式

并发 HTTP + SQLite、Zod、cheerio、流式、WebSocket 等见 [references/patterns.md](references/patterns.md)。

## 进阶能力

- **`bun build --compile`** — 把脚本打成单文件可执行 binary（可分发，无需 bun 运行时）
- **`bun x <pkg>`** — 临时跑 CLI 工具（类似 npx，不污染项目；有 shim 时可用 `bunx`）
- **`bun run --env-file .env`** — 加载环境变量文件
- **`bun run --watch`** — 文件变更时自动重跑

## 避坑清单

| 问题 | 解决 |
|------|------|
| 写 `# /// script` TOML | Bun 无此机制，依赖用 `import` |
| sharp / argon2 / bcrypt（native） | wasm-vips / `Bun.password` |
| `Bun.glob()` | `import { Glob } from "bun"` + `scanSync` |
| auto-install 被关掉 | 显式 `--install=fallback` 或 `-i` |
| here-string `<<<` | 一律 `<< 'TS'` |
| esbuild / tsx / node-fetch | 多余，Bun 原生替代 |
