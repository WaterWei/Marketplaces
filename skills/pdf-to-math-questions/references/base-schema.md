# 飞书多维表格题库 Schema

包含两张关联表：**目录表**（存储 PDF 目录结构）和 **题库**（存储题目），通过关联字段双向引用。

## 创建 Base

每套教辅一个独立 Base，以目录名命名。

```bash
# 以目录名创建 Base（目录名自动作为 Base 名称）
lark-cli base +base-create --json '{"name":"25秋浙教版数学七年级上册《53 同步》"}' --as user

# 从返回中获取 base_token（格式如 app_xxx）
```

## 建表

```bash
BASE_TOKEN="<上一步获取的 base_token>"

# 创建数据表
lark-cli base +table-create --base-token "$BASE_TOKEN" --json '{"table_name":"目录"}'
lark-cli base +table-create --base-token "$BASE_TOKEN" --json '{"table_name":"题库"}'

# 获取 table_id
TOC_TABLE_ID=$(lark-cli base +table-list --base-token "$BASE_TOKEN" --as user | jq -r '.items[] | select(.table_name=="目录") | .table_id')
QB_TABLE_ID=$(lark-cli base +table-list --base-token "$BASE_TOKEN" --as user | jq -r '.items[] | select(.table_name=="题库") | .table_id')
```

## 表 1：目录（Chapters）

存储 PDF 目录的层级结构，供题目关联。

| 字段名 | 类型 | 必填 | 说明 | CellValue 示例 |
|--------|------|------|------|---------------|
| `章节名称` | 文本 | 是 | 完整章节标题 | `"第五章 相交线与平行线"` |
| `层级` | 数字 | 是 | 1=章, 2=节, 3=知识点 | `1` |
| `父章节` | 关联 | 否 | 关联到本表的父章节 | `[{record_id}]` |
| `页码` | 数字 | 否 | 在 PDF 中的起始页码 | `52` |
| `来源` | 文本 | 是 | PDF 文件名 | `"2026《初中数学·53同步》七下B本(ZJ).pdf"` |

```bash
# 目录表字段
lark-cli base +field-create --base-token "$BASE_TOKEN" --table-id "$TOC_TABLE_ID" \
  --json '{"field_name":"章节名称","type":1}'
lark-cli base +field-create --base-token "$BASE_TOKEN" --table-id "$TOC_TABLE_ID" \
  --json '{"field_name":"层级","type":2}'
# 父章节（关联本表，需先拿到 TOC_TABLE_ID）
lark-cli base +field-create --base-token "$BASE_TOKEN" --table-id "$TOC_TABLE_ID" \
  --json '{"field_name":"父章节","type":7,"property":{"table_id":"'$TOC_TABLE_ID'"}}'
lark-cli base +field-create --base-token "$BASE_TOKEN" --table-id "$TOC_TABLE_ID" \
  --json '{"field_name":"页码","type":2}'
lark-cli base +field-create --base-token "$BASE_TOKEN" --table-id "$TOC_TABLE_ID" \
  --json '{"field_name":"来源","type":1}'
```

## 表 2：题库（Questions）

| 字段名 | 类型 | 必填 | 说明 | CellValue |
|--------|------|------|------|-----------|
| `题干` | 文本 | 是 | 完整题目，LaTeX 用 `$...$` | `"1. 如图，$AB \\perp CD$..."` |
| `题型` | 单选 | 是 | | `"选择题"` |
| `选项` | 文本 | 否 | ABCD 选项，换行分隔 | `"A. 甲\nB. 乙"` |
| `答案` | 文本 | 否 | | `"C"` |
| `解析` | 文本 | 否 | 答案解析 | |
| `有确定解` | 复选框 | 是 | 模型判断该题是否有可确定的正确答案。true=能确定答案，false=缺条件/开放题/依赖不可见图 | `true` |
| `难度` | 单选 | 是 | | `"★★☆☆☆"` |
| `知识点` | 多选 | 否 | | `["垂线","垂直定义"]` |
| `知识点标签` | 多选 | 否 | 知识点分类标签（58 个预置选项，含小学+初中） | `["平行线","同旁内角"]` |
| `思想标签` | 多选 | 否 | 解题思想方法标签（35 个预置选项，含初中+小学） | `["数形结合","分类讨论"]` |
| `模型标签` | 多选 | 否 | 知识模型标签（48 个预置选项，含初中+小学） | `["直线、线段、交点或角的数量问题"]` |
| `题目图片` | 附件 | 否 | 题目配图（须通过 `+record-upload-attachment` 上传，不能直接写入） | — |
| `所属章节` | 关联 | 否 | 关联到目录表 | `[{record_id}]` |
| `年级` | 单选 | 是 | 从封面解析 | `"七年级"` |
| `学期` | 单选 | 是 | 从封面解析 | `"下册"` |
| `来源` | 文本 | 是 | PDF 文件名 | |
| `页码` | 数字 | 是 | | `6` |
| `标签` | 多选 | 否 | 自定义 | |
| `状态` | 单选 | 否 | | `"待审核"` |

