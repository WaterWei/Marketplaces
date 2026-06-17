---
name: pdf-to-math-questions
version: 7.1.0
description: 从教辅目录提取数学题，自动创建飞书多维表格并写入
trigger:
  - "录入题库"
  - "PDF 提取数学题"
  - "PaddleOCR 题库导入"
  - "OCR 录入题目"
---

# PDF to Math Questions

每套教辅 = 一个本地目录（含多个 PDF）= 一个飞书多维表格（含 目录 + 题库 两张表）。
自动创建 Base、解析封面提取年级/学期、解析目录建立章节结构、
逐页解析题目并上传图片。

## 目录结构约定

```
25秋浙教版数学七年级上册《53 同步》/
├── 5年中考3年模拟 初中数学七年级上册浙教版+A本（彩色版）.pdf   ← 主书
├── 5年中考3年模拟 初中数学七年级上册浙教版+B本（彩色版）.pdf
├── 5年中考3年模拟-初中数学七年级上册浙教版+试卷（A4版）.pdf
├── 5年中考3年模拟 初中数学七年级上册浙教版+A本答案.pdf
└── 5年中考3年模拟 初中数学七年级上册浙教版+B本答案（彩色版）.pdf
```

每个目录内的所有 PDF 共享同一个 Base 的 目录 + 题库 两张表。

## 工作流概览

```
教辅目录/
  ├── ① 创建飞书 Base（以目录名命名）
  │     ├── 创建「目录」表
  │     └── 创建「题库」表
  ├── ② 提交目录下所有 PDF 到 PaddleOCR → raw_pages/
  ├── ③ 解析主书封面(前5页) → 提取年级/学期/版本
  │    解析主书目录 → 章节树 → 写入「目录」表
  └── ④ 逐页解析所有 PDF（3页滑动窗口）
        解析中间页题目 → 创建题目记录 → 上传云端图片 → 关联章节
```

## 输入

| 参数 | 说明 |
|------|------|
| `input_dir` | 教辅目录路径（含多个 PDF） |
| `output_dir` | 输出目录（默认 `output/`） |

## 前置准备

```bash
uv pip install requests
lark-cli config init
lark-cli auth login --domain base
```

API Token 和端点见 `references/api-config.md`。

## 执行步骤

### Step 1 — 创建飞书多维表格

以目录名为 Base 名称创建飞书多维表格，建好 目录 + 题库 两张表及其字段。

```
Task(
  subagent_type: "general",
  description: "为 {input_dir} 创建飞书 Base",
  prompt: "执行以下步骤：
1. 从目录名 {input_dir} 中提取 Base 名称（取最后一级目录名）
2. 读取 references/base-schema.md 了解表结构
3. 使用 lark-cli base +base-create --name "<目录名>" 创建 Base
4. 记录返回的 base_token
5. 依次创建「目录」表和「题库」表及其所有字段（字段定义见 base-schema.md）
6. 保存 base_token + 两个 table_id 到 {output_dir}/base-info.json

返回：1) base_token 2) 目录表 table_id 3) 题库表 table_id"
)
```

### Step 2 — 提交 PDF 到 PaddleOCR API

扫描目录下所有 `.pdf` 文件，逐个提交到 PaddleOCR 并下载结果。

```
Task(
  subagent_type: "general",
  description: "提交 {input_dir} 所有 PDF 到 OCR",
  prompt: "执行以下步骤：
1. 扫描 {input_dir} 下所有 *.pdf 文件
2. 读取 references/api-config.md 获取 API 参数
3. 参考 docs/paddleocr/test_ocr.py 的实现
4. 对每个 PDF：
   a. 上传，轮询等待 job 完成
   b. 下载 JSONL 结果
   c. 保存为 {output_dir}/raw_pages/{pdf_name}.json
5. 输出每个 PDF 的页数和状态

返回：1) 所有 raw_pages 路径 2) 每个 PDF 的页数 3) 任何异常"
)
```

### Step 3 — 解析主书封面 & 目录

从主书 PDF（通常文件名含"主书"、"A本"或体积最大）的前 5 页，
解析元数据和完整目录，写入「目录」表。

