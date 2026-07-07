# FnDepot 应用源

自动拉取 GitHub 上符合 FnDepot 商店规范的应用源，并将其注入到 FnDepot 商店中。

## 功能

- **自动拉取源列表**：从 [FnDepot 仓库](https://github.com/710850609/FnDepot) 的 `repo_list.txt` 获取最新应用源
- **GitHub 加速**：使用GitHub加速代理，自动重试
- **定时更新**：支持配置每 N 小时自动执行一次，利用飞牛系统应用检查机制触发，无需额外常驻进程
- **Web 管理界面**：提供可视化配置页面，支持手动执行、查看日志、设置定时任务

## 构建

```bash
# 开发构建
./build.sh release=false arch=x86_64

# 发布构建（需要指定版本号、平台、系统最低版本）
./build.sh 0.0.2 x86 1.1.8 release=true arch=x86_64

# 一键发布多架构
./build-release.sh
```

## 依赖

- Python 3.11+
- 飞牛 NAS 系统
