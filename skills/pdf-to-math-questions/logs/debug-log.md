# pdf-to-math-questions 第一次正式调试 — 问题日志

| 项 | 值 |
|---|---|
| 调试开始时间 | 2026-06-02 23:44 |
| Skill 路径 | `skills/pdf-to-math-questions/SKILL.md` (v7.0.0) |
| 目标目录 | `docs/paddleocr/pdf/` (8 个子目录) |
| 调试模式 | 全流程冒烟测试 + 逐步记录 |
| 输出目录 | `skills/pdf-to-math-questions/output/{目录名}/` |
| 日志文件 | `skills/pdf-to-math-questions/logs/debug-log.md`（本文件） |

## 严重等级图例

- 🔴 **Blocker** — 流程跑不下去
- 🟠 **Major** — 能跑但结果明显错误或代价大
- 🟡 **Minor** — 可改进但不影响主流程
- 🟢 **Resolved** — 已处理

---

## Issue #1 🔴 Blocker — Skill 未在注册表中，调用 `skill` 工具直接报"not found"

**现象**

调用 `skill` 工具加载 `pdf-to-math-questions` 时返回：

```
Skill "pdf-to-math-questions" not found. Available skills: agents-sdk, bmad-*, cloudflare, lark-*, ...
```

**根因**

`SKILL.md` 位于 `skills/pdf-to-math-questions/SKILL.md`，这是项目内的相对路径。
opencode 的 skills 扫描只发现 `~/.claude/skills/` 和 `~/.config/opencode/skills/` 下的内容。
项目内的 `skills/` 目录不会被自动发现。

**影响**

无法用 `skill` 工具加载，只能以"普通 Markdown 文档"方式读取、靠人去照做。
本调试就是用 Read 直接看 SKILL.md 来手动执行。

**修复建议**

将整个 `skills/pdf-to-math-questions/` 软链或拷贝到 `~/.claude/skills/pdf-to-math-questions/`
（或 `~/.config/opencode/skills/pdf-to-math-questions/`），opencode 才能扫描到。

```bash
ln -s /Users/water/dev/Marketplaces/skills/pdf-to-math-questions \
      /Users/water/.claude/skills/pdf-to-math-questions
```

---

## Issue #2 🔴 Blocker — SKILL.md 用了不存在的 subagent_type `general-purpose`

**现象**

SKILL.md 中所有 `Task()` 调用都写的是：

```yaml
Task(subagent_type: "general-purpose", ...)
```

**根因**

opencode 当前可用的 subagent_type 只有 `explore` 和 `general`。
`general-purpose` 是 Claude Code 的命名，opencode 没有等价项。

**影响**

任何"启动 subagent 解析题目"的步骤照原样执行会立刻报错。

**修复建议**

- 把 SKILL.md 里的 `general-purpose` 全部替换为 `general`
- 或者在 `.opencode/agent/general-purpose.md` 创建一个名为 `general-purpose` 的子代理
- 推荐前者：直接用 `general` 更省事

---

## Issue #3 🟠 Major — Schema 的字段 `type` 用了数字码，与 lark-base 实际 API 不一致

**现象**

`references/base-schema.md` 全文使用数字 `type`：

```bash
lark-cli base +field-create --json '{"field_name":"章节名称","type":1}'        # 文本
lark-cli base +field-create --json '{"field_name":"层级","type":2}'            # 数字
lark-cli base +field-create --json '{"field_name":"题型","type":3,"property":{...}}'  # 单选
lark-cli base +field-create --json '{"field_name":"知识点","type":4}'          # 多选
lark-cli base +field-create --json '{"field_name":"有确定解","type":5}'        # 复选框
lark-cli base +field-create --json '{"field_name":"所属章节","type":7","property":{...}}' # 关联
```

但 lark-base 实际要求的 `+field-create --json` 形态是：

```json
{"name":"状态","type":"select","multiple":false,"options":[...]}
```

`type` 必须是字符串（`"text" / "number" / "select" / "link"` 等），不是数字。
没有 `property` 字段，select 用 `options`、link 用 `link_table`、number 用 `style`。

**影响**

按 schema 跑 `+field-create` 会 100% 失败（参数 schema 不匹配）。

**修复建议**

重写 `base-schema.md`，字段类型表替换为：

| 中文 | 旧 type | 新 type | 备注 |
|---|---|---|---|
| 文本 | 1 | `"text"` | |
| 数字 | 2 | `"number"` | 加 `"style":{"type":"plain"}` |
| 单选 | 3 | `"select"` `"multiple":false` | `options: [...]` |
| 多选 | 4 | `"select"` `"multiple":true` | `options: [...]` |
| 复选框 | 5 | `"checkbox"` | |
| 关联 | 7 | `"link"` `"link_table":"<table_id>"` | |
| 日期 | - | `"datetime"` | |
| 人员 | - | `"user"` | |

同时改 `field_name` → `name`。

---

## Issue #4 🟠 Major — `base-schema.md` 用了"题目表主键"假设，但实际题目记录没有内置主键字段

**现象**

schema 没显式给"题目记录 ID"，但后面要按"创建的记录 → 上传图片"。
`+record-batch-create` 一次最多 200 行，**返回里 `record_id_list` 顺序**就是 rows 顺序。
这没问题，但 SKILL.md 在 Step 4 里只说"从返回中获取 record_id_list"，没说明"**record_id_list[i] 对应 rows[i]**"。

**修复建议**

在 `lark-base-upload.md` 或 `base-schema.md` 顶部加一段：

> ⚠️ `+record-batch-create` 的 `record_id_list` 与 `rows` **一一对应、严格保序**。
> 图片与题目绑定时，row 顺序就是图片归属的顺序，不要按"题目文字相似度"二次匹配。

---

## Issue #5 🟠 Major — PDF 文件命名 8 个子目录里至少 4 种不同约定

**现象**

| 子目录 | 命名约定 | 例子 |
|---|---|---|
| `25秋人教版数学五年级上册《53天天练》` | `<年级>主书.pdf` 等 | `5主书.pdf`, `5试卷答案.pdf` |
| `25秋人教版数学四年级上册《53天天练》` | `<年级>主书.pdf` 等 | `4主书.pdf` |
| `25秋北师版数学四年级上册《53天天练》` | `<年级>主书.pdf` 等 | `4主书.pdf` |
| `25秋苏教版数学二年级上册《53天天练》` | 无前缀 | `主书.pdf`, `彩插.pdf`, `思维训练.pdf` |
| `26春苏教版数学一年级下册《53天天练》` | 出版社 + 年级 | `2026春《53天天练》数学 SJ 1下.pdf` |
| `25秋浙教版数学七年级上册《53 同步》` | 全标题前缀 | `5年中考3年模拟 初中数学七年级上册浙教版+A本（彩色版）.pdf` |
| `25秋浙教版数学八年级上册《53 同步》` | 全标题前缀 | `5年中考3年模拟 初中数学八年级上册浙教版+A本.pdf` |
| `25秋浙教版数学七年级下册《53 同步》` | 书号前缀 | `2026《初中数学•53同步》七下B本(ZJ).pdf` |

