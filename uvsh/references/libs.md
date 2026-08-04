# Python 顶级库详细参考

每个领域：第一选择 + 理由、第二选择 + 场景、过时/避开、heredoc 示例。

依赖：示例一律 `# /// script` 元数据（推荐）。极短一次性可用 `uv run -q --with pkg -`（见 SKILL.md）。

## HTTP / 网络请求

**首选：httpx** — 同步异步一体，HTTP/2，自动重试，Client 连接复用。FastAPI 生态默认选择。
**次选：requests**（纯同步简单脚本）、aiohttp（极致高并发异步）
**避开：** urllib3 底层、旧版 requests 无 HTTP/2

```bash
uv run -q - << 'PY'
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx"]
# ///
import httpx, asyncio
async def main():
    async with httpx.AsyncClient(timeout=10) as c:
        urls = ["https://api.github.com", "https://httpbin.org/json"]
        results = await asyncio.gather(*[c.get(u) for u in urls], return_exceptions=True)
        for r in results:
            if not isinstance(r, Exception): print(r.json())
asyncio.run(main())
PY
```

## HTML / XML 解析

**首选：selectolax** — 基于 Modest 引擎，CSS 选择器速度是 BeautifulSoup + lxml 的 3-5x。
**次选：lxml**（纯性能 XML/严格 HTML）、BeautifulSoup4（最宽容的脏 HTML 处理）
**避开：** 纯 html.parser（太慢）

```bash
uv run -q - << 'PY'
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx", "selectolax"]
# ///
from selectolax.parser import HTMLParser
import httpx
html = httpx.get("https://news.ycombinator.com/").text
tree = HTMLParser(html)
for row in tree.css(".athing")[:20]:
    title = row.css_first(".titleline > a").text()
    print(title[:60])
PY
```

## 数据校验

**首选：pydantic v2** — 类型校验 + JSON 序列化极快，FastAPI 生态事实标准。
**次选：msgspec**（纯 JSON 校验/解码吞吐量场景首选，比 pydantic 快数倍；不需要 pydantic 丰富校验生态时优先）、attrs（轻量类定义）
**避开：** pydantic v1、纯 dataclasses（无校验）

```bash
uv run -q - << 'PY'
# /// script
# requires-python = ">=3.12"
# dependencies = ["pydantic"]
# ///
from pydantic import BaseModel
class Item(BaseModel):
    id: int
    price: float
    category: str
raw = [{"id": 1, "price": 9.99, "category": "food"}, {"id": 2, "price": "bad"}]
for r in raw:
    try: print(Item.model_validate(r).model_dump_json())
    except Exception as e: print(f'{{"error": "{e}"}}')
PY
```

## 数据查询

**首选：duckdb + polars** — duckdb 直接 SQL 查 CSV/Parquet/JSON（零 ETL），polars 做内存 DataFrame 转换。
**次选：pandas**（生态巨大但速度差 5-30x）、numpy（纯数值数组）
**避开：** 旧 pandas 链式赋值、numpy matrix（已弃用）

```bash
uv run -q - << 'PY'
# /// script
# requires-python = ">=3.12"
# dependencies = ["duckdb"]
# ///
import duckdb
con = duckdb.connect(":memory:")
con.sql("SELECT * FROM 'https://example.com/data.csv' LIMIT 5").show()
con.sql("SELECT category, SUM(price) as total FROM read_csv_auto('sales*.csv') GROUP BY category ORDER BY total DESC").show()
PY
```

## CLI 输出结构化

**首选：jc** — 100+ CLI 命令输出转 JSON（ps、df、dig、netstat、lsblk、ifconfig、mount…）。Python 独有优势，无对等替代。
**次选：rich**（Table/Live/Markdown 渲染美化）、textual（完整 TUI）
**避开：** 纯 print + tabulate（丑且无结构化能力）

```bash
uv run -q - << 'PY'
# /// script
# requires-python = ">=3.12"
# dependencies = ["jc", "psutil", "rich"]
# ///
# ⚠️ jc 的 Windows tasklist parser 不可靠（jc 1.25.x），Windows 上建议用 psutil 替代
import jc, subprocess, platform
from rich.console import Console
from rich.table import Table
if platform.system() == "Windows":
    # Windows: 推荐用 psutil 替代 jc tasklist（见 uvsh 避坑清单）
    import psutil
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'memory_info']):
        try: procs.append({'image_name': p.info['name'], 'pid': str(p.info['pid']), 'mem_usage': p.info['memory_info'].rss})
        except: pass
    t = Table(title="Top 10 by MEM")
    for c in ["image_name", "pid", "mem_usage"]: t.add_column(c)
    for p in sorted(procs, key=lambda x: x.get('mem_usage', 0), reverse=True)[:10]:
        t.add_row(p['image_name'][:25], p['pid'], f"{p['mem_usage']:,}")
else:
    procs = jc.parse('ps', subprocess.getoutput('ps aux'), quiet=True)
    t = Table(title="Top 10 by MEM")
    for c in ["user", "pid", "mem_percent", "command"]: t.add_column(c)
    for p in sorted(procs, key=lambda x: float(x.get('mem_percent', 0)), reverse=True)[:10]:
        t.add_row(p['user'], p['pid'], f"{float(p['mem_percent']):.1f}", p['command'][:50])
Console().print(t)
PY
```

