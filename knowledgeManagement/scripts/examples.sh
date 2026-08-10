#!/bin/bash
# 使用示例脚本

# 示例1：使用 open-zread 提取并生成架构文档
echo "示例1：使用 open-zread 生成架构文档"
python3 extract.py \
  --adapter zread \
  --repo /tmp/oz-trial/forum-reply-robot \
  --output-type architecture \
  --output ./output/forum-reply-robot-architecture.md \
  --save-raw

# 示例2：使用 MemoryKnowledge 提取并生成快速开始指南
# 注意：需要先启动 MemoryKnowledge 服务
# echo "示例2：使用 MemoryKnowledge 生成快速开始指南"
# python3 extract.py \
#   --adapter mk \
#   --repo /path/to/your/repo \
#   --output-type quickstart \
#   --output ./output/quickstart.md

# 示例3：使用 Understand-Anything 提取并生成 API 参考
# 注意：需要先启动 UA 服务，且需要确认实际 API
# echo "示例3：使用 UA 生成 API 参考"
# python3 extract.py \
#   --adapter ua \
#   --repo /path/to/your/repo \
#   --output-type api-reference \
#   --output ./output/api-reference.md

echo "完成！"
