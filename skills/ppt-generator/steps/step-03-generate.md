# Step 3: 生成 JSON

## 目标

根据 Step 2 确认的布局规划表，从演讲稿原文中提取具体内容，生成完整的 JSON。

## 执行流程

### 1. 准备工作

- 回顾 Step 2 的布局规划表
- 回顾用户的原始演讲稿内容
- 回顾 `{skill-root}/schema.md` 中每个布局的字段要求

### 2. 逐张生成幻灯片

按规划表顺序，为每张幻灯片生成 JSON 对象：

**规则：**

1. **内容忠实于原文** — 从演讲稿中提取，不编造。如果原文某处表述模糊，保留原文用词
2. **精简但完整** — 幻灯片文字应精炼（每行不超过 30 字），但不丢失关键信息
3. **id 递增** — 从 1 开始，每张 +1
4. **eyebrow 全大写** — 英文标签使用大写形式
5. **封面页的 eyebrow 为空字符串** `""`
6. **emoji 选择** — cards 布局的 icon 字段，选择与内容语义匹配的 emoji
7. **代码块换行** — 使用 `\n` 表示换行，保持代码缩进
8. **accent 字段** — columns 布局中，最多一个 column 的 accent 为 true（选择最关键的栏目）
9. **highlight 字段** — comparison 布局中，推荐方案的 highlight 为 true

**每张幻灯片的生成步骤：**
- 从原文中定位对应段落
- 提取关键信息
- 按 schema 格式组装 JSON
- 检查必填字段是否齐全

### 3. 组装完整 JSON

将所有幻灯片组装为完整的 JSON 对象：

```json
{
  "title": "从 Step 1 获取的标题",
  "author": "从 Step 1 获取的作者",
  "date": "从 Step 1 获取的日期",
  "slides": [
    // 所有幻灯片
  ]
}
```

### 4. 自检清单

生成完毕后，逐项检查：

- [ ] 第一张和最后一张是 `cover` 布局
- [ ] 所有 `id` 从 1 递增，无跳号
- [ ] 所有 `eyebrow` 和 `title` 非空（封面 eyebrow 可为空字符串）
- [ ] `cards` 布局的每张卡片都有 icon、title、description
- [ ] `list` 布局的 items 数组非空
- [ ] `columns` 布局有 2-3 个 column，每个有 title 和 items
- [ ] `code` 布局的 code 字段非空
- [ ] `table` 布局的 headers 和 rows 列数一致
- [ ] `comparison` 布局的 left 和 right 都有 title 和 items
- [ ] JSON 语法正确（无尾逗号、引号匹配）

如果检查发现问题，立即修复后再输出。

### 5. 输出完整 JSON

将生成的完整 JSON 输出为代码块，供用户预览。

HALT，等待用户审阅。用户可能：
- **确认** → 进入 Step 4 保存文件
- **要求修改某张幻灯片** → 修改后重新输出
- **要求增删幻灯片** → 调整后重新输出
- **要求调整布局** → 修改后重新输出

## NEXT

用户确认后，读取并执行 `./steps/step-04-output.md`
