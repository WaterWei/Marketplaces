---
name: extract-questions
version: 1.1.0
description: 逐张处理题目图片，用 subagent 单张分析、即时追加保存 JSON
model:
  min: extended
trigger:
  - "提取题目"
  - "处理图片为 JSON"
  - "分析题目图片"
---

# Extract Questions

逐张处理分割后的题目图片，提取题目内容和知识点，每完成一张即写入 JSON。

## 输入

- 图片目录 `{章节名}/output/`
- 输出文件 `{章节名}/questions.json`

## 工作流

### 1. 扫描图片

列出 `{章节名}/output/` 下所有 `*.png`，按文件名排序。

### 2. 逐张 Subagent 处理

对每张图片创建一个 `task`（`subagent_type: general`），按顺序或并行发出。每返回一个结果，立即更新 JSON 文件。

**Subagent Prompt:**

```
请分析这张图片，提取题目信息。

图片路径：{image_path}

提取字段：
- id: 文件名（不含扩展名）
- image_path: 相对路径（如 output/0001.png）
- question_text: 完整文本（保持原文，数学符号保持原样）
- knowledge_points: 知识点列表 2-4 个
- question_type: "讲解" 或 "例题"
  - 讲解：知识回顾、方法总结、规律归纳
  - 例题：需要回答/解题的题目
- grade_level: 适合年级（如 小学一年级）
- subject: 学科（如 数学）

空白页（无实际内容）返回 null。

只返回 JSON 对象，不要多余文字：
{ "id": "0001", "image_path": "...", "question_text": "...", "knowledge_points": [...], "question_type": "例题", "grade_level": "...", "subject": "数学" }
```

### 3. 即时保存

每从 subagent 拿到一个有效结果（非 null），立即：

1. 读取已有的 JSON 文件（或创建新文件）
2. 追加到 `questions` 数组
3. 更新 `metadata.total_questions`
4. 写回文件（UTF-8，格式化）

### 4. 输出 JSON 格式

```json
{
  "version": "1.0",
  "source": {
    "pdf": "原始 PDF 文件名",
    "split_output": "output"
  },
  "questions": [
    {
      "id": "0001",
      "image_path": "output/0001.png",
      "question_text": "比一比，在○里填上 >、< 或 =",
      "knowledge_points": ["数的大小比较"],
      "question_type": "例题",
      "grade_level": "小学一年级",
      "subject": "数学"
    }
  ],
  "metadata": {
    "total_questions": 12,
    "processed_at": "2026-05-18T00:00:00+08:00",
    "model_used": "当前模型名称"
  }
}
```

## 规则

- 空白页不纳入 JSON
- `question_type` 仅两类：`讲解` / `例题`
- 保持 `question_text` 原文，不做改写或解答
- 知识点用中文短语，2-4 个为宜
