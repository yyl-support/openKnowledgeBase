"""
成本计算：用配置里的单价 × 真实 token 数算出成本

token 数由 LangChain 的 get_openai_callback() 从模型响应的 usage 字段取到（已实测
火山 ARK 会返回 usage）。但 callback 的 total_cost 只认 OpenAI 官方模型，对
minimax-m3 恒为 0，所以单价必须自己配、自己算。

单价配置在 config/projects.yaml 的 global.pricing 段。

单价来源备查（YAML 里的同名注释会被 save_system_config 的 yaml.dump 清掉，
所以在此留一份，见 docs/phase6-impl-report.md 的遗留问题）：

- minimax-m3: $0.60 / $2.40 每百万 token，来源 MiniMax 官方公开价。
- deepseek-v4-flash: $0.44 / $1.32。单一来源 morphllm.com 称这是 2026-08-16
  调价后的高峰价，与其他五家来源的 $0.14/$0.28 冲突，未能取到官方一手价证实
  （api-docs.deepseek.com 与 deepseek.ai 均被网络策略拦截）。按用户指示取高峰价。
  该条目当前不被代码使用——全量路径隔着 subprocess，callback 取不到 token。
- Qwen/Qwen3-Embedding-8B: ¥0.28 每百万 token（用户提供的 SiliconFlow 实际单价
  ¥0.000280/K tokens），计价币种为 CNY，embedding 只计输入无输出计费。
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# 定价缺失时的默认币种。方案要求：缺 currency 视为 USD 并打 warning。
DEFAULT_CURRENCY = "USD"


def calc_cost(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    pricing: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    按配置单价计算一次调用的成本

    Args:
        model: 模型名（需与 pricing 配置里的键一致）
        prompt_tokens: 输入 token 数
        completion_tokens: 输出 token 数
        pricing: 定价配置（global.pricing）；为 None 视为无定价配置

    Returns:
        Dict[str, Any]:
            {
                "model": str,
                "prompt_tokens": int,
                "completion_tokens": int,
                "total_tokens": int,
                "cost": float,          # 该币种下的金额
                "currency": "USD" | "CNY",
                "priced": bool          # False 表示单价缺失，cost 是兜底的 0
            }
    """
    result = {
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "cost": 0.0,
        "currency": DEFAULT_CURRENCY,
        "priced": False,
    }

    entry = (pricing or {}).get(model)

    # 单价缺失时记 0，但必须打 warning——不能让「没配单价」和「真的没花钱」
    # 在日志里长得一样，那是假成功。
    if not isinstance(entry, dict):
        logger.warning(
            f"模型 {model} 无定价配置，成本记 0"
            f"（token 数仍为真实值: 输入={prompt_tokens}, 输出={completion_tokens}）"
        )
        return result

    input_per_1m = entry.get("input_per_1m")
    output_per_1m = entry.get("output_per_1m")

    if input_per_1m is None or output_per_1m is None:
        logger.warning(
            f"模型 {model} 定价配置不完整"
            f"（input_per_1m={input_per_1m}, output_per_1m={output_per_1m}），成本记 0"
        )
        return result

    currency = entry.get("currency")
    if not currency:
        logger.warning(
            f"模型 {model} 的定价未标注 currency，按 {DEFAULT_CURRENCY} 处理"
        )
        currency = DEFAULT_CURRENCY

    cost = (
        prompt_tokens / 1_000_000 * float(input_per_1m)
        + completion_tokens / 1_000_000 * float(output_per_1m)
    )

    result["cost"] = cost
    result["currency"] = currency
    result["priced"] = True

    logger.info(
        f"成本计算: {model} 输入={prompt_tokens} 输出={completion_tokens} "
        f"→ {cost:.6f} {currency}"
    )

    return result


def split_by_currency(cost_records: list) -> Dict[str, float]:
    """
    按币种分别累加成本，不做汇率折算

    minimax/deepseek 计价为美元，embedding 为人民币。折算需要汇率，而汇率会过期，
    折算出来的合计是个「看着精确其实在编」的数字，所以分列。

    Args:
        cost_records: calc_cost() 返回值的列表

    Returns:
        Dict[str, float]: {"cost_usd": float, "cost_cny": float}
    """
    totals = {"cost_usd": 0.0, "cost_cny": 0.0}

    for record in cost_records:
        if not record:
            continue
        currency = (record.get("currency") or DEFAULT_CURRENCY).upper()
        amount = float(record.get("cost") or 0.0)

        if currency == "CNY":
            totals["cost_cny"] += amount
        elif currency == "USD":
            totals["cost_usd"] += amount
        else:
            logger.warning(f"未知币种 {currency}，计入 USD 列")
            totals["cost_usd"] += amount

    return totals
