# PPT Deck JSON Schema

## 顶层结构

```json
{
  "title": "演示标题（必填）",
  "author": "作者（可选）",
  "date": "日期（可选）",
  "slides": [ ... ]
}
```

## Slide 通用字段

每个 slide 对象必须包含：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | number | 是 | 从 1 开始的递增序号 |
| `layout` | string | 是 | 布局类型（见下表） |
| `eyebrow` | string | 是 | 顶部小标签，如 "OVERVIEW"、"PHASE 1"。封面页可为空字符串 `""` |
| `title` | string | 是 | 幻灯片大标题 |

## 布局类型 (layout)

### `cover` — 封面 / 结尾页

| 字段 | 类型 | 说明 |
|------|------|------|
| `subtitle` | string | 副标题 |
| `description` | string | 描述行（如日期、面向人群） |

```json
{
  "id": 1,
  "layout": "cover",
  "eyebrow": "",
  "title": "React 19",
  "subtitle": "What's New & What's Next",
  "description": "前端团队技术分享 · 2026"
}
```

### `cards` — 多列卡片

| 字段 | 类型 | 说明 |
|------|------|------|
| `cards` | CardItem[] | 卡片数组 |

**CardItem:**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `icon` | string | 是 | emoji 图标，如 "⚡"、"🧠" |
| `title` | string | 是 | 卡片标题 |
| `description` | string | 是 | 卡片描述 |
| `tag` | string | 否 | 右上角标签，如 "Pain #1" |

```json
{
  "id": 2,
  "layout": "cards",
  "eyebrow": "OVERVIEW",
  "title": "三大核心变化",
  "cards": [
    { "icon": "⚡", "title": "性能", "description": "描述文字", "tag": "Tag" },
    { "icon": "🌊", "title": "API", "description": "描述文字" }
  ]
}
```

### `list` — 编号列表

| 字段 | 类型 | 说明 |
|------|------|------|
| `description` | string | 列表前的描述文字（可选） |
| `items` | string[] | 列表项数组 |

```json
{
  "id": 3,
  "layout": "list",
  "eyebrow": "STEPS",
  "title": "迁移要点",
  "items": [
    "第一步：升级依赖",
    "第二步：移除废弃 API",
    "第三步：运行测试"
  ]
}
```

### `columns` — 多栏并列

| 字段 | 类型 | 说明 |
|------|------|------|
| `description` | string | 栏目前的描述（可选） |
| `columns` | ColumnContent[] | 栏目数组（2-3 个） |

**ColumnContent:**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | string | 是 | 栏目标题 |
| `items` | string[] | 是 | 栏目内容列表 |
| `accent` | boolean | 否 | 是否高亮此栏目（最多一个为 true） |

```json
{
  "id": 4,
  "layout": "columns",
  "eyebrow": "COMPARISON",
  "title": "新旧对比",
  "columns": [
    { "title": "Before", "items": ["旧方式1", "旧方式2"] },
    { "title": "After", "items": ["新方式1", "新方式2"], "accent": true }
  ]
}
```

### `code` — 代码块

| 字段 | 类型 | 说明 |
|------|------|------|
| `description` | string | 代码前的描述（可选） |
| `code` | CodeBlock | 代码块对象 |

**CodeBlock:**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `filename` | string | 否 | 文件名标签 |
| `language` | string | 否 | 语言标识 |
| `code` | string | 是 | 代码内容（用 `\n` 换行） |

```json
{
  "id": 5,
  "layout": "code",
  "eyebrow": "EXAMPLE",
  "title": "示例代码",
  "code": {
    "filename": "app.tsx",
    "language": "tsx",
    "code": "function App() {\n  return <div>Hello</div>\n}"
  }
}
```

### `table` — 表格

| 字段 | 类型 | 说明 |
|------|------|------|
| `description` | string | 表格前的描述（可选） |
| `table` | TableData | 表格对象 |

**TableData:**

| 字段 | 类型 | 说明 |
|------|------|------|
| `headers` | string[] | 表头列名 |
| `rows` | string[][] | 数据行（每行是 string 数组，列数需与 headers 一致） |

```json
{
  "id": 6,
  "layout": "table",
  "eyebrow": "STATUS",
  "title": "框架支持情况",
  "table": {
    "headers": ["框架", "版本", "状态"],
    "rows": [
      ["React", "19.x", "稳定"],
      ["Vue", "3.5", "稳定"]
    ]
  }
}
```

### `comparison` — 左右对比

| 字段 | 类型 | 说明 |
|------|------|------|
| `comparison` | object | 包含 `left` 和 `right` |

**ComparisonSide:**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | string | 是 | 侧标题 |
| `items` | string[] | 是 | 对比项列表 |
| `highlight` | boolean | 否 | 是否高亮（通常右侧为 true） |

```json
{
  "id": 7,
  "layout": "comparison",
  "eyebrow": "VS",
  "title": "方案对比",
  "comparison": {
    "left": {
      "title": "方案 A",
      "items": ["优点1", "缺点1"]
    },
    "right": {
      "title": "方案 B",
      "items": ["优点1", "优点2"],
      "highlight": true
    }
  }
}
```

### `content` — 通用内容页

最灵活的布局，适用于大部分内容页。

| 字段 | 类型 | 说明 |
|------|------|------|
| `description` | string | 描述文字（可选） |
| `items` | string[] | 要点列表（可选） |

```json
{
  "id": 8,
  "layout": "content",
  "eyebrow": "SUMMARY",
  "title": "总结",
  "description": "本次分享的核心要点：",
  "items": ["要点一", "要点二", "要点三"]
}
```

## 布局选择指南

| 内容特征 | 推荐布局 |
|----------|---------|
| 开场 / 结尾 | `cover` |
| 3-6 个并列要点，每个需要图标和描述 | `cards` |
| 有序步骤、操作清单 | `list` |
| 2-3 个维度并列对比 | `columns` |
| 展示代码片段 | `code` |
| 结构化数据、矩阵 | `table` |
| 二选一、正反对比 | `comparison` |
| 其他所有情况 | `content` |
