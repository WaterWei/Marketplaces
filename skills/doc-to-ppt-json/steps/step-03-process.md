# Step 3: Subagent 并发处理

## 目的

使用 Claude Code 的 Agent 工具并发将每个分片 Markdown 文件转换为 PPT Deck JSON。

## 执行步骤

### 1. 准备 schema 内容

读取 `{skill-root}/schema.md` 的完整内容，作为 subagent prompt 的一部分。**每个 subagent 都必须收到完整 schema**。

### 2. 读取分片清单

读取 `{output_dir}/chunks/manifest.json`，获取所有分片信息。

### 3. 按批次并发处理

按 `max_concurrency` 分批发射 Agent 调用。每批中的所有 Agent 调用**必须在同一条消息中发出**（这样才能真正并发执行）。

**单个 subagent 的调用模式：**

```
Agent(
  description: "处理 chunk_NNN → JSON",
  prompt: """
你是一个文档转 PPT 幻灯片的专家。

## 任务
将以下 Markdown 片段转换为 PPT Deck JSON 格式的 slides 数组。

## 输入文件
读取文件: {output_dir}/chunks/chunk_NNN.md

## 片段信息
- 分片编号: NNN
- 分片类型: {section_type}
- 建议布局: {layout_hint}

## JSON Schema（必须严格遵循）
{完整 schema.md 内容}

## 输出要求
1. 生成一个 JSON 对象，包含 "slides" 数组
2. 每个 slide 必须有: id, layout, eyebrow, title（以及 layout 特定的必填字段）
3. id 从 1 开始递增（后续聚合时会全局重编号）
4. eyebrow 使用英文大写标签
5. 内容忠实于原文，不编造
6. 每行文字不超过 30 个字符
7. 根据内容特征选择最合适的布局类型

## 输出文件
将生成的 JSON 写入: {output_dir}/chunks/chunk_NNN.json

返回:
1) 完成状态
2) 生成的 slide 数量
3) 使用了哪些布局类型
"""
)
```

### 4. 批次调度逻辑

```
分片总数: N
并发数: C (max_concurrency)
批次数: ceil(N / C)

第 1 批: chunk_001 ~ chunk_C     → 并发执行
第 2 批: chunk_(C+1) ~ chunk_2C  → 并发执行
...
最后一批: 剩余分片              → 并发执行
```

每一批的所有 Agent 调用必须在**同一条消息**中发出。

### 5. 跟踪处理进度

每批完成后，输出进度：

```
📊 处理进度: [批次数/总批次] ████████░░░░ 67%

✅ chunk_001: 5 slides (cover, content, content, list, content)
✅ chunk_002: 3 slides (list, table, content)
✅ chunk_003: 4 slides (content, cards, content, content)
```

### 6. 处理 subagent 失败

如果某个 subagent 失败或返回异常：

1. 记录失败的分片编号和错误信息
2. **继续处理**剩余分片（不中断整个流程）
3. 所有批次完成后，对失败的分片**重试 1 次**
4. 重试仍失败的分片，记录下来供 Step 4 由 AI 修复

### 7. 验证输出文件存在

所有 subagent 完成后，检查每个 `chunk_NNN.json` 文件是否已生成。如果有缺失：

```
已生成: chunk_001.json, chunk_002.json, ..., chunk_NNN.json
缺失: 无 ✓
```

如果仍有缺失（重试后仍失败），标记这些分片为"待修复"，在 Step 4 中处理。

### CHECKPOINT

展示所有分片的处理结果。**HALT** 等待用户确认。

如果用户对某些分片的 slides 不满意，可以手动编辑对应的 `chunk_NNN.json` 文件后继续。

## NEXT

Read fully and follow `./steps/step-04-aggregate.md`
