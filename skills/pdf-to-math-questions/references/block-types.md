# Block Types Reference

Subagent 收到的 `blocks` 中，标签含义与处理方式：

| block_label | 含义 | 处理方式 |
|-------------|------|---------|
| `doc_title` | 章/节标题 | 作为上下文，不录入题目 |
| `paragraph_title` | 小节/知识点标题 | 帮助推断 `knowledge_points` |
| `text` | 正文（题干/选项/答案/解析） | 主要处理对象 |
| `image` | 嵌入图片（几何图/表格/插图） | 保留在题干中 `<img>` |
| `figure_title` | 图注（如"第 3 题图"） | 附在对应图片后 |
| `header` / `footer` / `number` | 页眉/页脚/页码 | **跳过**，不传给 subagent |
| `vision_footnote` | 脚注（如"几何画板"） | 跳过 |
| `table` | 表格 | 保留为 Markdown 表格 |

## 处理规则

- **跳过非题目页：** 封面、目录、前言、空白页 → subagent 返回空数组
- **答案来源：** 如果原 PDF 是答案册，`answer` 字段填入答案；如果是练习册（无答案），`answer: null`
- **数学公式：** 强制用 LaTeX `$...$` 风格，不要用 Unicode 数学符号替代
- **图片引用：** 保留原始路径，消费端按需下载或转 Base64
- **难度分级：** 1=基础，2=中等，3=较难，4=综合，5=压轴
- **知识点：** 优先从 `paragraph_title` 推断，次从题目内容推断