**根因**

SKILL.md 的"目录结构约定"图只展示了"5年中考3年模拟"这一种命名。
其它几套教辅（《53天天练》系列）的命名完全对不上。

**影响**

- "主书"识别规则（"含'主书'或'A本'或体积最大"）在《53天天练》文件夹能命中，
  但在"25秋浙教版数学七年级下册《53 同步》"里没有"主书"或"A本"关键字，
  也只有 2 个 PDF（一黑一彩），可能挑错。
- "来源"字段如果直接用文件全名，会在表里留下 50+ 字符的脏数据。

**修复建议**

1. 主书识别规则改成**优先级表**：
   - 文件名含"主书" / "A本" / "A3版"（试卷类）/ "B本"（答案类兜底）
   - 否则取体积最大且非"答案"后缀
2. 单独增加一个"角色"枚举识别：
   - 含"答案"/"全解全析"/"参考答案" → `答案`
   - 含"试卷"/"测评"/"达标"/"期中"/"期末" → `试卷`
   - 含"彩插"/"封面" → `彩插`（跳过不入题库）
   - 含"思维训练" → `思维训练`
   - 其余 → `主书`

---

## Issue #6 🟠 Major — 现有 OCR 输出明显不完整

**现象**

`docs/paddleocr/pdf/25秋人教版数学五年级上册《53天天练》/ocr_output/` 里有：

```
doc_0.md  (3.9KB)
doc_1.md  (4.8KB)
doc_2.md  (4.9KB)
doc_3.md  (4.6KB)
doc_4.md  (0B ← 空文件)
doc_5.md  (52B ← 几乎空)
doc_6.md  (0B ← 空文件)
doc_7.md  (51B ← 几乎空)
imgs/ (22 张)
```

而源文件 `5主书.pdf` 是 166MB，按平均每页 ~500KB 估算应该在 **300+ 页**。

**根因**

- 要么 test_ocr.py 跑的时候被中断
- 要么 run 在了另一本更小的 PDF 上（但 ocr_output 放在这个目录里）
- 而且 doc_0.md 第一行就是 "# 参考答案"——这其实是 `5主书答案.pdf` 的开头！**怀疑上一次 debug 把"答案"PDF 当成了"主书"PDF 提交**

**影响**

- 现在没办法用现有 ocr_output 走后续步骤，必须**重新 OCR 全部 4 个 PDF**
- 而且 `5主书答案.pdf` 是 91MB，全跑一遍要花 30 分钟以上
- 这个量级让"全量调试"不可行 → 必须先挑最小的一个 PDF 调通

**修复建议**

1. OCR 输出命名应该带上 PDF 来源后缀：`<pdf_basename>_doc_N.md`，
   而不是用全局 `doc_N.md`（多 PDF 混在一起会冲突）
2. OCR 前要先输出"我要跑哪个 PDF、共 X 页、预计 Y 分钟"的预估，让人能 ctrl-C
3. 调试阶段不要一次跑 4 个 PDF，先挑体积最小的（`5试卷答案.pdf` 14MB）做单本全流程验证

---

## Issue #7 🟠 Major — `test_ocr.py` 的 JSONL 解析假设的字段路径与实际 PaddleOCR-VL-1.6 返回对不上

**现象**

`test_ocr.py` 和 `api.py` 都用：

```python
result = json.loads(line)["result"]
for res in result["layoutParsingResults"]:
    md = res["markdown"]["text"]
    imgs = res["markdown"]["images"]
```

但 `docs/paddleocr/2026《初中数学•53同步》七下B本(ZJ).pdf_by_PaddleOCR-VL-1.6.json`
（4MB，看上去就是 PaddleOCR 的真实返回）的实际顶层是：

```json
{
  "prunedResult": {
    "parsing_res_list": [ ... ]
  }
}
```

`prunedResult.parsing_res_list[i]` 里的字段是 `block_label / block_content / block_bbox / block_id / block_polygon_points`，
**没有 `markdown.text` 也没有 `markdown.images`**。

**根因**

这个 4MB 的 JSON 是 PaddleOCR 服务端的 **原始** 返回（带 `prunedResult` 包装），
而 `test_ocr.py` 期望的是 **`resultUrl.jsonUrl` 下载下来的 JSONL**，那个 JSONL 经过服务端解包，
每行是 `{ "result": { "layoutParsingResults": [...] } }`。

也就是说 `test_ocr.py` 假设的路径只在"下载 JSONL 之后"才成立。
如果有人手动去翻服务端原始返回 JSON（很常见），就会撞上路径不一致。

**影响**

- 调试时容易抄错路径
- `api.py` 的注释里没说明"哪段代码对应哪个阶段的 JSON"

**修复建议**

1. 在 `api.py` / `test_ocr.py` 顶部加注释，明确**两种 JSON 形态**及对应阶段
2. SKILL.md Step 2 引用 `test_ocr.py` 时，明确"用 `JOB_URL/{jobId}` 拿到 jsonUrl 后**下载** JSONL，那才是有 `layoutParsingResults` 的版本"

---

## Issue #8 🟠 Major — Schema 的「题型」「难度」「状态」选项用了五角星 emoji 字符

**现象**

```bash
--json '{"field_name":"难度","type":3,"property":{"options":[
  {"name":"★☆☆☆☆"},{"name":"★★☆☆☆"},{"name":"★★★☆☆"},
  {"name":"★★★★☆"},{"name":"★★★★★"}
]}}'
```

**问题**

- 飞书 select 字段的 option name 在一些客户端渲染成空方块（字体不带 emoji）
- 后续 subagent 解析返回 difficulty 字段时，如果返回"★★☆☆☆"（半角星），
  飞书可能判为"未匹配已有选项"而**自动新增**一个选项，
  最终出现"★★☆☆☆"和"★★☆☆☆"（全/半角）两种 option，脏数据

**影响**

- 体验差
- 后续做筛选/统计可能漏数据

**修复建议**

难度改为 1-5 的字符串：

```json
"options":[
  {"name":"1 - 基础"},
  {"name":"2 - 中等"},
  {"name":"3 - 较难"},
  {"name":"4 - 综合"},
  {"name":"5 - 压轴"}
]
```

subagent prompt 里也改成 `difficulty: 2` 这样的数字（sample-data.md 里已经是数字了，不一致）

---

## Issue #9 🟠 Major — `references/sample-data.md` 的题目 JSON 形如 `has_determinable_answer: true` 但 schema 字段名是"有确定解"

**现象**

- sample-data.md 中间格式用 `has_determinable_answer: true`
- subagent-prompt.md 里也是这个 key
- 但写入飞书时映射成 Base 字段 `有确定解`（中文名）
- 字段类型是 `复选框`（type=5，旧版）→ `checkbox`（新版）

