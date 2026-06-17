# Subagent Prompt Templates

## 1. 封面 & 目录解析模板（Step 2 使用）

解析 PDF 前 5 页，提取元数据和完整目录结构。

### 输入

```json
{
  "pdf_name": "2026《初中数学·53同步》七下B本(ZJ).pdf",
  "cover_pages": [
    {
      "page_number": 1,
      "blocks": [
        {"label": "doc_title", "content": "2026 初中数学·53同步"},
        {"label": "text", "content": "七年级下册"},
        {"label": "text", "content": "浙教版"}
      ]
    },
    {
      "page_number": 2,
      "blocks": [
        {"label": "paragraph_title", "content": "目录"},
        {"label": "text", "content": "第五章 相交线与平行线"},
        {"label": "text", "content": "5.1 相交线"}
      ]
    }
  ]
}
```

### Prompt 模板

```
你是一个 PDF 教辅解析工具。根据以下 PDF 前 5 页的 OCR 数据，提取元数据和完整目录。

PDF 名称：{pdf_name}

OCR 块：
{cover_pages_json}

输出两样东西：

A. 元数据（从封面/版权页提取）：
{
  "grade": "七年级",       // 一年级~九年级
  "semester": "下册",      // 上册/下册
  "subject": "数学",
  "publisher": "浙教版"    // 出版社/版本
}

B. 目录结构（从目录页提取）：
[
  {"title": "第五章 相交线与平行线", "level": 1, "page": 52},
  {"title": "5.1 相交线", "level": 2, "page": 52},
  {"title": "知识点 1 垂线", "level": 3, "page": 52},
  {"title": "知识点 2 垂直定义", "level": 3, "page": 55},
  {"title": "5.2 平行线", "level": 2, "page": 58},
  {"title": "第五章 达标检测", "level": 2, "page": 62}
]

规则：
1. level: 1=章, 2=节, 3=知识点
2. page: 尽量从目录页提取，找不到则填 null
3. 保留完整标题文字，不要截断
4. 封面页、前言等非目录内容不输出到目录数组
5. 如果前 5 页没有目录，返回空数组 []

只返回 JSON，不要多余文字：
{"meta": {...}, "toc": [...]}
```

---

## 2. 题目解析模板（Step 3 使用）

每个 subagent 接收 3 页上下文，只解析中间页的题目。

### 滑动窗口规则

| 场景 | 传入页 | 解析目标 |
|------|--------|---------|
| 第 1 页 | `[1, 2]` | 第 1 页 |
| 第 N 页（2 ≤ N ≤ last-1） | `[N-1, N, N+1]` | 第 N 页 |
| 最后 1 页 | `[last-1, last]` | 最后 1 页 |

前后页仅用于消除翻页导致的内容截断，不从中提取题目。

### 输入

```json
{
  "pdf_name": "2026《初中数学·53同步》七下B本(ZJ).pdf",
  "current_page": 6,
  "total_pages": 60,
  "context_pages": [
    {
      "page_number": 5,
      "blocks": [
        {"label": "text", "content": "...上一页末尾..."}
      ]
    },
    {
      "page_number": 6,
      "blocks": [
        {"label": "paragraph_title", "content": "知识点 1 垂直"},
        {"label": "text", "content": "1. 如图，已知直线 AB 与 CD ..."}
      ]
    },
    {
      "page_number": 7,
      "blocks": [
        {"label": "text", "content": "...下一页开头..."}
      ]
    }
  ]
}
```

### Prompt 模板

```
你是一个数学教辅结构化工具。以下是一个 PDF 中连续 3 页的 OCR 块数据，
请提取第 {current_page} 页中的所有数学题目。

PDF 名称：{pdf_name}
当前解析页：第 {current_page} 页（共 {total_pages} 页）

传入的 3 页 OCR 块（已按阅读顺序排列）：
{context_pages_json}

注意：
- context_pages 中第 1 页是上一页、最后 1 页是下一页，仅作为跨页内容参考
- 只输出第 {current_page} 页中的题目
- 如果某题题干在前一页开始、在本页结束，将其归为当前页完整输出

输出规则：
1. 提取当前页每一道独立题目，每题一个对象
2. id 格式为 "Q{current_page}_{序号}"（如 Q6_1, Q6_2）
3. 对选择题：提取完整选项文本到 options 字段（如 "A. 40°\nB. 50°\nC. 60°\nD. 70°"）
4. 对解答题/计算题：保留完整题干，options 为 null
5. question_text 保持原文，数学符号用 LaTeX 风格 $...$
6. image 块保留为 <img src=\"...\"> 标签，放在对应题干的文本位置
7. 空白页、目录页、封面页返回 []
8. 题型分类：选择题 / 填空题 / 解答题 / 计算题 / 应用题
9. 从 paragraph_title 推断 knowledge_points
10. 判断这道题是否有确定解（has_determinable_answer）：
    - 结合题目文本、选项（若有）、图片内容综合理解
    - 如果能作为数学教师 confidently 确定正确答案 → true，并填入 answer
    - 如果缺少关键信息（如依赖未见过的图、条件不足、开放性答案）→ false，answer 留空
11. 难度判断（difficulty）：1=基础识记、2=简单应用、3=中等综合、4=较难推理、5=压轴题
12. 标签匹配（如果能从题目内容推断）：
    - knowledge_point_tags：从 class-point.json 选项中匹配
    - thinking_tags：从 method.json 选项中匹配
    - model_tags：从 model.json 选项中匹配
    - 无法匹配时返回空数组 []

只返回 JSON 数组：
[
  {
    "id": "Q6_1",
    "source_page": 6,
    "question_text": "...",
    "question_type": "选择题",
    "options": "A. 40°\nB. 50°\nC. 60°\nD. 70°",
    "answer": "C",
    "analysis": "由 AB∥CD 知同位角相等，∠2=∠1=50°",
    "has_determinable_answer": true,
    "difficulty": 2,
    "knowledge_points": ["垂线", "垂直定义"],
    "knowledge_point_tags": ["垂线"],
    "thinking_tags": ["数形结合"],
    "model_tags": ["直线、线段、交点或角的数量问题"],
    "section_title": "知识点 1 垂直",
    "images": ["imgs/img_in_image_box_...jpg"]
  }
]
```

注意：
- `section_title` 字段帮助后续匹配目录表中的章节
- `images` 列表中的路径对应 PaddleOCR 返回的 `markdown.images` 的 key
- `has_determinable_answer` 用于写入「有确定解」字段，subagent 需结合 OCR 图片和上下文综合判断
- `options` 字段：选择题必须提取完整选项文本，非选择题填 null
- `analysis` 字段：如果题目本身包含解析/解题过程则提取，否则留空
- `knowledge_point_tags` / `thinking_tags` / `model_tags`：尽量从题目内容推断匹配预置选项，无法匹配返回空数组