```bash
# 题库表字段
lark-cli base +field-create --base-token "$BASE_TOKEN" --table-id "$QB_TABLE_ID" \
  --json '{"field_name":"题干","type":1}'
lark-cli base +field-create --base-token "$BASE_TOKEN" --table-id "$QB_TABLE_ID" \
  --json '{"field_name":"题型","type":3,"property":{"options":[{"name":"选择题"},{"name":"填空题"},{"name":"解答题"},{"name":"计算题"},{"name":"应用题"}]}}'
lark-cli base +field-create --base-token "$BASE_TOKEN" --table-id "$QB_TABLE_ID" \
  --json '{"field_name":"选项","type":1}'
lark-cli base +field-create --base-token "$BASE_TOKEN" --table-id "$QB_TABLE_ID" \
  --json '{"field_name":"答案","type":1}'
lark-cli base +field-create --base-token "$BASE_TOKEN" --table-id "$QB_TABLE_ID" \
  --json '{"field_name":"解析","type":1}'
lark-cli base +field-create --base-token "$BASE_TOKEN" --table-id "$QB_TABLE_ID" \
  --json '{"field_name":"有确定解","type":5}'
lark-cli base +field-create --base-token "$BASE_TOKEN" --table-id "$QB_TABLE_ID" \
  --json '{"field_name":"难度","type":3,"property":{"options":[{"name":"★☆☆☆☆"},{"name":"★★☆☆☆"},{"name":"★★★☆☆"},{"name":"★★★★☆"},{"name":"★★★★★"}]}}'
lark-cli base +field-create --base-token "$BASE_TOKEN" --table-id "$QB_TABLE_ID" \
  --json '{"field_name":"知识点","type":4}'
# 知识点标签、思想标签、模型标签 — 多选，预置选项来自 class-point.json / method.json / model.json
# 选项列表较长，实际创建时用 --json "@./field_spec.json"（相对路径）传入完整 JSON
# 格式：{"name":"知识点标签","type":"select","multiple":true,"options":[{"name":"平行线"},...]}
lark-cli base +field-create --base-token "$BASE_TOKEN" --table-id "$QB_TABLE_ID" \
  --json "@./field_spec.json"
# 所属章节（关联目录表）
lark-cli base +field-create --base-token "$BASE_TOKEN" --table-id "$QB_TABLE_ID" \
  --json '{"field_name":"所属章节","type":7,"property":{"table_id":"'$TOC_TABLE_ID'"}}'
lark-cli base +field-create --base-token "$BASE_TOKEN" --table-id "$QB_TABLE_ID" \
  --json '{"field_name":"年级","type":3,"property":{"options":[{"name":"一年级"},{"name":"二年级"},{"name":"三年级"},{"name":"四年级"},{"name":"五年级"},{"name":"六年级"},{"name":"七年级"},{"name":"八年级"},{"name":"九年级"}]}}'
lark-cli base +field-create --base-token "$BASE_TOKEN" --table-id "$QB_TABLE_ID" \
  --json '{"field_name":"学期","type":3,"property":{"options":[{"name":"上册"},{"name":"下册"}]}}'
lark-cli base +field-create --base-token "$BASE_TOKEN" --table-id "$QB_TABLE_ID" \
  --json '{"field_name":"来源","type":1}'
lark-cli base +field-create --base-token "$BASE_TOKEN" --table-id "$QB_TABLE_ID" \
  --json '{"field_name":"页码","type":2}'
lark-cli base +field-create --base-token "$BASE_TOKEN" --table-id "$QB_TABLE_ID" \
  --json '{"field_name":"标签","type":4}'
lark-cli base +field-create --base-token "$BASE_TOKEN" --table-id "$QB_TABLE_ID" \
  --json '{"field_name":"状态","type":3,"property":{"options":[{"name":"待审核"},{"name":"已审核"},{"name":"已录入"}]}}'
# 注意：题目图片（附件字段）无法通过 +field-create 创建，会随 Base 初始化自动存在。
# 若 Base 中缺少此字段，需在飞书 UI 手动添加，或检查 lark-cli 版本是否支持 attachment 类型创建。
```

