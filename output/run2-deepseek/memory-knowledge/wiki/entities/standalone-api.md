---
type: entity
title: standalone_api
description: 提供 run_standalone_api() 的模块，负责实际拉起 ForumBot 独立 API 服务。
sources: ["api_main.txt"]
kind: module
tags: ["ForumBot", "API"]
---

# standalone_api

## 定义

`standalone_api` 是提供 `run_standalone_api()` 启动函数的模块，接收 host、port、config_file 参数并实际拉起 [[ForumBot 独立 API 服务]]。

## 关键属性

- 导出函数：`run_standalone_api(host, port, config_file)`
  - `host`：服务监听地址
  - `port`：服务监听端口
  - `config_file`：配置文件路径，可为 `None`
- 被 [[api_main]] 以关键字参数形式调用

## 关系

- 由 [[api_main]] 入口脚本委托调用
- 启动 [[ForumBot 独立 API 服务]] 实例
- 属于 [[ForumBot]] 平台，是 [[独立 API 服务部署模型]] 的实际启动器
