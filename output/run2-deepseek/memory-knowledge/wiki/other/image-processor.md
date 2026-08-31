---
type: other
sources:
  - image_processor.txt
---

# ImageProcessor

## 定义

[[ForumBot]] 中 `src` 包内的图片处理模块（`src/image_processor.py`）。核心职责是「提取图片标签 → 调用多模态模型生成描述 → 用描述增强/替换原文」。

## 关键属性

| 属性 | 说明 |
| --- | --- |
| `config` | 模块配置；读取 `config['api']`（`base_url`、`api_key`）与 `config['image_processing']`（`model1`/`model2`/`model3`、可选 `base_url`） |
| `client` | 基于 [[多模态模型服务]] 配置创建的 `openai.OpenAI` 客户端 |
| `model_list` | 按顺序排列的三个多模态模型，用于故障转移 |

## 核心方法

| 方法 | 职责 |
| --- | --- |
| `extract_image_info_from_text(text)` | 用正则 `\[img: \((.*?)\)\]` 提取图片标签；`http` 开头视为绝对路径，否则以基准 URL（默认 [[OpenUBMC 论坛]]）`urljoin` 解析 |
| `process_image_content(image_url, context, topic_id)` | 处理单张图片；URL 含 `user_avatar` 返回 `USER_AVATAR`；依据 `context` 选择提示词并调用模型 |
| `_call_multimodal_model(image_url, prompt, topic_id)` | 按 `model_list` 顺序调用模型，失败时记日志并切换下一个；提供 `topic_id` 时记录 token 用量 |
| `enhance_text_with_image_descriptions(text, context, topic_id)` | 汇总流程：提取 → 描述 → 标签替换为 `[图片: 描述]`，头像标签直接删除 |

## 关系

- 属于 [[ForumBot]] 系统平台（src 包内的模块）。
- 依赖 [[logging_config]]：`from .logging_config import main_logger`，记录图片处理错误与模型切换日志。
- 依赖 [[token_tracker]]：`token_tracker.add_usage(topic_id, prompt_tokens, completion_tokens, total_tokens)` 按主题记账。
- 调用 [[多模态模型服务]]：通过 OpenAI 兼容接口 `chat.completions.create` 传入文本与图片消息。
- 实现 [[图片标签提取与增强机制]]：是机制的实际代码实现。
- 图片来源：[[OpenUBMC 论坛]] 的帖子文本是 `[img: (...)]` 标签的载体，也是相对路径的默认基准 URL。

## 相关概念

- [[图片标签提取与增强机制]] — 本模块实现的文本增强流程
- 来源：[[image_processor.txt]]
