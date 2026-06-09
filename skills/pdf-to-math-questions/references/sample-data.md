# 样本数据

## 目录结构

```
output/
├── base-info.json                          ← Step 1 输出
├── raw_pages/
│   ├── 主书.pdf.json
│   ├── 答案.pdf.json
│   └── 试卷.pdf.json
├── meta/
│   └── 主书.pdf.json                       ← Step 2 输出的元数据
└── chapter-map.json                        ← Step 3 输出的章节映射
```

## base-info.json（Step 1 输出）

```json
{
  "base_name": "25秋浙教版数学七年级上册《53 同步》",
  "base_token": "app_xxxxxxxxxx",
  "toc_table_id": "tbl_yyyyyyyyyy",
  "qb_table_id": "tbl_zzzzzzzzzz"
}
```

## meta/{pdf_name}.json（Step 3 从封面解析）

```json
{
  "grade": "七年级",
  "semester": "上册",
  "subject": "数学",
  "publisher": "浙教版"
}
```

## chapter-map.json（Step 3 输出）

```json
[
  {"title": "第五章 相交线与平行线", "level": 1, "page": 52, "record_id": "rec_ch1"},
  {"title": "5.1 相交线", "level": 2, "page": 52, "record_id": "rec_ch2", "parent_title": "第五章 相交线与平行线"},
  {"title": "知识点 1 垂线", "level": 3, "page": 52, "record_id": "rec_ch3", "parent_title": "5.1 相交线"},
  {"title": "5.2 平行线", "level": 2, "page": 58, "record_id": "rec_ch4", "parent_title": "第五章 相交线与平行线"}
]
```

## 题目解析结果中间格式

subagent 解析一页后的输出（经字段映射后写入 Base）：

```json
[
  {
    "source_page": 6,
    "question_text": "1. [2025 河北石家庄平山月考] 如图，已知直线 AB 与 CD 相交于点 O...\n\n<img src=\"imgs/img_in_image_box_985_979_1387_1382.jpg\" />\n\nA. 只有乙不正确\nB. 只有丙不正确\nC. 甲、乙、丙都正确",
    "images": ["imgs/img_in_image_box_985_979_1387_1382.jpg"],
    "answer": "C",
    "knowledge_points": ["垂线", "垂直定义"],
    "question_type": "选择题",
    "difficulty": 2,
    "section_title": "知识点 1 垂线",
    "has_determinable_answer": true
  }
]
```

`section_title` 用于匹配 `chapter-map.json` 找到对应章节的 `record_id`。
`images` 中的路径对应 PaddleOCR JSONL 里 `markdown.images` 的 key。
`has_determinable_answer` 映射到 Base 的「有确定解」字段。