```
Task(
  subagent_type: "general",
  description: "解析 {input_dir} 封面和目录",
  prompt: "执行以下步骤：
1. 扫描 {output_dir}/raw_pages/ 下所有文件
2. 从 {output_dir}/base-info.json 读取 base_token 和目录表 table_id
3. 读取 references/subagent-prompt.md 中的 cover-toc prompt 模板
4. 按优先级确定主书 PDF：
   - 文件名含"主书"、"A本"优先
   - 或页数最多的 PDF
5. 读取主书 PDF 的 raw_pages 前 5 页
6. 构造 prompt，解析封面和目录

输出两样东西：
  A. 元数据：{grade, semester, subject, publisher}
  B. 目录数组：[{title, level, parent_title, page}]

7. 将目录写入「目录」表（先父后子，逐级写入）
8. 将章节名称 → record_id 的映射保存到 {output_dir}/chapter-map.json

返回：1) 年级/学期 2) 目录条目数 3) 章节映射路径"
)
```

**目录写入规则：**
- 按层级写入：先 level=1（章），再 level=2（节），最后 level=3（知识点）
- 子章节通过 `parent_title` 查找父章节的 record_id，建立关联
- 每批 ≤200 条，批次间延迟 0.5-1 秒

### Step 4 — Subagent 逐页解析并写入（3 页滑动窗口）

对每个 PDF 的每一内容页，启动 subagent：解析题目 → 写入 Base → 上传图片。

滑动窗口：
- 第 1 页 → `[1, 2]`，解析第 1 页
- 第 N 页 → `[N-1, N, N+1]`，解析第 N 页
- 最后 1 页 → `[last-1, last]`

```
Task(
  subagent_type: "general",
  description: "解析并写入 {pdf_name} 第 {N} 页",
  prompt: "执行以下步骤：

A. 解析题目
  1. 读取 {output_dir}/raw_pages/{pdf_name}.json 中第 {N-1}、{N}、{N+1} 页
  2. 读取 references/subagent-prompt.md 中的 question prompt 模板
  3. 构造 prompt，传入 3 页上下文，解析第 {N} 页题目

B. 确定所属章节
  4. 读取 {output_dir}/chapter-map.json 中的章节映射
  5. 根据当前页的 section_title/paragraph_title 匹配章节 record_id

C. 写入飞书
  6. 从 {output_dir}/base-info.json 读取 base_token 和题库表 table_id
  7. 读取 references/base-schema.md 了解字段映射
  8. 构造写入数据，关联章节 record_id
  9. 使用 +record-batch-create 创建题目记录
  10. 从返回中获取新记录的 record_id_list

D. 上传图片
   11. 从 raw_pages 中提取本页的 markdown.images（云端 URL → 本地文件映射）
   12. 下载图片到 /tmp/pdf-images/
   13. 对每张图片，使用 +record-upload-attachment 上传到对应记录
       注意：使用 --field-id "题目图片"（不要用 --field 或 --file）

返回：1) 本页题数 2) 写入记录数 3) 上传图片数 4) 任何错误"
)
```

**并行策略：**
- 同时启动 3-5 个 subagent 并发，每个处理不同 PDF 的不同页
- 连续写入时批次间延迟 0.5-1 秒

### Step 4b — 填写标签字段（可选，批量补录时使用）

题库已有 3 个预置选项的多选标签字段，subagent 解析题目时可同步填写：

| 字段 | 选项来源 | 写入格式 |
|------|---------|---------|
| `知识点标签` | `class-point.json`（小学 42 项 + 初中补充 16 项） | `["平行线","同旁内角"]` |
| `思想标签` | `method.json`（初中 18 项 + 小学 17 项） | `["数形结合","分类讨论"]` |
| `模型标签` | `model.json`（初中 41 项 + 小学 7 项） | `["直线、线段、交点或角的数量问题"]` |

写入方式：直接在 `+record-batch-create` 的 rows 中包含这 3 列，值为纯字符串数组。
选项名必须与预置选项**完全一致**（区分大小写、标点）。

> **注意**：`题目图片` 是附件字段，不能通过 JSON 直接写入。必须先创建记录，再用 `+record-upload-attachment --field-id "题目图片"` 上传。

## ⚠️ 硬性规则（违反会导致数据不完整）

### 规则 1：禁止自定义简化 Schema

**绝对不要**为 subagent 创建新的输出格式定义文件（如 `parse-prompt.md`）。
所有题目解析的 prompt **必须**直接引用 `references/subagent-prompt.md` 中的 **Step 3 模板**。

原因：Step 3 模板已定义完整字段（answer, knowledge_points, difficulty, has_determinable_answer 等），
自定义简化版会导致大量字段缺失。

