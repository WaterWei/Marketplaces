# Bun/TS 顶级库详细参考

每个领域：第一选择 + 理由、第二选择 + 场景、过时/避开、heredoc 示例。

依赖靠 `import "pkg"` **auto-install**（无 PEP 723 / 无 `uv --with` 等价 CLI）。可复用脚本用 `#!/usr/bin/env bun` + `chmod +x`。

## HTTP / 网络请求

**首选：Bun.fetch** — 原生 Web Fetch API，HTTP/2，stream，自动 JSON，性能远超 Node fetch，零依赖。
**次选：ky**（轻量 Fetch 包装，自动重试/JSON/超时）、axios（遗留兼容）
**避开：** got（维护弱）、node-fetch（多余）

```bash
bun --silent run - << 'TS'
const urls = ["https://api.github.com", "https://httpbin.org/json"]
const results = await Promise.all(
  urls.map(u => fetch(u, { signal: AbortSignal.timeout(5000) })
    .then(r => r.json()).catch(e => ({ error: String(e) })))
)
console.table(results)
TS
```

## HTML / XML 解析

**首选：cheerio** — jQuery-like API，heredoc 爬虫事实标准，内存低，CSS 选择器强大。
**次选：linkedom**（完整 DOM 模拟，需浏览器级操作）、htmlparser2（底层流式解析）
**避开：** jsdom（太重，heredoc 不推荐）

```bash
bun --silent run - << 'TS'
import { load } from "cheerio"
const html = await fetch("https://news.ycombinator.com/").then(r => r.text())
const $ = load(html)
$(".athing").slice(0, 20).each((_, el) => {
  const title = $(el).find(".titleline > a").text().trim().slice(0, 60)
  const score = $(el).next().find(".score").text().match(/\d+/)
  console.log(`${title.padEnd(60)} ${score?.[0] ?? "0"}`)
})
TS
```

## 数据校验

**首选：zod v4+** — TS 类型推导完美，生态最广（tRPC/Hono 集成），v4 性能大幅提升。
**次选：valibot**（极致轻量 tree-shaking）、arktype（TS 语法直接写 schema，运行时最快）
**避开：** yup（老旧）、class-validator（Angular 风格）

```bash
bun --silent run - << 'TS'
import { z } from "zod"
const Item = z.object({ id: z.number(), price: z.number(), category: z.string() })
const raw = [{ id: 1, price: 9.99, category: "food" }, { id: 2, price: "bad" }]
for (const r of raw) {
  const result = Item.safeParse(r)
  if (result.success) console.log(result.data)
  else console.log({ error: result.error.issues[0].message })
}
TS
```

## JSON / 数据格式

**首选：Bun 原生 JSON** — JSC 优化后性能已接近 orjson 级别，零依赖。
**次选：** 无必要第三方（除非极特殊场景）
**避开：** 无

```bash
bun --silent run - << 'TS'
const text = await Bun.file("data.jsonl").text()
const items = text.split("\n").filter(Boolean).map(l => JSON.parse(l))
const out = items.filter(i => i.price > 100).map(i => JSON.stringify(i)).join("\n")
await Bun.write("filtered.jsonl", out)
console.log(`${items.length} → ${items.filter(i => i.price > 100).length} records`)
TS
```

## 日期时间

**首选：date-fns v4** — 函数式、tree-shakable、ISO 8601 完整支持。Temporal（TC39 Stage 4）在 Bun 完整支持仍需 polyfill。
**次选：dayjs**（极轻 Moment 替代，插件丰富）、@js-temporal/polyfill（未来标准）
**避开：** moment（已死）、luxon（体积大）

```bash
bun --silent run - << 'TS'
import { format, addDays, parseISO } from "date-fns"
const dt = parseISO("2026-05-09T14:30:00Z")
console.log(format(dt, "yyyy-MM-dd HH:mm"))
console.log(format(addDays(dt, 7), "yyyy-MM-dd HH:mm"))
TS
```

## 文件格式

**首选：papaparse（CSV）+ xlsx/SheetJS（Excel）** — papaparse 流式最快；xlsx 格式支持最广。
**次选：exceljs**（富格式/流式写入场景）、csv-parse（Node 风格流式）
**避开：** node-xlsx（功能弱）