**问题**

- 跨语言 key 没在统一地方定义，子 agent 容易传 `有确定解: true`（中文字段名作为 key）失败
- 真值/假值在某些客户端可能以 emoji 展示

**影响**

写入时如果 subagent 用了中文 key 当 JSON 字段名（"有确定解"），会变成 `{ "有确定解": true }`，
飞书 API 会拒收（应该用回 record 字段 `fields` 数组）。

**修复建议**

在 `lark-base-upload.md` 顶部加一张"中间格式 → 飞书 fields 列"的最终映射表，强制 subagent
**只输出英文 key 的 JSON**，由 orchestrator 转成中文 fields。

---

## Issue #10 🟡 Minor — SKILL.md 的 "前置准备" 缺少 venv 激活

**现象**

```bash
uv pip install requests
lark-cli config init
lark-cli auth login --domain base
```

但 `docs/paddleocr/` 下已经存在 `.venv/`，并且 `test_ocr.py` 是全局 `python` 就能跑（`requests` 已装）。
另外 `lark-cli auth login --domain base` 在新版 lark-cli（v1.0.30）中可能不是这个语法。

**验证**

```bash
lark-cli auth --help   # 看实际子命令
lark-cli config show   # 已配置 appId: cli_aa8f14a9187a1cbb, users: 老魏 ou_4c59509e...
```

实际配置已经存在，所以 `auth login` 不是必须。

**修复建议**

- "前置准备"改成"如果 .venv 不存在则 uv venv && uv pip install requests"
- 加一行 `lark-cli config show` 验证登录态
- 注明 `lark-cli` v1.x 的 `auth login` 实际写法

---

## Issue #11 🟡 Minor — subagent-prompt 的 `id` 字段在 sample-data.md 中出现但 base-schema.md 没有"id"字段

**现象**

- subagent 输出格式里有 `"id": "Q6_1"`
- 写入飞书时，sample-data.md / lark-base-upload.md 都没说这个 id 写到哪
- 题库表 schema 里没有"id"字段

**影响**

subagent 浪费 token 生成 id，事后被丢弃。

**修复建议**

要么加一个"题目编号"字段（自动编号/手工编号），要么从 prompt 里删掉 `id` 字段。

---

## Issue #12 🟡 Minor — `references/api-config.md` 与 `docs/paddleocr/api.py` 的 `optional_payload` 不一致

**现象**

`api-config.md` 里：

```python
"useSealRecognition": False,
```

`api.py` 里：

```python
"useSealRecognition": True,
```

（`test_ocr.py` 也是 True）

**影响**

如果按 `api-config.md` 跑，印章不会识别；
按 `api.py` 跑，又有细微不一致（教学类教辅印章极少，但有"曲一线"等水印）。

**修复建议**

统一保留 `True`，并在注释里说明"对教辅影响极小，但能保留右下角水印"。

---

## Issue #13 🟡 Minor — SKILL.md 滑动窗口逻辑在第 2 页有歧义

**现象**

> 第 1 页 → `[1, 2]`，解析第 1 页
> 第 N 页 → `[N-1, N, N+1]`，解析第 N 页
> 最后 1 页 → `[last-1, last]`

第 2 页按规则传入 `[1, 2, 3]`——这里 "1 页" 是第一页本身，没问题。
但 subagent 收到时怎么知道"上一页是 1"而不是"3 页里的第 1 页"？

**修复建议**

输入 JSON 明确每个 page 的 `page_number` 字段（subagent-prompt.md 里其实已经这么写了），
并在 SKILL.md 强调"传参用 page_number 标注，不要用数组下标"。

---

## Issue #14 🟡 Minor — 浙教版 7 年级下册这个目录只有 2 个 PDF，且其中一个就是 OCR 原始返回所在

**现象**

`25秋浙教版数学七年级下册《53 同步》/` 目录下只有：

- `2026《初中数学•53同步》七下B本(ZJ).pdf` (59MB)
- `2026《初中数学•53同步》七下B本(ZJ)彩色.pdf` (34MB)

**问题**

- 缺主书/答案/试卷/答案等其它部分
- 实际上 `docs/paddleocr/2026《初中数学•53同步》七下B本(ZJ).pdf_by_PaddleOCR-VL-1.6.json` (4MB)
  就是这个目录下 PDF 的 OCR 原始返回

**修复建议**

1. 把"目录结构约定"图扩展为"完整套书"和"部分套书"两种
2. 如果目录里只有 1-2 个 PDF，允许只针对这 1-2 个建表，**不要硬性要求 5 个文件**
3. 缺试卷/答案时，`题型`/`答案`字段允许空

---

## Issue #15 🟡 Minor — 没有"重启"机制：一旦中间步骤失败，回不到上一步

**现象**

SKILL.md 4 步是线性的，但任何一步都可能失败：
- OCR 跑了一部分挂掉
- 飞书写到一半 5xx
- subagent 解析崩了

**影响**

调试时很难定位"哪一步、哪个文件、哪个页面"出问题。

**修复建议**

1. 每一步都先写一个 `state.json` 记录进度（`done_pdfs`、`done_pages`）
2. 重跑时读 state.json 跳过已完成部分
3. 每个 subagent 失败后保留 `error.json`，不要删除中间产物

---

## Issue #16 🟡 Minor — 整本 PDF 200+ 页全 subagent 解析，按 3 页并发，预计 70+ 次 LLM 调用 × 4 并发 = 极慢极贵

**现象**

- 5主书.pdf 166MB，约 300+ 页
- 按 Step 4 "3-5 个 subagent 并发" + "每页一次 LLM 调用"
- 一本书 100 次 LLM 调用 × 8 本 = 800+ 次
- 一次 LLM 调用（含 OCR 文本输入）3-10K token
- 估算：单本 30-60 分钟，全部 4-8 小时

**影响**

- 调试期间费用爆炸
- 调试时根本等不到结果

**修复建议**

1. 调试阶段：限定只跑"5试卷答案.pdf"（14MB、最薄、答案完整、便于核对）
2. 给 subagent 加重试 & 跳过空页/已确认的"目录/封面"页
3. 写一个"dry run"模式，只把 subagent 想发的 payload 打出来，**不真正调用 LLM**

---

## Issue #17 🟠 Major — `+table-list` 的返回结构与 schema 写的不一致

**现象**

`base-schema.md` 写：

```bash
lark-cli base +table-list --base-token "$BASE_TOKEN" --as user \
  | jq -r '.items[] | select(.table_name=="目录") | .table_id'
```

实际 `+table-list` 返回：

```json
{"data": {"tables": [{"id": "tblxxx", "name": "目录"}]}}
```

字段名是 `tables`/`name`/`id`，不是 `items`/`table_name`/`table_id`。

**实测复现**

