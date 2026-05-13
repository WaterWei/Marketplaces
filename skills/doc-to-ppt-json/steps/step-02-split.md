# Step 2: 文档分割

## 目的

调用 Python 脚本将大型 Markdown 文档分割为带编号的片段文件。

## 执行步骤

### 1. 执行分割脚本

运行以下命令：

```bash
python3 {skill-root}/scripts/split_document.py "{input_file}" --config "{config_path}" --output-dir "{output_dir}/chunks"
```

### 2. 检查执行结果

**如果脚本报错（退出码非 0）：**
- 读取 stderr 输出，向用户报告具体错误
- 常见问题：
  - "没有标题匹配到任何 section_types 模式" → 检查配置文件的 pattern
  - "分段内容为空" → 文档结构异常
- **HALT**，请用户调整配置或文档后重试

**如果脚本成功：**
- 确认输出目录中生成了以下文件：
  - `chunk_001.md` ~ `chunk_NNN.md`（带编号的分片文件）
  - `manifest.json`（分片清单）

### 3. 读取并展示清单

读取 `{output_dir}/chunks/manifest.json`，向用户展示分片结果：

```
分割完成！共 N 个分片：

编号 | 类型           | 标题                           | 行数
-----|---------------|-------------------------------|-----
001  | cover         | 大差÷小差 · 统一模型天梯          | 12
002  | toc           | 第一部分：总目录                  | 25
003  | phase         | 第一阶段：模型的发现与建立         | 8
004  | main_ladder   | 主梯 1：鸡兔同笼                 | 5
005  | sub_ladder    | 1-1 梯：画脚游戏                 | 42
...
```

### 4. 验证分片完整性

快速检查：
- 分片编号是否连续（1 ~ N）
- 每个分片文件是否非空
- manifest.json 中记录的数量是否与实际文件数一致

如果有任何异常，**HALT** 报告问题。

### CHECKPOINT

展示分片结果。**HALT** 等待用户确认。

如果用户觉得分片不合理（太细或太粗），可以调整 `customize.toml` 中的 `section_types` 配置后重新运行此步骤。

## NEXT

Read fully and follow `./steps/step-03-process.md`
