# Claude 项目指令

## 目录规则

- `codeSource/` 存放外网代码事实和服务知识来源。
- `knowledgeManagement/` 存放知识管理 CLI、架构、契约和长期规则。
- `output/` 是生成文档的唯一正式输出目录。
- 不得将生成的 Wiki、仓库全景、报告或其他正式知识文档写入 `codeSource/`、`knowledgeManagement/` 或仓库根目录。
- `.knowledge/`、实验候选、调试响应、测试输出和日常工作记录不得提交。

## 知识文档生成规则

- 遵守 `knowledgeManagement/knowledge-core/schemas/wiki-output-contract.md`。
- “构建信息”始终位于最后。
- 使用“整体概述”，不得使用“三十秒概览”。
- 可读 Markdown 不逐条展示块 ID 和行号；详细证据保留在 CLI Claim 元数据中。
- 数据、统计、清单矩阵、状态对照和方案比较使用 Markdown 表格。
- 代码流程、架构、组件关系和系统交互在证据充分时使用 GitHub Mermaid。
- 生成后运行 `wiki validate --file`，不得绕过失败的校验。
- 文档保持未审核候选状态，直至人工审核并通过 CLI 批准。

## 溯源边界

- 来源 URL 的存在不等于公开可访问，受控来源不得描述为公开可验证。
- 不从不完整资料推断运行架构、调用关系、部署拓扑或安全细节。
- 人类可读文档与机器可审计证据分开保存，但不能损失可追溯性。