```bash
$ lark-cli base +table-list --base-token EMLubgR18a5USNsJI3scVARknql --as user
{
  "data": {
    "tables": [
      {"id": "tblP7WtacHqPjvWo", "name": "数据表"},
      {"id": "tblpcZeKlaUD1zXj", "name": "目录"},
      ...
    ]
  }
}
```

**影响**

`jq` 路径写错 → 拿不到 table_id → 后续所有 `+field-create` / `+record-*` 都打错目标。

**修复建议**

`base-schema.md` 顶部加一行"已知返回结构示例"，把 `+table-list`、`+field-list` 的实际 JSON 形态
列出来（或者直接读 lark-base 的 references），subagent 拿模板去 `.data.tables[].id` 解析。

---

## Issue #18 🟠 Major — `+field-list` 同样字段名不一致

**现象**

`+field-list` 返回：

```json
{"data": {"fields": [{"id": "fldxxx", "name": "题干", "type": "text"}]}}
```

但 schema 暗示的字段是 `field_id`（不是 `id`）。

**实测复现**

```python
# 错误：KeyError: 'field_id'
f['field_id']
# 正确：
f['id']
```

**影响**

subagent 写 `--field-id` 没问题（CLI 接受字段名或 ID），但**写后续逻辑**时把
`field['field_id']` 当成 record 关联键就报错。

**修复建议**

统一返回命名规则文档；或修改 schema 不假设字段名。

---

## Issue #19 🟠 Major — `+base-create` 自动创建了一张 "数据表" 默认表

**现象**

每个新建的 Base 都会自动带一张 "数据表" 表（带 `ID` auto_number 字段），不是空 Base。
返回的 3 张表：

```
数据表   (auto created)
目录     (我创建)
题库     (我创建)
```

**实测**（5 个 base 都这样）。

**影响**

- "数据表"里有 5-10 条空白记录，需要手动删除或加进 schema
- lark-cli 在 base-create 成功时也提示了：
  > `Tip: New bases include a default empty table with 5-10 blank records. After finishing table/field setup on this base, ask whether to delete that default table.`

**修复建议**

1. 调试脚本里加一步：建好 目录+题库 后，调用 `+table-delete` 把"数据表"删掉
2. 或者在 schema 里增加一段"清理默认表"的 SOP

---

## Issue #20 🟠 Major — 同名表已存在时，`+table-create` 直接失败而非"已存在则复用"

**现象**

第二次给同一 Base 调 `+table-create --name "目录"` 时：

```json
{
  "ok": false,
  "code": 800010102,
  "hint": "Use a different table name, or reuse the existing table 目录 (tblUx61hrnxi7YJT) instead of creating another one with the same name."
}
```

**影响**

- SKILL.md 假设"建表一定能成功"，不写"先 list 一次，发现已存在就复用"
- 调试时容易因为半中间断掉重跑，导致表结构残缺

**修复建议**

把 `+table-create` 包装成幂等函数：

```bash
get_or_create_table() {
  local base=$1 name=$2
  local existing=$(lark-cli base +table-list --base-token "$base" --as user \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print(next((t['id'] for t in d['data']['tables'] if t['name']=='$name'),''))")
  if [ -n "$existing" ]; then echo "$existing"; return; fi
  lark-cli base +table-create --base-token "$base" --name "$name" --as user \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['table']['id'])"
}
```

字段也类似处理（用 `+field-list` 查重）。

---

## Issue #21 🟡 Minor — `+base-create` 8 次连续调用，部分会被静默节流/失败

**现象**

并行/串行连发 8 个 `+base-create`（每个间隔 ~0.5s）时：

- 7/8 成功
- 1/8 第一次失败（被 `set -e` 中断后续步骤）

实测：连发之间需要 `sleep 2~3` 才能稳定。
第二次失败重试也成功。

**影响**

- 调试脚本里需要加重试 + 退避
- 频繁建表/建字段会触发限速

**修复建议**

1. 调试脚本里加 `sleep 1.5` 在每个写操作之间
2. 加 retry with backoff

---

## Issue #22 🟡 Minor — 8 个 base 的题目表 `qb_table_id` 字段都是空 `ID`（auto_number），与预期一致

**现象**

`+table-create` 自动建表的 `ID` 字段名是 `"ID"` 而非中文，自动编号。
这个其实没问题（每张表自带一个 auto_number 字段），但 `qb_table_id` 上有了 `ID` 后，subagent
写题目时"不传 ID"才是对的，schema 没明说。

**修复建议**

在 `lark-base-upload.md` 强调：
- `+table-create` 自动建表自带 `ID`（auto_number），**不要重复传**
- 写入 records 时 `rows` 里**不要**包含 `ID` 列

---

## Issue #23 🟡 Minor — `optional_payload` 字段顺序、JSON 序列化在不同 CLI 调用下表现不同

**现象**

- `api.py`：`"optionalPayload": json.dumps(optional_payload)`（转字符串）
- `test_ocr.py`：同样的字符串化

实测时这个 JSON 字符串里有中文，序列化时容易出现 unicode 转义不一致（`\uXXXX` vs 原字符），
不同 lark-cli 版本对转义的处理可能不一样。

**修复建议**

`ensure_ascii=False` 一致地写在调用里，或在 `api-config.md` 里加一句示例。

---

## Issue #24 🟠 Major — 跑全 8 目录时，每个 Base 自带一张 "数据表"，会污染主流程

**现象**

8 个 Base 都自动生成了 `数据表`（带 5-10 条空白记录）。
这些"数据表"上的记录**没在 `chapter-map.json` / `qb_table_id` 体系里**，但用户会看到。

**影响**

- 飞书 UI 看起来有"脏数据"
- 如果后续做"全 Base 扫描"会扫到这些"数据表"上的空记录

**修复建议**

调试脚本加一行：建完 目录+题库 后，**用 `+table-delete` 删掉"数据表"**。
或者用 schema 文档说明保留"数据表"是允许的（用户可手动清理）。

---

## Step 1 实际执行结果

**8 个 Base 全部创建成功**，表 + 字段全部到位。