### 规则 2：batch 写入必须覆盖 base-schema.md 的全部必填字段

生成 `+record-batch-create` 的 rows 时，**必须**对照 `references/base-schema.md` 表 2 的字段列表，
确保以下字段全部写入：

| 字段 | 必填 | 来源 |
|------|------|------|
| `题干` | 是 | subagent → question_text |
| `题型` | 是 | subagent → question_type |
| `选项` | 否 | subagent 提取的 ABCD 选项文本 |
| `答案` | 否 | subagent → answer |
| `解析` | 否 | subagent 提取的解题过程 |
| `有确定解` | 是 | subagent → has_determinable_answer |
| `难度` | 是 | subagent → difficulty（1-5） |
| `知识点` | 否 | subagent → knowledge_points |
| `知识点标签` | 否 | subagent 匹配 class-point.json |
| `思想标签` | 否 | subagent 匹配 method.json |
| `模型标签` | 否 | subagent 匹配 model.json |
| `所属章节` | 否 | 根据 section_title 匹配 chapter-map.json |
| `年级` | 是 | 从封面解析 |
| `学期` | 是 | 从封面解析 |
| `来源` | 是 | PDF 文件名 |
| `页码` | 是 | 当前页号 |
| `状态` | 否 | 默认 "待审核" |

**检查方法**：batch 写入前，用以下脚本验证字段完整性：

```bash
# 验证 batch JSON 包含所有必填字段
python3 -c "
import json, sys
REQUIRED = ['题干', '题型', '有确定解', '难度', '年级', '学期', '来源', '页码']
batch = json.load(open(sys.argv[1]))
fields = batch.get('fields', [])
missing = [f for f in REQUIRED if f not in fields]
if missing:
    print(f'ERROR: missing fields: {missing}')
    sys.exit(1)
print(f'OK: {len(fields)} fields, {len(batch[\"rows\"])} rows')
" batch_1.json
```

### 规则 3：subagent prompt 必须包含完整输出字段列表

构造 subagent prompt 时，输出格式部分**必须**包含以下全部字段：

```json
{
  "id": "Q{page}_{seq}",
  "source_page": N,
  "question_text": "完整题干（含 LaTeX）",
  "question_type": "选择题|填空题|解答题|计算题|应用题",
  "options": "A. xxx\nB. xxx\nC. xxx\nD. xxx",
  "answer": "C",
  "analysis": "解题过程...",
  "has_determinable_answer": true,
  "difficulty": 2,
  "knowledge_points": ["垂线", "垂直定义"],
  "knowledge_point_tags": ["平行线"],
  "thinking_tags": ["数形结合"],
  "model_tags": ["直线、线段、交点或角的数量问题"],
  "section_title": "知识点 1 垂直",
  "images": ["imgs/img_in_image_box_xxx.jpg"]
}
```

**不要**删除或简化上述任何字段。即使某个字段暂时无法提取，
也要在输出中保留该字段（值为 null 或空数组）。

### 规则 4：每个 Base 写入后必须验证字段覆盖率

写入完成后，抽样检查记录的字段覆盖率：

```bash
# 抽样 5 条，检查非空字段数
lark-cli base +record-list --base-token <token> --table-id <table_id> --limit 5 --format json
# 预期：每条记录至少 8 个字段有值（题干、题型、年级、学期、来源、页码、有确定解、难度）
```

如果大部分记录只有 3-5 个字段有值，说明 subagent prompt 缺少字段定义，必须回到 Step 3 模板检查。

---

## 参考文件

| 文件 | 内容 |
|------|------|
| `references/api-config.md` | PaddleOCR API 端点、认证、参数配置 |
| `references/subagent-prompt.md` | prompt 模板（封面/TOC + 题目）— **Step 4 必须引用此文件** |
| `references/block-types.md` | OCR 块类型说明和处理规则 |
| `references/base-schema.md` | 飞书完整 Schema、建表命令、图片上传 — **batch 写入必须对照此文件** |
| `references/lark-base-upload.md` | 写入流程与 CellValue 映射 |
| `class-point.json` | 知识点标签选项（小学） |
| `method.json` | 思想标签选项（小学+初中） |
| `model.json` | 模型标签选项（小学+初中） |
| `references/sample-data.md` | 解析结果中间格式参考 |
| `docs/paddleocr/test_ocr.py` | API 调用参考实现 |
| `docs/paddleocr/api.py` | API Token 和完整参数 |
