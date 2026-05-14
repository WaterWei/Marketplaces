---
name: git-commit-cn
description: '中文规范化 Git 提交，自动分析变更内容生成中文提交信息，提交后自动推送到远程。Use when user says "提交", "commit", "git提交", "推送", "commit and push"'
allowed-tools: Bash
---

# Git Commit — 中文规范化提交

## 概述

分析代码变更差异，生成符合规范的中文提交信息，提交后自动推送到远程仓库。

## 提交信息格式

```
<类型>[可选范围]: <标题>

[可选正文]

[可选脚注]
```

## 提交类型

| 类型 | 说明 |
|------|------|
| 特性 | 新功能 |
| 修复 | Bug 修复 |
| 文档 | 仅文档变更 |
| 格式 | 代码格式（不影响逻辑） |
| 重构 | 代码重构（非特性非修复） |
| 性能 | 性能优化 |
| 测试 | 增加/修改测试 |
| 构建 | 构建系统/依赖 |
| 持续集成 | CI 配置变更 |
| 杂项 | 日常维护 |
| 回退 | 回退提交 |

### 破坏性变更

在类型后加 `!`，或在脚注中注明：

```
特性!: 移除已废弃的 API

修复: 修改配置继承逻辑

破坏性变更: `extends` 字段行为已变更
```

## 工作流程

### 1. 分析变更

```bash
# 已暂存文件
git diff --staged

# 未暂存文件
git diff

# 查看状态
git status --porcelain
```

### 2. 暂存文件

无已暂存文件时，按逻辑分组暂存：

```bash
# 暂存特定文件
git add path/to/file1 path/to/file2

# 按模式暂存
git add src/components/*.tsx

# 交互式暂存
git add -p
```

**绝不提交敏感文件：** .env、credentials.json、密钥文件、.env.local 等。

**注意：** `git add -p` 需要交互式终端，在不支持交互的 CLI 环境中请改用 `git add <文件路径>` 显式暂存。

### 3. 生成提交信息

根据差异分析确定：

- **类型**：属于哪种变更？
- **范围**：涉及哪个模块？
- **标题**：一行概括变更内容（现在时，祈使语气，≤72 字）
- **正文**（可选）：详细说明变更原因和影响

### 4. 执行提交

```bash
# 单行提交
git commit -m "<类型>[范围]: <标题>"

# 多行提交
git commit -m "$(cat <<'EOF'
<类型>[范围]: <标题>

<正文>

<脚注>
EOF
)"
```

### 5. 推送到远程

提交成功后，检查是否存在远程仓库：

```bash
# 获取当前分支名
branch=$(git rev-parse --abbrev-ref HEAD)

# 检查远程
git remote -v

# 推送到当前分支（首次自动设 upstream）
git push -u origin "$branch"
```

推送被拒时（远程有新提交），提示用户先拉取再重试：

```bash
git pull --rebase && git push
```

## 规范

- 一个提交一个逻辑变更
- 标题用现在时、祈使语气：`添加登录功能` 而非 `添加了登录功能`
- 标题不超过 50 字
- 正文说明原因而非方式
- 关联 Issue：`关闭 #123`、`关联 #456`

## 安全规则

- 绝不更新 git 配置
- 绝不执行破坏性命令（--force、hard reset），除非用户明确要求
- 绝不跳过 hooks（--no-verify），除非用户要求
- 绝不强制推送到 main/master
- 提交因 hooks 失败时，修复问题后创建新提交（绝不 amend）
