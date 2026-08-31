---
type: source
title: api_main.txt
description: ForumBot 独立 API 服务命令行入口脚本 api_main.py 的源码摘要。
sources: ["api_main.txt"]
source_type: other
tags: ["ForumBot", "API", "入口脚本"]
---

# api_main.txt

## 来源文档摘要

本文档为 `api_main.py` 的源代码，是 ForumBot 独立 API 服务的命令行启动入口脚本。

主要职责：

- 将脚本所在目录及 `src` 子目录注入 `sys.path`，确保 `standalone_api` 与 `src.ForumBot` 包可被导入。
- 通过 `argparse` 解析 `--host`（默认 `127.0.0.1`）、`--port`（默认 `5085`）、`--config`（默认 `None`）三个参数。
- 初始化日志：从 `src.ForumBot.logging_config` 导入 `main_logger`。
- 调用 [[standalone_api]] 模块中的 `run_standalone_api(host, port, config_file)` 启动 [[ForumBot 独立 API 服务]]。
- 捕获 `KeyboardInterrupt`（记录"API服务已停止"）与异常（记录"API服务启动失败"）。

## 关键代码路径

1. 路径注入：`sys.path.insert(0, current_dir)` 与 `sys.path.insert(0, os.path.join(current_dir, 'src'))`
2. 参数解析：`argparse.ArgumentParser(description='ForumBot 独立API服务')`
3. 日志提示：启动地址、配置文件路径或"自动查找配置文件"
4. 委托启动：`run_standalone_api(host=args.host, port=args.port, config_file=args.config)`

## 相关页面

- [[api_main]] — 对应模块实体
- [[独立 API 服务部署模型]] — 该脚本对应的部署形态
- [[命令行入口启动流程]] — 该脚本实现的启动流水线