## JSON / 数据格式

**首选：orjson** — 序列化/反序列化全面领先，支持 dataclass/UUID/Numpy/JSONL。
**次选：msgspec**（结构化 JSON 模型）、ujson（兼容性好但已被 orjson 超越）
**避开：** 标准 json（慢）、simdjson Python 绑定（已过时）

```bash
uv run -q - << 'PY'
# /// script
# requires-python = ">=3.12"
# dependencies = ["orjson"]
# ///
import orjson
from pathlib import Path
lines = Path("data.jsonl").read_bytes()
data = [orjson.loads(line) for line in lines.splitlines()]
processed = [orjson.dumps({**d, "processed": True}) for d in data[:100]]
Path("out.jsonl").write_bytes(b"\n".join(processed))
PY
```

## 日期时间

**首选：zoneinfo + dateutil** — Python 3.11+ 内置 IANA 时区（无需 pytz），dateutil.parser 解析最强。
**次选：arrow**（人类友好 API）、pendulum（功能最全但维护稍弱）
**避开：** pytz（已被 zoneinfo 取代）

```bash
uv run -q - << 'PY'
# /// script
# requires-python = ">=3.12"
# dependencies = ["python-dateutil"]
# ///
from datetime import datetime
from zoneinfo import ZoneInfo
from dateutil.parser import parse
dt = parse("2026-05-09 14:30 PST")
dt_shanghai = dt.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo("Asia/Shanghai"))
print(f"UTC: {dt} → Shanghai: {dt_shanghai:%Y-%m-%d %H:%M}")
PY
```

## 文件格式

**首选：pymupdf (fitz) + openpyxl** — pymupdf 提取文本/图片/表格远快于 pypdf；openpyxl Excel 读写全能。
**次选：xlsxwriter**（纯写 + 图表场景更快）、pypdf（简单 PDF 合并/拆分）
**避开：** xlrd（已停止维护）

```bash
uv run -q - << 'PY'
# /// script
# requires-python = ">=3.12"
# dependencies = ["pymupdf", "openpyxl"]
# ///
import fitz, openpyxl
doc = fitz.open("report.pdf")
page = doc[0]
tabs = page.find_tables()
wb = openpyxl.Workbook(); ws = wb.active
for row in tabs[0].extract(): ws.append(row)
wb.save("output.xlsx")
print(f"已导出 {len(tabs[0].extract())} 行")
PY
```

## 文本处理

**首选：ftfy + charset-normalizer + rapidfuzz** — ftfy 一行修 Unicode 乱码，charset-normalizer 比 chardet 快 47x，rapidfuzz 是 fuzzywuzzy 现代 C++ 后端替代。
**次选：clean-text**（管道式清洗）、regex（增强正则，替代 re）
**避开：** fuzzywuzzy（慢 + GPL）

```bash
uv run -q - << 'PY'
# /// script
# requires-python = ">=3.12"
# dependencies = ["ftfy", "charset-normalizer", "rapidfuzz"]
# ///
from charset_normalizer import from_bytes
import ftfy
from rapidfuzz import process, fuzz
raw = open("messy.log", "rb").read()
enc = from_bytes(raw).best().encoding
text = ftfy.fix_text(raw.decode(enc or "utf-8"))
candidates = ["cafe", "coffee shop", "restaurant"]
match = process.extractOne(text[:50], candidates, scorer=fuzz.ratio)
print(match)
PY
```

## 系统/进程

**首选：psutil** — 跨平台进程/内存/CPU/磁盘监控，2025 仍是事实标准。
**次选：plumbum**（DSL 风格命令组合）
**避开：** 纯 os/subprocess 裸写（可读性差）

```bash
uv run -q - << 'PY'
# /// script
# requires-python = ">=3.12"
# dependencies = ["psutil"]
# ///
import psutil
for p in sorted(psutil.process_iter(['pid','name','cpu_percent','memory_percent']),
                key=lambda x: x.info.get('memory_percent', 0) or 0, reverse=True)[:15]:
    info = p.info
    print(f"{info['name'][:20]:20} PID:{info['pid']:>7} MEM:{(info['memory_percent'] or 0):5.1f}% CPU:{(info['cpu_percent'] or 0):5.1f}%")
PY
```

## DNS / 网络诊断

