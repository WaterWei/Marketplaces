# Python 典型代码模式

依赖声明：示例一律用 PEP 723 `# /// script`（与 SKILL 主路径一致）。极短一次性仍可用 `uv run -q --with pkg -`，见 SKILL.md。

## 并发 HTTP + DuckDB 聚合

```bash
uv run -q - << 'PY'
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx", "duckdb"]
# ///
# task: 销售数据聚合分析
# step: 1. 查询销售 API 并用 DuckDB 按 category 聚合
import httpx, duckdb
resp = httpx.get("https://api.example.com/sales", timeout=10).json()
con = duckdb.connect(":memory:")
con.execute("CREATE TABLE sales (category TEXT, price REAL)")
for r in resp: con.execute("INSERT INTO sales VALUES (?, ?)", [r["category"], r["price"]])
con.sql("SELECT category, SUM(price) as total FROM sales GROUP BY category ORDER BY total DESC").show()
PY
```

## psutil 系统监控 + rich 表格

```bash
uv run -q - << 'PY'
# /// script
# requires-python = ">=3.12"
# dependencies = ["psutil", "rich"]
# ///
# task: 系统进程监控
# step: 1. 用 psutil 获取进程列表，rich 表格展示内存占用前 15
import psutil
from rich.console import Console
from rich.table import Table
procs = []
for p in psutil.process_iter(["pid", "name", "memory_percent", "cpu_percent"]):
    try: procs.append(p.info)
    except: pass
procs.sort(key=lambda x: x.get("memory_percent") or 0, reverse=True)
t = Table(title="Top 15 by MEM")
t.add_column("Name"); t.add_column("PID", justify="right"); t.add_column("MEM%", justify="right"); t.add_column("CPU%", justify="right")
for p in procs[:15]:
    mem, cpu = p.get("memory_percent") or 0, p.get("cpu_percent") or 0
    t.add_row((p.get("name") or "")[:25], str(p.get("pid")), f"{mem:.1f}", f"{cpu:.1f}")
Console().print(t)
PY
```

## PDF 表格提取 + Excel 输出

```bash
uv run -q - << 'PY'
# /// script
# requires-python = ">=3.12"
# dependencies = ["pymupdf", "openpyxl"]
# ///
# task: PDF 表格导出为 Excel
# step: 1. 从 report.pdf 首页提取表格并导出为 output.xlsx
import fitz, openpyxl
doc = fitz.open("report.pdf")
tabs = doc[0].find_tables()
wb = openpyxl.Workbook(); ws = wb.active
for row in tabs[0].extract(): ws.append(row)
wb.save("output.xlsx")
print(f"已导出 {len(tabs[0].extract())} 行")
PY
```

## 脏文件修复 + 编码检测

```bash
uv run -q - << 'PY'
# /// script
# requires-python = ">=3.12"
# dependencies = ["charset-normalizer", "ftfy"]
# ///
# task: 脏文件编码修复
# step: 1. 检测 messy.log 的编码并修复 Unicode 问题
from charset_normalizer import from_bytes
import ftfy
raw = open("messy.log", "rb").read()
enc = from_bytes(raw).best().encoding
text = ftfy.fix_text(raw.decode(enc or "utf-8"))
print(text[:500])
PY
```

## asyncio 并发批量（Semaphore 限流 + gather）

```bash
uv run -q - << 'PY'
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx"]
# ///
# task: 并发批量请求带并发限制
# step: 1. Semaphore(5) 限流 + gather，收集 {url,status,ms}，打印前 10
import asyncio, time, httpx
async def fetch(c, sem, url):
    async with sem:
        t = time.time()
        try:
            r = await c.get(url, timeout=10)
            return {"url": url, "status": r.status_code, "ms": round((time.time()-t)*1000)}
        except Exception:
            return {"url": url, "status": "ERR", "ms": round((time.time()-t)*1000)}
async def main():
    urls = ["https://httpbin.org/get", "https://api.github.com", "https://example.com"]
    sem = asyncio.Semaphore(5)
    async with httpx.AsyncClient() as c:
        results = await asyncio.gather(*[fetch(c, sem, u) for u in urls], return_exceptions=True)
    for r in results[:10]: print(r)
asyncio.run(main())
PY
```

## 流式迭代大 JSON（ijson，不全量加载）

```bash
uv run -q - << 'PY'
# /// script
# requires-python = ">=3.12"
# dependencies = ["ijson"]
# ///
# task: 流式统计大 JSON 数组
# step: 1. ijson.items 逐项迭代，不把整文件读入内存，只输出摘要
import ijson
count = hits = 0
with open("big.json", "rb") as f:
    for item in ijson.items(f, "item"):
        count += 1
        if item["price"] > 5000: hits += 1
print(f"count={count} hits={hits}")
PY
```

## 重试 / 指数退避

```bash
uv run -q - << 'PY'
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx"]
# ///
# task: 带指数退避的重试请求
# step: 1. 最多 3 次，httpx.HTTPError 捕获，退避 base*2^n + jitter，耗尽输出 error
import time, random, httpx
def get_with_retry(url, n=3, base=0.5):
    for attempt in range(n):
        try:
            return httpx.get(url, timeout=10).json()
        except httpx.HTTPError as e:
            if attempt == n - 1: return {"error": str(e)[:60]}
            time.sleep(base * 2 ** attempt + random.uniform(0, 0.3))
data = get_with_retry("https://httpbin.org/get")
print({"ok": "url" in data})
PY
```

## 可复用文件脚本（init / add / run / shebang）

```bash
uv init --script fetch_status.py --python 3.12
uv add --script fetch_status.py 'httpx'
```

```python
# fetch_status.py — uv add 后的形态示意
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "httpx>=0.28.1",
# ]
# ///
# task: URL 状态探测
# step: 1. GET 并打印 status
import httpx
print(httpx.get("https://example.com", timeout=10).status_code)
```

```bash
uv run -q fetch_status.py

# 或 shebang 后直接执行
# #!/usr/bin/env -S uv run --script
chmod +x fetch_status.py
./fetch_status.py
```
