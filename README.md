# FnDepot 应用源构建规范

> **版本**: 1.0.0
> **最后更新**: 2025-11-30

## 1. 概述 (Overview)

FnDepot 是运行于 FNOS 上的去中心化第三方应用管理器。本文档详细定义了 FnDepot 应用源（Repository）的构建规范、目录结构及元数据标准。开发者需严格遵循本规范，以确保应用源能被 FnDepot 客户端正确解析、索引及分发。

## 2. 仓库规范 (Repository Standards)

为了保证解析效率与编写方便，项目在制作时大量采用了飞牛官方开发文档的键名，方便开发者识别。应用源仓库必须满足以下硬性条件：

| 项目 | 要求 | 说明 |
| :--- | :--- | :--- |
| **托管平台** | GitHub | 目前仅支持 GitHub 托管的仓库。 |
| **仓库可见性** | Public | 仓库必须设为公开，私有仓库无法被客户端索引。 |
| **仓库命名** | FnDepot | **[强制]** 仓库名称必须严格命名为 `FnDepot`（大小写敏感）。 |
| **分支策略** | main | 客户端默认拉取默认分支的内容。 |

## 3. 目录结构 (Directory Structure)

FnDepot 采用扁平化的目录结构。仓库根目录必须包含全局索引文件 `fnpack.json`，每个应用拥有独立的子目录。

```text
FnDepot/                      # [Root] 仓库根目录
│
├── fnpack.json               # [Core] 全局元数据索引文件
│
├── {app_name}/               # [Dir] 应用目录 (名称即为 Unique ID)
│   ├── ICON.PNG              # [Asset] 应用图标 (强制全大写)
│   ├── {app_name}.fpk        # [Bin] 安装包 (文件名须与目录名一致)
│   ├── README.md             # [Doc] 应用详情文档 (Markdown)
│   └── Preview/              # [Asset] 预览图目录
│       ├── 01.png
│       └── 02.jpg
│
└── ... (其他应用目录)
```

### 3.1 命名约定

*   **应用唯一标识 (`app_name`)**：
    *   仅允许使用 **小写字母 (a-z)**、**数字 (0-9)** 和 **连字符 (-)**。
    *   应用目录名称必须与 `fnpack.json` 中的键名（Key）完全一致。
*   **大小写敏感**：Linux 文件系统对大小写敏感，请严格遵守文件名规范（特别是 `ICON.PNG`）。

## 4. 元数据规范 (fnpack.json)

`fnpack.json` 是应用源的核心数据库，位于仓库根目录。它是一个标准的 JSON 对象，其键（Key）为应用的 `app_name`。

### 4.1 数据结构

```json
{
  "unique-app-id": {
    "display_name": "String",
    "version": "String",
    "desc": "String",
    "labels": "String",
    "author": "String",
    "author_url": "String",
    "bug_report_url": "String",
    "install_type": "Enum",
    "size": "String",
    "history": {
      "version_number": "String"
    }
  }
}
```

### 4.2 字段定义表

| 字段 | 类型 | 必填 | 描述与约束 |
| :--- | :--- | :---: | :--- |
| **Key** | String | ✅ | 应用唯一标识。必须与应用文件夹名称完全一致。 |
| `display_name` | String | ✅ | 客户端展示的应用名称（UI 显示用）。 |
| `version` | String | ✅ | 当前版本号（建议遵循 SemVer 规范，如 1.0.0）。 |
| `desc` | String | ✅ | 应用简介。支持使用 `\n` 进行换行控制。 |
| `labels` | String | ✅ | 分类标签。多个标签使用半角逗号 `,` 分隔（无空格）。 |
| `download_url` | String | 可选 | 下载地址。建议 Release 发布后填写；若 fpk 小于 100MB 可不填写。 |
| `author` | String | ✅ | 开发者或维护团队名称。 |
| `author_url` | String | ✅ | 开发者主页/仓库链接 (HTTP/HTTPS)。 |
| `bug_report_url` | String | ✅ | 问题反馈链接 (HTTP/HTTPS)。 |
| `install_type` | String | ✅ | 安装目标路径类型。`"系统空间"` 或 `"存储空间"`。 |
| `size` | String | ✅ | 安装包体积。仅填写数字，单位默认为 **MB**。 |
| `history` | Object | ✅ | 版本更新记录。<br>**Key**: 版本号; **Value**: 更新日志内容。 |

## 5. 资源文件规范 (Assets Specification)

### 5.1 图标 (ICON.PNG)
*   **路径**: `/{app_name}/ICON.PNG`
*   **格式**: PNG
*   **尺寸**: 建议 256x256
*   **注意**: 文件名必须为 **`ICON.PNG`**（全大写），否则客户端无法获取。

### 5.2 安装包 (.fpk)
*   **路径**:
    *   **模式1**（fpk < 100MB）：`/{app_name}/{app_name}.fpk`
    *   **模式2**（fpk ≥ 100MB）：通过 Release 发布
*   **格式**: FNOS 标准安装包格式 (.fpk)
*   **注意**: 文件名必须严格匹配 `{app_name}.fpk`。

### 5.3 预览图 (Preview/)
*   **路径**: `/{app_name}/Preview/`
*   **支持格式**: `.png`, `.jpg`, `.jpeg`, `.webp` 等

## 6. 完整配置示例 (Configuration Example)

```json
{
  "fntermx": {
    "display_name": "FntermX 终端",
    "desc": "专为飞牛 NAS 打造的现代化 Web 终端\n支持 SSH 连接与会话管理",
    "labels": "工具,终端,SSH,DevOps",
    "version": "1.0.8",
    "author": "EWEDL",
    "author_url": "https://github.com/EWEDLCM",
    "bug_report_url": "https://github.com/EWEDLCM/FntermX/issues",
    "install_type": "系统空间",
    "size": "15",
    "history": {
      "v1.0.8": "性能优化与 Bug 修复",
      "v1.0.7": "新增深色模式支持",
      "v1.0.0": "Initial Release"
    }
  }
}
```

## 7. 维护与更新 (Maintenance)

FnDepot 客户端包含自动同步机制。开发者只需对 GitHub 仓库进行常规的 Git 操作即可完成发布：

1.  **更新二进制文件**：替换对应的 `.fpk` 文件。
2.  **更新元数据**：修改 `fnpack.json` 中的 `version` 字段并追加 `history` 记录。
3.  **推送 (Push)**：将更改推送到 GitHub 的默认分支。

客户端会在同步源信息时检测到 `version` 字段变更，正确响应状态。

## 8. 法律与免责声明 (Disclaimer)

*   **责任限制**：FnDepot 仅提供分发协议与索引服务。应用开发者需对其提交的代码安全性、稳定性及版权合规性负全部责任。
*   **安全合规**：严禁在应用源中包含恶意代码、后门程序或未经授权的侵权内容。违规仓库将被 FnDepot 索引服务拉黑并公示。
*   **数据安全**：开发者应在文档中明确告知用户应用的权限要求及潜在风险。

***
*FnDepot Protocol Version 1.0*