**首选：dnspython** — 完整 DNS 工具包，支持查询、动态更新、DNSSEC、区域传输。
**次选：** stdlib socket（简单查询）

```bash
uv run -q - << 'PY'
# /// script
# requires-python = ">=3.12"
# dependencies = ["dnspython"]
# ///
import dns.resolver
for qtype in ['A', 'AAAA', 'MX', 'NS', 'TXT']:
    try:
        answers = dns.resolver.resolve('google.com', qtype)
        for r in answers: print(f"{qtype:6} {r}")
    except Exception: pass
PY
```

## 加密/安全

**首选：cryptography + PyJWT** — cryptography 是官方推荐现代加密库；PyJWT 处理 JWT 最佳实践（RS256/ES256）。
**次选：pynacl**（NaCl 现代 API 更简洁）
**避开：** pycrypto（已弃用）、hashlib（功能有限但 stdlib 可用）

```bash
uv run -q - << 'PY'
# /// script
# requires-python = ">=3.12"
# dependencies = ["cryptography", "PyJWT"]
# ///
import jwt
from cryptography.fernet import Fernet
key = Fernet.generate_key()
f = Fernet(key)
token = jwt.encode({"user": "alice", "exp": 1740000000}, "secret", algorithm="HS256")
print(jwt.decode(token, "secret", algorithms=["HS256"]))
print(f.decrypt(f.encrypt(b"sensitive data")).decode())
PY
```

## 代码分析

**首选：libcst (LibCST)** — 保留注释/空格/格式的 Concrete Syntax Tree，heredoc 自动重构代码最强工具。
**次选：ast**（stdlib，丢弃格式但零依赖）

```bash
uv run -q - << 'PY'
# /// script
# requires-python = ">=3.12"
# dependencies = ["libcst"]
# ///
import libcst as cst
code = "x = 1\ny = 2\nprint(x + y)"
tree = cst.parse_module(code)
print(f"Statements: {len(tree.body)}")
for node in tree.body:
    if isinstance(node, cst.SimpleStatementLine):
        print(f"  Line: {node}")
PY
```

## 归档/压缩

**首选：py7zr** — 纯 Python 7z 压缩/解压/加密，补全 stdlib zipfile 短板。
**次选：** zipfile（stdlib，zip 格式）、tarfile（stdlib，tar.gz）

```bash
uv run -q - << 'PY'
# /// script
# requires-python = ">=3.12"
# dependencies = ["py7zr"]
# ///
import py7zr
with py7zr.SevenZipFile("backup.7z", mode="r", password="secret") as z:
    print(z.getnames())
    z.extractall(path="output/")
PY
```

## 图片元数据

**首选：ExifRead** — 零依赖 EXIF/GPS/XMP 提取，支持 JPEG/PNG/HEIC/RAW。
**次选：Pillow**（功能更全但更重）

```bash
uv run -q - << 'PY'
# /// script
# requires-python = ">=3.12"
# dependencies = ["ExifRead"]
# ///
from exifread import process_file
with open("photo.jpg", "rb") as f:
    tags = process_file(f)
for k, v in tags.items():
    if "GPS" in k or "Date" in k:
        print(f"{k}: {v}")
PY
```

## 轻量 NLP / 文本分析

**首选：TextBlob** — 情感分析、词性标注、名词短语提取，无需 GPU。
**次选：vaderSentiment**（纯情感分析，更轻更准，社交文本/表情符号友好；首次用 TextBlob 需下载 corpora 较慢）、NLTK（经典但稍重）
**避开：** spaCy / transformers（非 heredoc 场景，太重）

```bash
uv run -q - << 'PY'
# /// script
# requires-python = ">=3.12"
# dependencies = ["textblob"]
# ///
from textblob import TextBlob
text = "This product is amazing! Best purchase ever."
blob = TextBlob(text)
print(f"Polarity: {blob.sentiment.polarity:.2f}, Subjectivity: {blob.sentiment.subjectivity:.2f}")
print(f"Noun phrases: {blob.noun_phrases}")
PY
```

## 性能陷阱

| 陷阱 | 影响 | 对策 |
|------|------|------|
| auto-install 首次延迟 | 大包（pandas/pydantic）5-30 秒 | 常用组合预热一次；后续秒开 |
| 重型包初始化 | pytorch/playwright/opencv 启动慢甚至 OOM | 用轻量替代（httpx+selectolax、pymupdf、polars/duckdb） |
| 大文件全加载 | 内存爆炸 | duckdb 流式查询 / ijson 流式解析 / chunksize |
| 网络无超时 | heredoc 脚本卡死 | httpx: `timeout=10` |
| C 扩展安装失败 | 部分 Linux 环境缺编译工具 | 优先纯 Python 包；uv 的 wheel 分发通常已解决 |
