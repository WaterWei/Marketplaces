# Bun 典型代码模式

依赖靠 **`import` auto-install**（无 PEP 723 / 无 `--with`）。Ephemeral 用 `bun --silent run - << 'TS'`；可复用落盘 + shebang。

## 并发 HTTP + SQLite ETL（零依赖 + p-limit）

```bash
bun --silent run - << 'TS'
// task: API 状态检测 + SQLite 存储
// step: 1. 并发检测 GitHub 和 httpbin 的 API 状态，存入内存 SQLite
import pLimit from "p-limit"
import { Database } from "bun:sqlite"
const limit = pLimit(5)
const urls = ["https://api.github.com","https://httpbin.org/json"]
const results = await Promise.all(urls.map(u => limit(async () => {
  const r = await fetch(u, { signal: AbortSignal.timeout(5000) })
  return { url: u, status: r.status }
})))
const db = new Database(":memory:")
db.run("CREATE TABLE checks (url TEXT, status INTEGER)")
for (const r of results) db.run("INSERT INTO checks VALUES (?, ?)", r.url, r.status)
console.table(db.query("SELECT * FROM checks").all())
TS
```

## Zod 校验 + JSONL 流水线

```bash
bun --silent run - << 'TS'
// task: JSONL 数据校验与筛选
// step: 1. 从 data.jsonl 中校验并筛选 price > 100 的记录
import { z } from "zod"
const Item = z.object({ id: z.number(), price: z.number(), category: z.string() })
const text = await Bun.file("data.jsonl").text()
const items = text.split("\n").filter(Boolean).map(l => Item.parse(JSON.parse(l)))
console.table(items.filter(i => i.price > 100).slice(0, 20))
TS
```

## HTML 抓取 + cheerio 提取表格

```bash
bun --silent run - << 'TS'
// task: 网页表格数据提取
// step: 1. 从 example.com 抓取 HTML 并提取前 20 行表格数据
import { load } from "cheerio"
const html = await fetch("https://example.com/table").then(r => r.text())
const $ = load(html)
const rows: string[][] = []
$("table tr").slice(0, 20).each((_, tr) => {
  const cells: string[] = []
  $(tr).find("td, th").each((_, td) => cells.push($(td).text().trim().slice(0, 50)))
  if (cells.length) rows.push(cells)
})
console.table(rows)
TS
```

## 流式读取大文件（Bun.file().stream()，不全量加载）

```bash
bun --silent run - << 'TS'
// task: 大 JSONL 流式统计
// step: 1. 用 stream + TextDecoderStream 逐块解析，不把整文件读入内存
const stream = Bun.file("big.jsonl").stream().pipeThrough(new TextDecoderStream())
let buf = "", lines = 0, hits = 0
for await (const chunk of stream) {
  buf += chunk
  const parts = buf.split("\n")
  buf = parts.pop() ?? ""
  for (const l of parts) { if (!l) continue; lines++; if (JSON.parse(l).price > 100) hits++ }
}
if (buf) { lines++; if (JSON.parse(buf).price > 100) hits++ }
console.log(`lines=${lines} hits=${hits}`)
TS
```

## WebSocket 客户端（有界收集，超时守卫）

```bash
bun --silent run - << 'TS'
// task: WebSocket 收集前 N 条消息
// step: 1. 连接后超时守卫，收满 5 条或 5s 即关闭（绝不无限监听）
const msgs: string[] = []
const ws = new WebSocket("wss://ws.postman-echo.com/raw")
await new Promise<void>((resolve) => {
  const done = () => { try { ws.close() } catch {}; resolve() }
  const timer = setTimeout(done, 5000)
  ws.onopen = () => { for (let i = 0; i < 5; i++) ws.send(`ping-${i}`) }
  ws.onmessage = (e) => { msgs.push(String(e.data).slice(0, 40)); if (msgs.length >= 5) { clearTimeout(timer); done() } }
  ws.onerror = () => { clearTimeout(timer); done() }
})
console.table(msgs.slice(0, 10))
TS
```

## 压缩/解压（Bun.gzipSync 内置，零依赖）

```bash
bun --silent run - << 'TS'
// task: 文件 gzip 压缩往返
// step: 1. 读文件 → gzip → 落盘 .gz → gunzip 校验，单行打印字节数
const raw = new Uint8Array(await Bun.file("data.jsonl").arrayBuffer())
const gz = Bun.gzipSync(raw)
await Bun.write("data.jsonl.gz", gz)
const back = Bun.gunzipSync(gz)
console.log(`${raw.length} → ${gz.length} → ${back.length}`)
TS
```

## 可复用单文件脚本（shebang + auto-install）

无 `package.json`、无 `bun install`。`import` 即依赖声明。

```typescript
#!/usr/bin/env bun
// task: URL 状态探测
// step: 1. GET 并打印 status（零外部依赖可用全局 fetch）
const r = await fetch("https://example.com", { signal: AbortSignal.timeout(10000) })
console.log(r.status)
```

```typescript
#!/usr/bin/env bun
// task: 彩色输出
// step: 1. import 触发 auto-install
import chalk from "chalk"
console.log(chalk.green("ok"))
```

```bash
chmod +x status.ts greeter.ts
./status.ts
./greeter.ts
# 或
bun --silent run greeter.ts
```

对比 uv：不要写 `# /// script` TOML；Bun 没有官方 inline metadata。

## 跨 heredoc 链式执行 + 错误恢复

多步分析任务中，每步一个 heredoc，用 `// step:` 串联上下文。失败时在下一步注明原因和调整策略。

```bash
bun --silent run - << 'TS'
// task: GitHub release 分析
// step: 1. 获取最近 release 列表
const releases = await fetch("https://api.github.com/repos/anthropics/claude-code/releases",
  { signal: AbortSignal.timeout(10000) }).then(r => r.json())
console.table(releases.slice(0, 5).map((r: any) => ({ tag: r.tag_name, date: r.published_at })))
TS

bun --silent run - << 'TS'
// task: GitHub release 分析
// step: 2. 从 body 提取变更项（step1 最新 tag = v1.0.50）
const release = await fetch("https://api.github.com/repos/anthropics/claude-code/releases/tags/v1.0.50",
  { signal: AbortSignal.timeout(10000) }).then(r => r.json())
const lines = release.body.split("\n").filter((l: string) => l.startsWith("- "))
lines.forEach((l: string) => console.log(l))
TS

bun --silent run - << 'TS'
// task: GitHub release 分析
// step: 3. 429 限流重试，退避 2s（step1 返回 429）
await new Promise(r => setTimeout(r, 2000))
const releases = await fetch("https://api.github.com/repos/anthropics/claude-code/releases",
  { headers: { "User-Agent": "bun" }, signal: AbortSignal.timeout(10000) }
).then(r => r.json())
console.table(releases.slice(0, 5).map((r: any) => ({ tag: r.tag_name, date: r.published_at })))
TS
```

关键点：
- **连续 heredoc 之间禁止输出文字解释**
- 每步 `// step: N.` 带上下文（引用前步结果或失败原因）
- 错误恢复写在下一步的 `// step:` 注释里（如 "step1 返回 429"）
- catch 只输出 `{"error": "简短描述"}`，不打 stack