## 图片处理流程

PaddleOCR 返回的图片是云端 URL，需要下载后上传到飞书 Base 作为附件。

### 步骤

```
subagent 解析 → 创建题目记录（返回 record_id）→ 下载图片 → +record-upload-attachment
```

### 1. 下载图片

PaddleOCR 的 JSONL 中每页包含 `markdown.images`：

```json
{
  "markdown": {
    "images": {
      "imgs/img_in_image_box_985_979_1387_1382.jpg": "https://paddleocr.aistudio-app.com/...",
      "imgs/img_in_image_box_1000_2000_1387_2382.jpg": "https://paddleocr.aistudio-app.com/..."
    }
  }
}
```

下载到本地临时目录：

```bash
mkdir -p /tmp/pdf-images/{pdf_name}/
curl -o /tmp/pdf-images/{pdf_name}/img_001.jpg "https://paddleocr.aistudio-app.com/..."
```

### 2. 创建题目记录

先创建不带附件的记录，获取 `record_id`：

```bash
lark-cli base +record-batch-create \
  --base-token "$BASE_TOKEN" \
  --table-id "$QB_TABLE_ID" \
  --as user \
  --json @batch-question.json
```

返回中获取 `record_id_list`。

### 3. 上传附件

对每张图片，上传到对应的记录（使用 `--field-id` 指定字段名或 ID）：

```bash
lark-cli base +record-upload-attachment \
  --base-token "$BASE_TOKEN" \
  --table-id "$QB_TABLE_ID" \
  --record-id "<record_id>" \
  --field-id "题目图片" \
  --file "./img_001.jpg" \
  --as user
```

> **注意**：`--field-id` 同时支持字段名和字段 ID 两种写法。不要使用不存在的 `--field` 或 `--file` 参数名。

### 批量写入示例

```bash
# batch-question.json
cat > /tmp/batch-question.json << 'EOF'
{
  "fields": ["题干", "题型", "答案", "难度", "知识点", "知识点标签", "思想标签", "模型标签", "所属章节", "年级", "学期", "来源", "页码", "状态"],
  "rows": [
    [
      "1. 如图，已知 $AB \\perp CD$...",
      "选择题",
      "C",
      "★★☆☆☆",
      ["垂线", "垂直定义"],
      ["平行线", "同旁内角"],
      ["数形结合"],
      ["直线、线段、交点或角的数量问题"],
      [{"id": "rec_chapter_xxx"}],
      "七年级",
      "下册",
      "2026《初中数学·53同步》七下B本(ZJ).pdf",
      6,
      "待审核"
    ]
  ]
}
EOF
```

## 字段类型对照

| type | 含义 |
|------|------|
| 1 | 文本 |
| 2 | 数字 |
| 3 | 单选 / 多选（`property.multiple: true` 时为多选） |
| 4 | 多选（旧写法，等同 type=3 + multiple） |
| 5 | 复选框 |
| 7 | 关联 |
| 17 | 附件（`题目图片`，须通过 `+record-upload-attachment` 写入，不能直接 JSON 写入） |

## 日期与来源自动提取

年级、学期、来源**不通过输入参数传入**，而是从 PDF 封面页（前 3-5 页）解析：

| 元数据 | 封面中常见来源 |
|--------|--------------|
| 年级 | `"七年级" / "八年级" / "五年级"` 等 |
| 学期 | `"上册" / "下册"` |
| 学科 | `"数学" / "语文" / "英语"` 等 |
| 来源 | PDF 文件名本身 |
| 出版信息 | `"人教版" / "浙教版" / "北师大版"` 等 |
