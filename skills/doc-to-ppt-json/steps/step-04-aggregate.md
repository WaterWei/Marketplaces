# Step 4: 验证、聚合与输出

## 目的

先逐片验证 JSON 质量，再聚合为最终 PPT Deck JSON 文件。

## 执行步骤

### 1. 自动修复 JSON 常见问题

LLM 生成的 JSON 常有未转义引号、尾部逗号等问题。先运行修复：

```bash
python3 {skill-root}/scripts/aggregate_json.py --repair --chunks-dir "{output_dir}/chunks"
```

此步骤会自动修复：
- 字符串内的中文引号 `""` → `「」`（避免与 JSON 分隔符混淆）
- 字符串内未转义的 `"` → `\"`
- 字符串内裸换行符 → `\n`
- 尾部逗号 `,]` 或 `,}`

修复后的文件会原地更新。查看输出报告，确认修复了哪些文件。

### 2. 逐片验证

运行验证脚本：

```bash
python3 {skill-root}/scripts/aggregate_json.py --validate --chunks-dir "{output_dir}/chunks"
```

### 3. 处理验证结果

**如果全部通过：** → 跳到步骤 5（聚合）

**如果有失败：** → 执行以下修复流程：

#### 3a. 自动重试

对验证失败的分片，重新调用 subagent 处理：

```
Agent(
  description: "修复 chunk_NNN JSON",
  prompt: """
读取 {output_dir}/chunks/chunk_NNN.md，重新生成 JSON。

上次生成的 JSON 验证失败，错误如下：
{具体错误列表}

请特别注意修复这些错误。

{完整 schema.md 内容}

将修复后的 JSON 写入: {output_dir}/chunks/chunk_NNN.json
"""
)
```

重试后重新运行验证。

#### 3b. AI 修复（重试仍失败时）

如果重试后仍然验证失败，由主 agent 直接读取有问题的 JSON 文件和对应的 MD 文件，手动修复 JSON 结构问题（如缺少必填字段、格式错误等），然后写回文件。

修复后再次运行验证，确保通过。

#### 3c. 无法修复

如果某个分片经过重试和 AI 修复后仍然无法通过验证，**HALT** 并报告：
- 失败的分片编号
- 所有验证错误
- 建议用户手动检查原始文档对应部分

### 4. 用户确认验证结果

展示验证报告：

```
逐片验证结果：

编号 | 文件                | 状态 | slides
-----|--------------------|----- |-------
001  | chunk_001.json     | PASS | 5
002  | chunk_002.json     | PASS | 3
003  | chunk_003.json     | PASS | 4
...

总计: N 个分片, X 张 slides — 全部通过 ✓
```

**HALT** 等待用户确认后继续聚合。

### 5. 聚合

运行聚合脚本：

```bash
python3 {skill-root}/scripts/aggregate_json.py --aggregate \
  --chunks-dir "{output_dir}/chunks" \
  --output "{output_dir}/output.json" \
  --title "{title}" \
  --author "{author}" \
  --date "{date}"
```

聚合脚本会：
1. 按编号顺序读取所有 chunk_NNN.json
2. 合并 slides 数组
3. 全局重编号 slide ID（从 1 开始连续递增）
4. 构建最终 JSON（含 title、author、date、slides）
5. 写入输出文件
6. 执行最终整体验证

**如果聚合中断：** 脚本会报告哪个分片出了问题。回到步骤 3 修复该分片。

### 6. 输出使用说明

展示完成信息：

```
🎉 文档转 PPT JSON 完成！

📄 输入: {input_file}
📊 统计: {N} 个分片 → {M} 张 slides
📁 输出: {output_dir}/output.json

文件大小: XXX KB
```

询问用户是否需要：
1. **预览** — 启动 PPT Deck 开发服务器查看效果
2. **调整** — 编辑某些 slide 的内容或布局
3. **完成** — 结束工作流

## 完成
