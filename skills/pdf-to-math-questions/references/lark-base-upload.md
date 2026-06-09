# 飞书多维表格写入流程

每个 subagent 解析完一页后，直接写入当前教辅的 Base。

## 前置条件

Base、两张表及其字段已在 Step 1 创建完成。
`base-info.json` 中包含 `base_token`、`toc_table_id`、`qb_table_id`。

## 写入数据构造

subagent 解析一页后，按以下映射构造写入数据：

### 目录表字段映射

| Base 字段 | 数据来源 | CellValue |
|-----------|---------|-----------|
| `章节名称` | title | 字符串 |
| `层级` | level | 数字 1/2/3 |
| `父章节` | parent_record_id | `[{"id": "rec_parent"}]` 或 null |
| `页码` | page | 数字或 null |
| `来源` | pdf_name | 字符串 |

### 题库表字段映射

| Base 字段 | 数据来源 | CellValue |
|-----------|---------|-----------|
| `题干` | question_text | 字符串 |
| `题型` | question_type | `"选择题"` / `"填空题"` / 等 |
| `答案` | answer | 字符串或空 |
| `有确定解` | has_determinable_answer | `true` / `false` |
| `难度` | difficulty | `"★☆☆☆☆"` ~ `"★★★★★"` |
| `知识点` | knowledge_points | 字符串数组 |
| `知识点标签` | knowledge_point_tags | `["平行线","同旁内角"]` |
| `思想标签` | method_tags | `["数形结合","分类讨论"]` |
| `模型标签` | model_tags | `["直线、线段、交点或角的数量问题"]` |
| `所属章节` | 章节映射 | `[{"id": "rec_chapter_xxx"}]` |
| `年级` | meta.grade | 字符串 |
| `学期` | meta.semester | 字符串 |
| `来源` | pdf_name | 字符串 |
| `页码` | source_page | 数字 |
| `状态` | 固定值 | `"待审核"` |

## 批量写入

### 目录表

```bash
lark-cli base +record-batch-create \
  --base-token "$BASE_TOKEN" \
  --table-id "$TOC_TABLE_ID" \
  --as user \
  --json @batch-chapters.json
```

```json
{
  "fields": ["章节名称", "层级", "父章节", "页码", "来源"],
  "rows": [
    ["第五章 相交线与平行线", 1, null, 52, "主书.pdf"],
    ["5.1 相交线", 2, [{"id": "rec_ch1"}], 52, "主书.pdf"],
    ["知识点 1 垂线", 3, [{"id": "rec_ch2"}], 52, "主书.pdf"]
  ]
}
```

### 题库表

```bash
lark-cli base +record-batch-create \
  --base-token "$BASE_TOKEN" \
  --table-id "$QB_TABLE_ID" \
  --as user \
  --json @batch-questions.json
```

```json
{
  "fields": ["题干", "题型", "答案", "有确定解", "难度", "知识点", "知识点标签", "思想标签", "模型标签", "所属章节", "年级", "学期", "来源", "页码", "状态"],
  "rows": [
    [
      "1. 如图，已知 $AB \\perp CD$...",
      "选择题",
      "C",
      true,
      "★★☆☆☆",
      ["垂线", "垂直定义"],
      ["平行线", "同旁内角"],
      ["数形结合"],
      ["直线、线段、交点或角的数量问题"],
      [{"id": "rec_chapter_xxx"}],
      "七年级",
      "下册",
      "5年中考3年模拟 初中数学七年级上册浙教版+A本（彩色版）.pdf",
      6,
      "待审核"
    ]
  ]
}
```

## 图片上传

### 流程

```
创建记录（获得 record_id） → 从 markdown.images 获取 URL → curl 下载 → +record-upload-attachment
```

### 命令

```bash
# 下载
curl -o /tmp/pdf-images/img_001.jpg "https://paddleocr.aistudio-app.com/..."

# 上传到已创建的题目记录（使用 --field-id 指定字段名）
lark-cli base +record-upload-attachment \
  --base-token "$BASE_TOKEN" \
  --table-id "$QB_TABLE_ID" \
  --record-id "<record_id>" \
  --field-id "题目图片" \
  --file "./img_001.jpg" \
  --as user
```

### 对应关系

PaddleOCR JSONL 中 `markdown.images` 格式：

```json
{
  "imgs/img_in_image_box_985_979_1387_1382.jpg": "https://paddleocr.aistudio-app.com/xxx"
}
```

subagent 解析的 `question.images` 中的路径即此字典的 key。
通过 key 找到云端 URL，下载后上传到对应的记录。

## 规则

- **身份：** 所有操作使用 `--as user`
- **串行写入：** 连续写入同一表时串行，批次间延迟 0.5-1 秒
- **分批限制：** 单批 ≤200 条

## 参考

- [lark-base 全局规则](../../../.config/opencode/skills/lark-base/SKILL.md)
- [lark-base-cell-value.md](../../../.config/opencode/skills/lark-base/references/lark-base-cell-value.md)
- [lark-base-record-batch-create.md](../../../.config/opencode/skills/lark-base/references/lark-base-record-batch-create.md)
- [lark-base-record-upload-attachment.md](../../../.config/opencode/skills/lark-base/references/lark-base-record-upload-attachment.md)