```bash
bun --silent run - << 'TS'
import Papa from "papaparse"
import { Database } from "bun:sqlite"
const csv = await Bun.file("data.csv").text()
const { data } = Papa.parse(csv, { header: true })
const db = new Database(":memory:")
db.run("CREATE TABLE IF NOT EXISTS data (id INTEGER, value TEXT)")
const stmt = db.prepare("INSERT INTO data VALUES (?, ?)")
for (const r of data) stmt.run(Number(r.id), String(r.value))
console.table(db.query("SELECT * FROM data LIMIT 5").all())
TS
```

## XML / RSS 解析

**首选：fast-xml-parser** — 零依赖、极快 XML 解析/构建，支持属性、CDATA、命名空间。
**次选：cheerio**（HTML 场景可兼用）
**避开：** xml2js（老旧回调风格）

```bash
bun --silent run - << 'TS'
import { XMLParser } from "fast-xml-parser"
const xml = await fetch("https://hnrss.org/newest").then(r => r.text())
const parser = new XMLParser()
const feed = parser.parse(xml)
for (const item of feed.rss.channel.item.slice(0, 10)) {
  console.log(item.title.slice(0, 60))
}
TS
```

## 文本处理 / 模糊搜索

**首选：fuse.js** — 轻量模糊搜索，无 native 依赖，阈值可调。
**次选：fuzzysort**（更极致速度场景）
**避开：** 无 direct rapidfuzz 对等物（native 问题）

```bash
bun --silent run - << 'TS'
import Fuse from "fuse.js"
const list = ["cafe", "coffee shop", "cafeteria", "restaurant", "bar"]
const fuse = new Fuse(list, { threshold: 0.3 })
for (const r of fuse.search("cafe")) {
  console.log(`${r.item} (score: ${r.score?.toFixed(2)})`)
}
TS
```

## 并发控制

**首选：p-limit** — 极轻量 promise 并发限制器，补 Bun.fetch 无内置队列的短板。
**次选：** 手写 semaphore
**避开：** bottleneck（过重）

```bash
bun --silent run - << 'TS'
import pLimit from "p-limit"
const limit = pLimit(5)
const urls = Array.from({ length: 20 }, (_, i) => `https://httpbin.org/get?id=${i}`)
const results = await Promise.all(urls.map(u => limit(async () => {
  const t = Date.now()
  try {
    const r = await fetch(u, { signal: AbortSignal.timeout(5000) })
    return { url: u, status: r.status, ms: Date.now() - t }
  } catch(e) { return { url: u, status: "ERR", ms: Date.now() - t } }
})))
console.table(results.slice(0, 10))
TS
```

## 加密 / JWT

**首选：Bun.crypto + jose** — Bun.crypto 内置 WebCrypto 现代 API；jose 是 2025 JWT 最佳实践（ESM 友好、算法全），取代 jsonwebtoken。
**次选：node:crypto**（兼容旧代码）
**避开：** jsonwebtoken（CommonJS + 安全隐患）、crypto-js（慢）

```bash
bun --silent run - << 'TS'
import * as jose from "jose"
const secret = new TextEncoder().encode("your-secret")
const token = await new jose.SignJWT({ user: "alice", role: "admin" })
  .setProtectedHeader({ alg: "HS256" })
  .setExpirationTime("1h")
  .sign(secret)
