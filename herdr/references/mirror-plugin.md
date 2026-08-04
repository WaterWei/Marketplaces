# herdr-mirror 远程镜像插件

将远程 herdr server 的 workspace/pane 镜像到本地 sidebar，实现跨主机 agent 操控。

来源：https://github.com/nikok6/herdr-mirror (v0.1.7)

## 安装

```bash
herdr plugin install nikok6/herdr-mirror --yes
```

## 配置

`~/.config/herdr/plugins/config/mirror/hosts.toml`：

```toml
[hosts.myserver]
target = "user@remote-host"
```

需要 SSH key 认证到远程主机。

## Plugin Actions

```bash
# 启动/恢复镜像 daemon
herdr plugin action invoke mirror start

# 状态查看
herdr plugin action invoke mirror status

# 单次同步（不启动 daemon）
herdr plugin action invoke mirror once

# 暂停（workspace 保留，resume 用 start）
herdr plugin action invoke mirror pause

# 远程分屏
herdr plugin action invoke mirror remote-split-right
herdr plugin action invoke mirror remote-split-down

# 远程创建
herdr plugin action invoke mirror remote-new-workspace
herdr plugin action invoke mirror remote-new-tab

# 恢复/清理
herdr plugin action invoke mirror restore     # 恢复已关闭的 mirror
herdr plugin action invoke mirror teardown    # 停 daemon + 关所有 mirror workspace
```

## 管理

```bash
herdr plugin list                                # 已装插件
herdr plugin config-dir mirror                   # 配置目录路径
herdr plugin log list --plugin mirror --limit 5  # 查看日志
herdr plugin action list                         # 全部 action
```

## 工作方式

1. `mirror start` 启动 daemon，通过 SSH 连接远程 herdr server
2. 远程 workspace 自动出现在本地 sidebar
3. 可用标准 herdr 命令操作远程 pane：`herdr pane run <remote-pane-id> "cmd"`
4. 远程输出实时镜像到本地：`herdr pane read <remote-pane-id> --source recent-unwrapped`
5. `workspace.focused` 事件自动触发 `ensure`（保持同步）
