# 校验记录：codearts-workflow-image

生成时间：2026-08-14 19:08:25
三方件：raw.json
校验条目数：2
冲突数：0

## 校验说明

本次校验执行了以下类型的核验：

### 1. 规则冲突核验
对 raw.json 中的事实性断言与 preprocess.json 的 rule_facts 进行了比对。
核验了 Go 版本、Dockerfile 基础镜像、依赖声明等关键事实。

### 2. 结构性核验
对 5/23 个 core 文件进行了结构性断言校验。
抽样检查了文件存在性、基本结构与 raw.json 描述的一致性。

### 3. 作用域核验
对 1 个关键字段进行了全仓取值分布统计：

**schedulerName** 分布：
  - `default-scheduler`: 6 次
  - `volcano`: 1 次

### 4. 枚举完整性核验
检查了 NPU 类型、测试用例等枚举是否完整。

## 冲突明细

无冲突发现。

经核验，raw.json 中的事实性断言与 preprocess.json 的 rule_facts 及仓库实际内容一致。
抽样检查的 core 文件结构性描述准确。
关键字段的作用域表述未发现明显错误。
