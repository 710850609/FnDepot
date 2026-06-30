# FnDepot - 飞牛OS去中心化应用管理器

## 概述

FnDepot 是运行于 FNOS（飞牛OS）上的去中心化第三方应用管理器。它允许用户通过多个社区维护的应用源（Repository）发现、安装和管理第三方应用，避免了单一中心化应用商店的限制。

本文档定义了 FnDepot 应用源的构建规范、目录结构及元数据标准。开发者需严格遵循本规范，以确保应用源能被 FnDepot 客户端正确解析、索引及分发。

## 应用列表

| 应用 | 描述 | 版本 |
|------|------|------|
| [OpenList](OpenList/) | 有韧性、长期治理、社区驱动的 AList 分支，支持多种存储的文件列表程序 | 4.2.2-10 |
| [AdGuardHome](AdGuardHome/) | 免费开源、强大的网络范围广告和跟踪器阻止DNS服务器 | 0.107.77-15 |
| [TaoSync](TaoSync/) | 适用于 OpenList/AList v3+ 的自动化同步工具 | 0.3.2-9 |
| [SmartDNS](SmartDNS/) | 开源DNS服务器，用于加速和优化网络访问 | 48.2-006 |
| [DBland](DBland/) | Go语言实现的Web版本数据库连接工具，支持MySQL、Oracle、SQLite | 1.1.1-003 |

## fnpack.json 元数据规范

`fnpack.json` 是 FnDepot 的核心配置文件，具体规范见文档：
- [FnDepot规范文档](https://github.com/EWEDLCM/FnDepot/blob/main/README.md)
- [飞书文档](https://ecn6sp7e44q3.feishu.cn/wiki/VSrmwqtjhigaygkWkyoceEvvnlb)


## 应用讨论
- [QQ群聊 767315692](https://qm.qq.com/q/MDHN8GlI4s)