const { payload } = await jose.jwtVerify(token, secret)
console.log(payload)
TS
```

> 流式/增量哈希用 `new Bun.CryptoHasher("sha256").update(...).digest("hex")`，大文件分块 update 不必全读入内存。

## CLI 美化

**首选：picocolors + cli-table3 + ora** — picocolors 14x 小于 chalk；cli-table3 灵活表格；ora spinner。
**次选：chalk**（功能更全但体积大）、kleur（老轻量替代）
**避开：** colors.js（维护差）

```bash
bun --silent run - << 'TS'
import pc from "picocolors"
import Table from "cli-table3"
const table = new Table({ head: ["Name", pc.green("Status"), "Time"] })
table.push(["api-a", pc.green("OK"), "120ms"])
table.push(["api-b", pc.red("FAIL"), "5000ms"])
table.push(["api-c", pc.yellow("SLOW"), "800ms"])
console.log(table.toString())
TS
```

## 数据分析 / ETL

**首选：bun:sqlite + arquero** — bun:sqlite 性能 4-6x 优于 better-sqlite3；arquero 提供 pandas-like 操作。
**次选：danfojs**（pandas-like 但稍重）
**避开：** 纯数组手动处理

```bash
bun --silent run - << 'TS'
import { Database } from "bun:sqlite"
const db = new Database(":memory:")
db.run("CREATE TABLE sales (category TEXT, price REAL)")
db.run("INSERT INTO sales VALUES ('food', 9.99)")
db.run("INSERT INTO sales VALUES ('food', 12.50)")
db.run("INSERT INTO sales VALUES ('tech', 99.99)")
console.table(db.query("SELECT category, SUM(price) as total, COUNT(*) as cnt FROM sales GROUP BY category").all())
TS
```

## 图像处理（WASM）

**首选：wasm-vips** — libvips WASM 版，零 native addon，替代 sharp。支持缩放/裁剪/格式转换/元数据。
**次选：@aspect/photon**（Rust WASM 图像处理，滤镜/Blurhash）
**避开：** sharp（native libvips binding，heredoc 场景下安装可能失败）。Bun 无内置图像 API（`Bun.Image` 不存在），需图像处理一律走 WASM。

```bash
bun --silent run - << 'TS'
import Vips from "wasm-vips"
const vips = await Vips.create()
const image = vips.Image.newFromFile("photo.jpg")
const thumb = image.resize(0.5)
await Bun.write("thumb.webp", thumb.webpsaveBuffer())
console.log(`Resized: ${image.width}x${image.height} → ${thumb.width}x${thumb.height}`)
TS
```

## 人类可读格式化

**首选：humanize-duration + pretty-bytes** — 零配置把毫秒/字节转成人话。
**次选：** Intl API（stdlib，但格式化选项有限）

```bash
bun --silent run - << 'TS'
import humanizeDuration from "humanize-duration"
import prettyBytes from "pretty-bytes"
console.log(humanizeDuration(3661000))        // "1 hour 1 minute 1 second"
console.log(humanizeDuration(86400000 * 7))   // "7 days"
console.log(prettyBytes(1536000))              // "1.54 MB"
console.log(prettyBytes(1073741824))           // "1.07 GB"
TS
```

## Markdown 解析

**首选：markdown-it** — 零依赖，插件生态丰富（锚点、高亮、footnote）。
**次选：marked**（更快但插件少）
**避开：** remarkable（维护弱）

```bash
bun --silent run - << 'TS'
import MarkdownIt from "markdown-it"
const md = new MarkdownIt({ html: true, linkify: true })
const src = await Bun.file("README.md").text()
const html = md.render(src)
await Bun.write("README.html", html)
console.log("Rendered")
TS
```

## 压缩 / 归档

**首选：Bun 内置 `Bun.gzipSync` / `Bun.gunzipSync` / `Bun.deflateSync`** — 零依赖 gzip/deflate 压缩解压，处理单流数据最快。
**次选：fflate**（纯 JS，支持 zip 多文件归档 + 流式 API）
**避开：** archiver（依赖重，heredoc 场景多余）

```bash
bun --silent run - << 'TS'
import { Glob } from "bun"
const raw = await Bun.file("data.jsonl").arrayBuffer()
const gz = Bun.gzipSync(new Uint8Array(raw))
await Bun.write("data.jsonl.gz", gz)
const back = Bun.gunzipSync(gz)
console.log(`${raw.byteLength} → ${gz.length} → ${back.length}`)
TS
```

## 性能陷阱

| 陷阱 | 影响 | 对策 |
|------|------|------|
| auto-install 首次延迟 | 大包 5-30 秒 | 常用组合预热一次；后续秒开 |
| native addon | sharp/bcrypt/esbuild 安装失败 | 优先 Bun 内置 API 或 WASM 替代 |
| 大文件全加载 | 内存爆炸 | `Bun.file().stream()` 流式 + bun:sqlite 流式 ETL |
| 网络无超时 | heredoc 脚本卡死 | `AbortSignal.timeout(5000)` |
| Bun npm 解析偶发不稳 | 罕见 import 失败 | 优先 Bun 内置 API；重试即可 |
| TTY 交互库 | inquirer/prompts 卡死 | 不适用于 heredoc 场景 |
