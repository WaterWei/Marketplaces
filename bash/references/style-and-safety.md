# Bash 安全与风格参考

来源：Google Shell Style Guide (39K stars) + bahamas10/bash-style-guide + ShellCheck + X/Twitter agent 安全讨论

## 严格模式

```bash
#!/usr/bin/env bash
set -euo pipefail
```

- `set -e` — 命令失败立即退出
- `set -u` — 未定义变量报错
- `set -o pipefail` — 管道中任一命令失败则整体失败

## Google Shell Style Guide 核心规则

### 何时用 Shell

- 只用于小工具或简单包装脚本
- 超过 100 行或含复杂控制流 → 用 Python/TS 重写
- 需要数据结构（hash/array 嵌套）→ 换语言

### 文件头

```bash
#!/usr/bin/env bash
# Brief description of what script does.
```

### 函数

```bash
my_func() {
  local arg="$1"
  # ...
}
```

- 不用 `function` 关键字
- 所有变量必须 `local`
- `main() { ... }; main "$@"` 结构（>50 行时）

### 控制结构

```bash
# then/do 与 if/while 同行
if [[ -f "$file" ]]; then
  echo "found"
fi

for item in "${array[@]}"; do
  echo "$item"
done
```

### 引号

1. 始终引号包裹变量：`"$var"`
2. 数组展开：`"${array[@]}"`
3. 命令替换：`"$(cmd)"`
4. 仅 `$?`, `$#`, `$$`, `$!` 可不引号

### 测试

- 用 `[[ ]]`（不用 `[ ]`）
- 字符串比较用 `==`
- 正则用 `=~`

### 命令替换

- 用 `$(cmd)`（不用反引号）
- 嵌套：`$(cmd1 "$(cmd2)")`

## Agent 安全清单

### 必须

1. 每条命令有超时意识（`timeout N cmd` 或设计上不可能死循环）
2. 输出截断（`| head -N`），防止无界输出
3. 操作前确认目标（ls/git status/herdr pane get）
4. 不执行用户输入拼接的命令（防注入）
5. 敏感文件操作前确认 `git status`；必要时备份或征得用户同意
6. 默认只操作当前 workspace/repo，出界先确认
7. 密钥不进 argv（`TOKEN=xxx cmd` 会进 atuin + process list）；用 env 文件

### 禁止

- `rm -rf` 没有明确限定路径
- `curl <url> | bash`（不审查的远程脚本）
- `chmod 777`
- `eval "$user_input"`
- 无 timeout 的 `while true` / `find /`
- 写 `/etc`、`/usr` 等系统目录

### 最佳实践

- 用 `mktemp` 创建临时文件
- 用 `trap` 清理临时资源
- 幂等设计（重跑不出错）
- ShellCheck 零警告

## 为什么 Agent 默认 Bash

1. **可移植** — 所有 Linux/macOS/WSL 都有
2. **文档最全** — 训练数据覆盖最广
3. **sandbox 生态** — 隔离工具默认支持 bash
4. **分工清晰** — bash 做编排，uv/bun 做计算

不要试图用 zsh/fish/nushell 特性 — agent 脚本必须假设 bash 4.x+ 环境。

## ShellCheck 常见规则

| 代码 | 含义 | 修复 |
|------|------|------|
| SC2086 | 变量未引号 | `"$var"` |
| SC2046 | 命令替换未引号 | `"$(cmd)"` |
| SC2006 | 反引号 | `$(cmd)` |
| SC2004 | 多余 `$` | `(( var++ ))` |
| SC2155 | declare+assign 一行 | 分两行 |
| SC2162 | read 没 -r | `read -r` |
| SC2034 | 未使用变量 | 删除或 `export` |