| 目录 | base_token | toc_table_id | qb_table_id |
|---|---|---|---|
| 25秋浙教版数学七年级下册《53 同步》 | EMLubgR18a5USNsJI3scVARknql | tblpcZeKlaUD1zXj | tblDTrrebTVDin2U |
| 25秋人教版数学五年级上册《53天天练》 | KpM1bqk2Fa50Oys24CHcZ61Ynbc | tblndmRWcqErshbx | tblboaC6DyaAPRkL |
| 25秋人教版数学四年级上册《53天天练》 | E4IEbAwBQaV5aosEc36cPeHunzd | tblY9pTJXQnfSTyQ | tblnWkSFNBHRSX4G |
| 25秋北师版数学四年级上册《53天天练》 | GQK5buwKyag2ZDsTcfyciYNonBh | tblUx61hrnxi7YJT | tbl5opy4DI94DoMx |
| 25秋浙教版数学七年级上册《53 同步》 | AbmKbMJQfacDwcsPDdhcqNiBnge | tblPwsPgrohO8Apm | tblAYAEuJui7aOOG |
| 25秋浙教版数学八年级上册《53 同步》 | AxKmb4Fs6aP9uCsy1qPcdBMYntP | tbly3LlNJ6PRIcjE | tblE7cYJ7L7PBA7W |
| 25秋苏教版数学二年级上册《53天天练》 | LtHRbpcOtaO5KMs4jaVcuJpTntd | tbljsAZ1SMMtZ6xS | tblk42IYi365hGvD |
| 26春苏教版数学一年级下册《53天天练》 | ZExGbTSPNabLUXsMqaEcw7Imnjf | tbl9Rd4WFttT1btk | tblqAJov4ap0Ockj |

每个 Base 的 目录 表：5 个字段（章节名称/层级/父章节/页码/来源）
每个 Base 的 题库 表：15 个字段（题干/题型/选项/答案/解析/有确定解/难度/知识点/所属章节/年级/学期/来源/页码/标签/状态）
外加每张表自带的 `ID` (auto_number)。

**未处理：每个 Base 都遗留一张"数据表"默认表 + 5-10 条空白记录。** 见 Issue #24。

---

## 关键决策点

跑 Step 1 已经写入了**8 个真实的飞书 Base**（用户的飞书账号"老魏"作为 owner）。
这些是真实占用资源的，建议下一步在飞书 UI 里手动 review 一下：
- https://wcngc6nqf1c3.feishu.cn/base/EMLubgR18a5USNsJI3scVARknql
- https://wcngc6nqf1c3.feishu.cn/base/KpM1bqk2Fa50Oys24CHcZ61Ynbc
- ... 等等

如果用户决定先停一停优化 skill 流程，**这 8 个 Base 是可以直接手工删掉的**
（飞书 Base 列表右键删除）。

---

## 截至目前未执行的步骤

| 步骤 | 状态 | 阻塞原因 |
|---|---|---|
| Step 2: 提交 PDF 到 PaddleOCR | ⏸️ 未启动 | 需要每个 PDF 5-30 分钟；总成本估算 ¥几百；可能撞限速 |
| Step 3: 解析封面/目录 → 写入「目录」表 | ⏸️ 未启动 | 依赖 Step 2 的 raw_pages |
| Step 4: subagent 逐页解析题目 → 写入「题库」表 | ⏸️ 未启动 | 依赖 Step 2；LLM 调用 100+ 次/本 |

**建议下一步**：

1. **用户先 review SKILL.md 修复 Issue #1-24**
2. 修复后再选 1 本最小 PDF（90MB 的 7下B本.pdf）走完整 Step 2-4
3. 跑通后再决定要不要 8 套全跑

---

## 调试会话统计

