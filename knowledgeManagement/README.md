# Knowledge Management

本目录承载知识管理系统的可运行工程、正式架构和生成契约。

| 路径 | 用途 |
|---|---|
| `knowledge-core/` | Source 到 Wiki 的 CLI 流水线 |
| `architecture/` | 正式架构设计与实现记录 |
| `../output/` | 所有正式生成文档的统一输出目录 |

运行 CLI 时应从仓库根目录执行，使默认 `--output-dir output` 指向根级输出目录。实验状态保存在被忽略的 `.knowledge/` 工作区，不得提交。
