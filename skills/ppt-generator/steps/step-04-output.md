# Step 4: 保存与验证

## 目标

将确认的 JSON 保存为文件，验证格式正确性，并提供使用说明。

## 执行流程

### 1. 确定文件名

询问用户保存路径，提供默认建议：

- 默认路径：`{project-root}/public/presentations/{slug}.json`
- `{slug}` 由演示标题生成：中文转拼音或使用英文关键词，kebab-case
- 示例：标题"React 19 新特性分享" → `react-19-new-features.json`

如果 `public/presentations/` 目录不存在，先创建。

### 2. 写入文件

将 Step 3 确认的 JSON 写入目标路径。使用 `JSON.stringify(data, null, 2)` 格式化输出，确保：
- 2 空格缩进
- UTF-8 编码
- 无尾逗号

### 3. 验证

写入后执行验证：

**a) JSON 语法验证：**
```bash
python3 -c "import json; json.load(open('文件路径'))"
```
或使用 `bun -e` 验证。

**b) Schema 验证（手动检查）：**
- 读取写入的文件
- 确认顶层有 `title`、`slides` 字段
- 确认 `slides` 是非空数组
- 确认每张 slide 有 `id`、`layout`、`eyebrow`、`title`

### 4. 输出使用说明

向用户展示完成信息：

```
JSON 已保存到: public/presentations/xxx.json
共 X 张幻灯片

使用方式:
1. URL 参数加载: http://localhost:5173/?file=/public/presentations/xxx.json
2. 拖拽文件到演示区域
3. 点击工具栏 ↑ 按钮导入

启动预览: bun run dev
```

### 5. 询问后续

询问用户是否需要：
- **立即预览** — 启动 dev server 并打开对应 URL
- **继续编辑** — 调整某张幻灯片
- **完成** — 结束工作流

## 工作流完成