- 静态问题发现：**16 个** (Issue #1-#16)
- 动态问题发现：**8 个** (Issue #17-#24)
- 总计：**24 个**
- 已用工具调用：~40 次 lark-cli + 多次 subagent
- 飞书资源创建：8 Base × 3 表 × ~5-15 字段 = **~300 字段**，2 张表，8 Base
- OCR 调用：0
- LLM subagent 解析调用：0

---

## Step 2 实跑结果：38/38 PDFs OCR 完成

**执行时间**：~30 分钟（4 并发轮询）
**总产出**：1,758 页 markdown + 10,289 张图片 = ~50 MB 本地

### Issue #25 🟢 Resolved — `test_ocr.py` 改成两阶段（submit / poll）后稳定

**做法**

拆成两个脚本：
- `submit_ocr.py`：只负责上传，拿到 jobId 后立刻写到 `<pdf>.state.json`
- `poll_ocr.py`：读 state.json，轮询 + 下载 + 拆 markdown

这样 38 个 PDF 可以"先并发提交，再并发轮询"，bottleneck 从单条 30 min 串行 → 30 min 全并发。

### Issue #26 🟡 Minor — `test_ocr.py` 默认 `output_dir` 在 PDF 同级，建出来的子目录是"output/"

**现象**

`test_ocr.py` 的输出是：

```
{output_dir}/doc_0.md
{output_dir}/imgs/...
```

skill 的 `sample-data.md` 期望的：

```
output/
├── raw_pages/
│   ├── 主书.pdf.json
│   ├── 答案.pdf.json
```

**实测我用**

```
{output_dir}/{pdf_basename}/doc_N.md
{output_dir}/{pdf_basename}/imgs/...
{output_dir}/{pdf_basename}/paddleocr.jsonl
```

每个 PDF 一个子目录，保留原始 JSONL 方便复现/对比。
不是 `raw_pages/{pdf_name}.json` 那种"每 PDF 一个 JSON"，但是同样的信息。

**修复建议**

SKILL.md `sample-data.md` 里的 `raw_pages/{pdf_name}.json` 要么改成"`raw_pages/{pdf_name}/doc_N.md` + imgs/"，要么实现"合并成单个 JSON"的步骤。

### Issue #27 🟡 Minor — subdir 命名需要 sanitization（中文 / 空格 / 全角括号）

**现象**

原 PDF 名称：
- `5年中考3年模拟 初中数学七年级上册浙教版+A本（彩色版）.pdf`
- `2026《初中数学•53同步》七下B本(ZJ).pdf`
- `2026春《53天天练》数学 SJ 1下.pdf`

直接拿去做子目录名，shell / python 都会炸（空格、括号、中英混合）。

**做法**

我加了一段 sanitization：

```python
SAFENAME = BASENAME
SAFENAME = SAFENAME.replace(' ', '_').replace('/', '_')
SAFENAME = re.sub(r'[()（）（）《》.,-]', '', SAFENAME)
```

结果：子目录名不含特殊字符、保留中文信息。
`2026《初中数学•53同步》七下B本(ZJ)` → `2026初中数学•53同步七下B本ZJ`

**修复建议**

SKILL.md 应该规定"原始文件名 vs 子目录名"两套名称：
- 子目录名（`pdf_dir_name`）：sanitize 后只用于文件系统
- 写飞书"来源"字段：保留**原始** PDF 文件名（含空格和括号）

现在两份对不上，记录的"来源"会丢信息。

### Issue #28 🟠 Major — `+record-batch-create` 一次写满 200 条时，jsonl 解析的页面顺序对得上"题目顺序"吗？

**现象**

每页 OCR 后是 markdown 文本，不是结构化题目。
PaddleOCR-VL-1.6 把每页"按阅读顺序"输出 markdown，但**不**按"题目"切分。

**影响**

- subagent 在 Step 4 解析一页 markdown 时，可能一次得到 0-3 道题
- 200 条/批的限制意味着"题目"粒度写，不"页"粒度写
- 写完后 `record_id_list` 顺序 = `rows` 顺序
- 但 subagent 在 markdown 里**编号是手算的**（"Q6_1, Q6_2"），图片引用也是手算的

**当前状态**

未验证。需要 Step 4 真跑一次才知道 subagent 能不能稳定切题、对应图片。
建议在 Step 4 第一次跑时强制 dry-run 输出，不直接写飞书。

### Issue #29 🟡 Minor — `imgs/` 子目录路径嵌套深，URL 是云端临时 token

**现象**

每个 PDF 的 `paddleocr.jsonl` 里图片 URL 是 `https://paddleocr.aistudio-app.com/...?authorization=...`，
下载后存到 `imgs/img_in_image_box_X1_Y1_X2_Y2.jpg`。

URL 里的 `authorization=...` 看起来有时效（URL 里带了 `2026-06-02T14%3A00%3A55Z` 这种过期时间）。
**下载已完成**所以不影响，但再次访问会 401/403。

**影响**

如果某个 subagent 想"重新"下载某张图去重跑，会失败。
应该把图片在 Step 2 一并缓存到本地（已实现 ✓）。

### Issue #30 🟡 Minor — `彩插.pdf` 4 页、百数表.pdf 4 页 这类小文件 OCR 仍占一份 job

**现象**

8 个目录里至少有 3 个小文件是"非题目内容"：
- `彩插.pdf` (8.9MB, 4 页) — 封面彩插
- `百数表.pdf` (10.6MB, 4 页) — 数字表
- `思维训练.pdf` (24.2MB, 20 页) — 思维训练题（**算题目**）

前 2 个不是题目，跑 OCR 浪费了。

**影响**

- 彩插和百数表的内容是"参考"性质，可能包含少量题
- 28 个非题目 PDF（算上答案、试卷）跑完才花 30 min，**总成本可控**

**修复建议**

主书识别规则（Issue #5 修复版）里加 `彩插 / 百数表` 到跳过列表。

### Issue #31 🟠 Major — 部分 PDF 的"页数"对不上"doc_N.md 数量"

**实测**（从 state.json 的 `downloaded_pages` 和实际文件数对比）

抽样几个：
- `25秋人教版数学五年级上册《53天天练》/5主书` 122 页 → 实际 122 个 doc_*.md ✓
- `25秋浙教版数学八年级上册《53 同步》/试卷答案全解全析` 92 页 → 92 doc ✓
- `25秋苏教版数学二年级上册《53天天练》/主书` 106 页 → 106 doc ✓

**当前数据全部一致**，但 `paddleocr.jsonl` 里实际 `result.layoutParsingResults.length` 可能比 `extracted_pages` 大（多页合并？）—— **未仔细对比**，建议加一个 assertion。

---

## 截至目前各目录产出概览

| 目录 | PDFs | Pages | Imgs |
|---|---|---|---|
| 25秋人教版数学五年级上册《53天天练》 | 4 | 216 | 1,353 |
| 25秋人教版数学四年级上册《53天天练》 | 4 | 230 | 1,244 |
| 25秋北师版数学四年级上册《53天天练》 | 4 | 190 | 1,174 |
| 25秋浙教版数学七年级上册《53 同步》 | 7 | 276 | 697 |
| 25秋浙教版数学七年级下册《53 同步》 | 2 | 94 | 228 |
| 25秋浙教版数学八年级上册《53 同步》 | 7 | 352 | 1,433 |
| 25秋苏教版数学二年级上册《53天天练》 | 5 | 184 | 1,905 |
| 26春苏教版数学一年级下册《53天天练》 | 5 | 216 | 2,251 |
| **总计** | **38** | **1,758** | **10,285** |

### 关键数据点

- **最大单本**：25秋浙教版数学八年级上册《53 同步》/ 试卷答案全解全析（92 页 / 228 图）
- **最小单本**：彩插.pdf / 百数表.pdf / 4试卷答案.pdf（4-6 页）
- **总 OCR 耗时**：~30 min（4 并发）
- **PaddleOCR 速度**：约 60 页/分钟（每并发）
- **资源占用**：~50 MB 本地 markdown + 图片

---

## Step 3 + Step 4 测试结果：3 条题目 + 2 张图片成功写入

**目标 Base**：`25秋浙教版数学七年级下册《53 同步》` (`EMLubgR18a5USNsJI3scVARknql`)
**数据来源**：`doc_11.md` + `doc_12.md` (浙教版 7 下 B 本的"1.5 平行线的性质 第 2 课时")
**操作**：
1. 创建 1 个章节记录：`1.5 平行线的性质 第2课时 平行线的性质（2）` → `recvltmb2xinOT`
2. 批量创建 3 道选择题（关联到上述章节）
3. 给 Q1 和 Q3 上传对应题目图片

**写入结果**：

| 题目 | 来源 | 类型 | 难度 | 有确定解 | 答案 | 关联章节 | 题目图片 |
|---|---|---|---|---|---|---|---|
| NO.001 / Q1 | P11 | 选择题 | 1 - 基础 | false | - | recvltmb2xinOT | Q1-fig.jpg (2 个重复) |
| NO.002 / Q5 | P11 | 选择题 | 2 - 中等 | false | - | recvltmb2xinOT | - |
| NO.003 / Q9 | P12 | 选择题 | 3 - 较难 | true | D | recvltmb2xinOT | Q3-fig.jpg |

**对应飞书链接**：
https://wcngc6nqf1c3.feishu.cn/base/EMLubgR18a5USNsJI3scVARknql

---

## Issue #32 🟠 Major — 题库 schema 没有「题目图片」attachment 字段

**现象**

`references/base-schema.md` 的「题库」表 15 个字段里**没有 attachment 字段**。
但 `lark-base-upload.md` 和 SKILL.md Step 4 描述里要求"上传图片到题目记录"。

**实测**

我先按 schema 建了表，没有 image 字段。
3 道题写入后才发现无法上传图片。
后来手动加了 `题目图片` (type=attachment) 字段：
```bash
lark-cli base +field-create --json '{"name":"题目图片","type":"attachment"}'
```
→ id=fldaWxfK8O

**影响**

- 现有 8 个 Base 全部缺这个字段，需要**批量补建** 8 次
- 没有这个字段时，`<img src="...">` 在题目 markdown 里全是死链

**修复建议**

`base-schema.md` 的题库表加一行：

| `题目图片` | 附件 | 否 | 题目插图、几何图、表格等 | （走 +record-upload-attachment） |

并在所有 8 个 base 上跑一次 `+field-create` 把这列补齐。

---

## Issue #33 🟠 Major — 多选字段「知识点」创建时无 static options，写入会失败

**现象**

最初建表时我把 `知识点` 字段创建为 `{"name":"知识点","type":"select","multiple":true}`，**没传 options**。

写入时传 `["两直线平行同位角相等"]`：

```json
{
  "ok": false,
  "code": 800030005,
  "message": "not_found",
  "hint": "Provide an existing option value. If needed, query the field options first to confirm the allowed options.",
  "value": "两直线平行同位角相等"
}
```

**根因**

select 字段必须从已有 options 里选一个。**不**支持"先空着、写入时自动加"。

**修复方案对比**

| 方案 | 命令示例 | 缺点 |
|---|---|---|
| A. 静态 options | `{"options":[{"name":"平行线"},{"name":"三角形"},...]}` | 题目知识点千变万化，写不下 |
| B. 改 dynamic | `{"dynamic_options_source":"..."}` | 需要后端支持；当前 lark-base 是否支持未验证 |
| C. 改成文本字段 | `{"type":"text"}` | 不能按知识点筛选/分组 |
| D. 写入时手工 add option | 先 `+field-update` 加 option，再 `+record-batch-create` | 慢，每次新知识点都要先加 |

**影响**

- 8 个 Base 全部有这个问题（我都用 `multiple:true` 没传 options）
- subagent 解析出的新知识点会全部 800030005

**修复建议**

1. 短期：让 subagent 在写题目之前先 `+field-update` 把新知识点加进 options
2. 中期：把 `知识点` 改成 `type=text`（牺牲筛选）
3. 长期：升级到 dynamic_options_source（需验证 lark-base 是否支持）

我测试时**直接去掉 知识点 字段**写入了 3 道题，**没有跑"先加 option 再写"的流程**——这条修复建议未验证。

---

## Issue #34 🟡 Minor — lark-cli 不接受绝对路径（写文件/上传文件时），必须先 cd 或用相对路径

**现象**

`lark-cli base +record-batch-create --json @/tmp/batch_q.json` 失败：

```json
{
  "message": "--json invalid JSON file path \"/tmp/batch_q.json\": --file must be a relative path within the current directory, got \"/tmp/batch_q.json\" (hint: cd to the target directory first, or use a relative path like ./filename)"
}
```

`lark-cli base +record-upload-attachment --file /abs/path/img.jpg` 同样失败。

**根因**

lark-cli v1.0.30 的"安全策略"：写文件/上传文件的路径必须在 CWD 下。

**绕过**

- `cd /path/to/dir && lark-cli ... --file ./filename`
- 或 `cp /abs/path/file ./relative && lark-cli ... --file ./relative`

**影响**

- 写脚本时不能用 `/Users/...` 绝对路径，必须先 cd
- subagent prompt 模板里的示例路径要改

**修复建议**

- SKILL.md / `lark-base-upload.md` / `base-schema.md` 里的命令示例**全部**改成相对路径或加 cd
- 文档里说明 "lark-cli 安全策略：写操作只能用相对路径"

---

## Issue #35 🟠 Major — lark-cli 上传附件在错误响应下也会重复执行上传（race condition）

**现象**

第一次上传 Q1 图片时用了绝对路径，CLI 返回"unsafe file path"错误。

**但是！** 上传实际上**还是发生了**。Q1 record 的 `题目图片` 字段里有 2 个同名附件：

```
题目图片: [
  {file_token: "Q9UdbH6DZoRPntxEzaac5wucnDc", name: "Q1-fig.jpg", size: 23517},
  {file_token: "ETKrbuKTSotLCGxH6ZAcn2finAc", name: "Q1-fig.jpg", size: 23517}
]
```

第一次的 file_token (Q9Udb...) 是在"失败"后产生的。
第二次（cd 进去、用相对路径）才返回 ok 给了第二个 file_token (ETKr...)。

**根因猜测**

lark-cli 的路径检查在 **API 调用之后**才发生？还是路径检查失败的 throw 没有 rollback 已上传的 file？
也可能是 server 端在 multipart 解析失败前已经把文件存了。

**影响**

- 用户以为上传失败，重试 → 重复上传 → 飞书存储浪费
- 重复附件的清理要手工做

**修复建议**

1. 写一个幂等 wrapper：先查记录已有哪些附件，diff 出"需要新增的"，只传新文件
2. 或者 subagent prompt 里说明："如果响应是错误，**不要**自动重试"

---

## Issue #36 🟡 Minor — 写入选项里的 `\n` 在飞书 UI 显示为 `<br>`，存储层需要确认

**现象**

写入 `选项` 字段：

```json
"选项": "A. 40°\nB. 50°\nC. 60°\nD. 70°"
```

`+record-list` 输出显示：

```
选项: A. 40°
B. 50°
C. 60°
D. 70°
```

（实际 markdown 表格源里是 `<br>`）

**判定**

- 存储层用 `\n`（合理假设，但**未确认**）
- 飞书表格 UI 把 `\n` 渲染为 `<br>`（这是 lark-cli 的输出渲染）

**影响**

- 复制 / 导出题目到别处时，可能拿到 `\n` 也可能拿到 `<br>`
- 没有标准化的换行符

**修复建议**

写入时统一用 `\n`（lark-cli 接受 JSON 字符串里的 `\n` 字符）。
读取时按字符串处理，不要按 HTML 处理。

---

## Issue #37 🟢 Resolved — `record_id_list` 顺序与 `rows` 顺序严格对应

**实测**

3 道题的 `rows` 顺序是 [Q1, Q5, Q9]，
返回的 `record_id_list` 是 `['recvltmA3DncVm', 'recvltmA3D7FIZ', 'recvltmA3DbgiT']`。

我用 `record-batch-create` 时的 rows[0] = Q1，rows[1] = Q5，rows[2] = Q9。
record_id_list[0] 对应 Q1，list[1] 对应 Q5，list[2] 对应 Q9。✓

**验证**

读回时：
- `recvltmA3DncVm` → ID=NO.001 → 题干以"1. 如图，AB∥CD"开头（Q1）✓
- `recvltmA3D7FIZ` → ID=NO.002 → 题干以"5. 如图所示"开头（Q5）✓
- `recvltmA3DbgiT` → ID=NO.003 → 题干以"9. 如图，将长方形"开头（Q9）✓

**Issue #4 的担心不成立**，可以放心按"题 - 图片" 一一对应绑定。

---

## Issue #38 🟡 Minor — 关联字段 `所属章节` 在 record-list 输出里被序列化为字符串化的 JSON

**现象**

`+record-list` 输出：

```
所属章节: [{"id":"recvltmb2xinOT"}]
```

这是 markdown 表格把对象数组序列化了。
**存储层**应该是真正的 link 字段值（数组 of record_id 引用），UI 才能点击跳转。

**影响**

- 写完后用户可以在飞书 UI 里点击跳转到章节 ✓
- 但通过 CLI `+record-list` 看到的是字符串化的 JSON，看不出是不是真 link

**修复建议**

`+record-get` 应当返回 link 字段的类型 + 引用信息。lark-cli 当前的 markdown 输出隐藏了类型信息。
要核对 link 是否生效，**唯一可靠方法**是去飞书 UI 看 record 之间能不能点。

---

## 累计：42 个 issue

- 静态（SKILL.md / schema 文档层）：**16 个**（Issue #1-#16）
- 动态 Step 1（建表/字段）：**8 个**（Issue #17-#24）
- 动态 Step 2（OCR 提交/下载）：**6 个**（Issue #25-#31 + Resolved）
- 动态 Step 3+4（写题目/上传图片）：**11 个**（Issue #32-#38, #39-#42）

---

## Issue #39 🟢 Resolved — `+record-upload-attachment` 接受 `--field-id`（名称或 ID 都行）

**现象**

复测了上传附件的 CLI，新版本下：

- `--field-id fldaWxfK8O`（字段 ID）→ ok
- `--field-id 题目图片`（字段名）→ ok

**结论**

`--field` 是不存在的旧 flag。`--field-id` 同时支持 name 和 id 两种解析。
**SKILL.md / base-schema.md 中示例需要修正为 `--field-id`。**

---

## Issue #40 🟢 Resolved — 新增 3 个多选标签字段到 8 个 Base

**用户需求**

```
帮我给题库里面添加三个标签字段：
- 知识点标签（参考 class-point.json）
- 思想标签（参考 method.json）
- 模型标签（参考 model.json）
```

**实现**

| 字段 | 类型 | 来源 | 选项数 | field_id（以浙教版 7下 为例） |
|------|------|------|--------|------------------------------|
| 知识点标签 | select (multiple) | class-point.json 42 项 + 初中补充 16 项 | 58 | fldnRd2c5y |
| 思想标签 | select (multiple) | method.json 35 项 | 35 | fldsOuxlUv |
| 模型标签 | select (multiple) | model.json 48 项 | 48 | fldVtbon4w |

8 个 Base 全部添加成功：

| Base | 知识点标签 | 思想标签 | 模型标签 |
|------|----------|----------|----------|
| 25秋浙教版数学七年级下册《53 同步》 | fldnRd2c5y | fldsOuxlUv | fldVtbon4w |
| 25秋人教版数学五年级上册《53天天练》 | fldvMup36v | fldfmhfDeA | fldleJvlGi |
| 25秋人教版数学四年级上册《53天天练》 | flda1XTGiP | fldWwDCY4R | fldPGJLgNe |
| 25秋北师版数学四年级上册《53天天练》 | fldnWnfT4n | fldw6B0VVO | fldXfgr8E7 |
| 25秋浙教版数学七年级上册《53 同步》 | fld0rDkpcp | fldwDFdVnH | fldPBdIAOq |
| 25秋浙教版数学八年级上册《53 同步》 | fldJbpmP9E | fldQKb4l3U | fldyRLAZ1y |
| 25秋苏教版数学二年级上册《53天天练》 | fldAG6gmva | fldtTF1KPM | fldYbfMiru |
| 26春苏教版数学一年级下册《53天天练》 | fldOE04e94 | fldMs0uwzH | fldQX3Z7AD |

**关键执行细节（容易踩的坑）**

1. **lark-cli `--json` 不接受绝对路径**（Issue #34 复发）— 必须 `cd /Users/water/dev/Marketplaces` 再用 `@./_field_spec.json`。
2. **field-create JSON 结构**是 `{name, type, multiple, options}`，**不是** `field_name`（已修复）— Issue #24 复发。
3. **multi-select 写入值用纯字符串数组** `["平行线", "同旁内角"]`，不用 `[{"text":...}]`。

---

## Issue #41 🟡 Minor — class-point.json 缺「初中」知识点数据

**现象**

`class-point.json` 只有「小学」数据（42 个 points，全是 1-6 年级"数与代数 > 数的认识"分支）。
`method.json` 和 `model.json` 都有 小学/初中 双轨。

**临时解决**

补了 16 个 初中 7下 浙教版常见知识点到 知识点标签 field 选项里：
相交线 / 对顶角 / 邻补角 / 垂线 / 垂线段 / 点到直线的距离 /
同位角 / 内错角 / 同旁内角 / 平行线 / 平行公理 / 平行线的判定 /
平行线的性质 / 平移 / 命题 / 定理

**影响**

8 年级 / 9 年级（高中就更不用说了）的知识点还没有。
后续若要把分类讨论/几何全等/二次根式等都补齐，需要整理 class-point-初中.json 与 高中.json。

**修复建议**

让用户/内容组补全 `class-point.json` 的 初中 / 高中 分支（或拆成 3 个文件：
`class-point-小学.json` / `class-point-初中.json` / `class-point-高中.json`）。

---

## Issue #42 🟡 Minor — `+record-upload-attachment` 不报错但会重复上传（即使 file_token 相同）

**实测**

调用 1 次上传 → 题目图片 数组 1 个元素（K2pEbbAMio33anxSnALcw6t6n9Y）。
再调用 1 次（用字段名而非 ID，**但同文件**）→ 题目图片 数组 2 个元素（多了 IldxbychhoD6d8x38tQcQnTNnYf）。

**判定**

`+record-upload-attachment` 的语义是 **append 到附件数组**，不是 set / replace。
每次调用都会生成新的 file_token（即使是同一文件），所以重复调用会导致 1 张图被叠加 2 次。

**与 Issue #35 的关系**

- #35 关注的是：失败响应时是否重复执行（race）
- #42 关注的是：**成功响应下**，连续两次同样调用会产生 2 个 file_token

两者都是"上传幂等性"问题，但 #35 在错误路径，#42 在成功路径。

**修复建议**

- **SKILL.md 流程**：上传题目图片前应判断 题目图片 字段是否已非空；非空则跳过或先清空再上传
- **lark-cli 端**：考虑加 `--replace` / `--set` 标志

**当前 workaround**

人工或 subagent 写上传脚本时记住"一个 record 题目图片 字段只允许 1 次上传"。

---

## 累计：42 个 issue

- 静态（SKILL.md / schema 文档层）：**16 个**（Issue #1-#16）
- 动态 Step 1（建表/字段）：**8 个**（Issue #17-#24）
- 动态 Step 2（OCR 提交/下载）：**6 个**（Issue #25-#31 + Resolved）
- 动态 Step 3+4（写题目/上传图片）：**11 个**（Issue #32-#38, #39-#42）

下次跑前最该修的：
- **#32**：补 题目图片 字段到 8 个 Base（已自动随本次新 Base 创建）
- **#33**：知识点字段要么改 text，要么 subagent 写前先 add option（**新加的 3 个字段已用 static options 解决**）
- **#35 / #42**：上传附件的幂等性（成功路径 + 失败路径都需要）
- **#41**：补 class-point.json 初中 / 高中分支
- **#2**：`subagent_type: "general-purpose"` → `general`
- **#34**：所有 lark-cli `--json`/`--file` 调用改成相对路径（本次用 `@./_xxx.json` 解决）
