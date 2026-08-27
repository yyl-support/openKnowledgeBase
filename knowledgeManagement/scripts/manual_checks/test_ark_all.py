#!/usr/bin/env python3
"""
火山 ARK API 完整测试
测试所有可能的配置组合
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

print("=" * 80)
print("火山 ARK API 完整测试")
print("=" * 80)

# 测试配置
api_keys = [
    os.getenv("ARK_API_KEY"),  # 从环境变量或 .env 读取
]

models = [
    "minimax-m3",
    "glm-5.3",
    "MiniMax-M3",
    "GLM-5.3"
]

base_urls = [
    "https://ark.cn-beijing.volces.com/api/v3",
    "https://ark.cn-beijing.volces.com/api/coding"
]

test_prompt = "你好"

success_count = 0
total_tests = len(api_keys) * len(models) * len(base_urls)

print(f"\n将测试 {total_tests} 种配置组合\n")

for api_key in api_keys:
    for model in models:
        for base_url in base_urls:
            test_name = f"API Key: {api_key[-10:]}... | Model: {model:12} | URL: {base_url.split('/')[-1]}"

            try:
                llm = ChatOpenAI(
                    model=model,
                    openai_api_key=api_key,
                    openai_api_base=base_url,
                    timeout=10
                )

                response = llm.invoke(test_prompt)

                print(f"✅ {test_name}")
                print(f"   响应: {response.content[:80]}...")
                print()

                success_count += 1

            except Exception as e:
                error_msg = str(e)
                if "404" in error_msg:
                    print(f"❌ {test_name} - 404 Not Found")
                elif "401" in error_msg:
                    print(f"❌ {test_name} - 401 Unauthorized")
                elif "timeout" in error_msg.lower():
                    print(f"❌ {test_name} - Timeout")
                else:
                    print(f"❌ {test_name} - {error_msg[:50]}...")

print("\n" + "=" * 80)
print(f"测试完成: {success_count}/{total_tests} 成功")
print("=" * 80)

if success_count > 0:
    print("\n✅ 找到可用的配置！")
else:
    print("\n❌ 所有配置都失败，可能原因:")
    print("   1. API Key 无效或过期")
    print("   2. 没有开通模型访问权限")
    print("   3. base_url 不正确")
    print("   4. 模型名称不正确")
