"""
Phase 6 成本统计测试

含一个真实 LLM 调用用例（断言 token > 0 且 cost > 0），
以及单价缺失时记 0 且打 warning 的用例。
"""

import logging
import os
import pytest

import config.env  # noqa: F401  收集期就加载 .env，否则 skipif 读不到密钥
from config.pricing import calc_cost, split_by_currency
from .conftest import make_knowledge_package

PRICING = {
    "minimax-m3": {
        "input_per_1m": 0.60,
        "output_per_1m": 2.40,
        "currency": "USD",
    },
    "Qwen/Qwen3-Embedding-8B": {
        "input_per_1m": 0.28,
        "output_per_1m": 0.0,
        "currency": "CNY",
    },
}


def test_calc_cost_basic():
    """按配置单价算出成本"""
    r = calc_cost("minimax-m3", 1_000_000, 1_000_000, PRICING)
    assert r["priced"] is True
    assert r["currency"] == "USD"
    assert r["cost"] == pytest.approx(3.0)
    assert r["total_tokens"] == 2_000_000


def test_calc_cost_missing_price_warns(caplog):
    """单价缺失 → cost=0 且必须打 warning（不能和「真的没花钱」混淆）"""
    caplog.set_level(logging.WARNING)

    r = calc_cost("some-unpriced-model", 1000, 500, PRICING)

    assert r["cost"] == 0.0
    assert r["priced"] is False
    # token 数仍是真实值，只是算不出钱
    assert r["prompt_tokens"] == 1000
    assert r["completion_tokens"] == 500
    assert "无定价配置" in caplog.text
    assert "some-unpriced-model" in caplog.text


def test_calc_cost_no_pricing_config_at_all_warns(caplog):
    """pricing 整个为 None → 同样记 0 并 warning"""
    caplog.set_level(logging.WARNING)
    r = calc_cost("minimax-m3", 100, 100, None)
    assert r["cost"] == 0.0
    assert r["priced"] is False
    assert "无定价配置" in caplog.text


def test_calc_cost_missing_currency_defaults_usd(caplog):
    """定价缺 currency → 视为 USD 并打 warning"""
    caplog.set_level(logging.WARNING)
    pricing = {"m": {"input_per_1m": 1.0, "output_per_1m": 2.0}}
    r = calc_cost("m", 1_000_000, 0, pricing)
    assert r["currency"] == "USD"
    assert r["cost"] == pytest.approx(1.0)
    assert "未标注 currency" in caplog.text


def test_split_by_currency_does_not_mix():
    """分币种独立累加，不做汇率折算，不相加"""
    records = [
        {"cost": 1.5, "currency": "USD"},
        {"cost": 2.5, "currency": "USD"},
        {"cost": 7.0, "currency": "CNY"},
    ]
    totals = split_by_currency(records)
    assert totals["cost_usd"] == pytest.approx(4.0)
    assert totals["cost_cny"] == pytest.approx(7.0)


@pytest.mark.skipif(
    not os.getenv("ARK_API_KEY"),
    reason="需要 ARK_API_KEY（.env）才能做真实 LLM 调用"
)
def test_real_llm_decision_reports_tokens_and_cost():
    """
    真实 LLM 调用：决策链应返回真实 token 数和非零成本

    这是本 Phase 成本统计的核心验证——callback 能否穿透 LLMChain.run() 取到 usage。
    """
    import config.env  # noqa: F401
    from update.decision_chain import UpdateDecisionChain

    chain = UpdateDecisionChain(pricing=PRICING)
    assert chain.chain is not None, "LLM 未初始化，检查 ARK_API_KEY"

    pkg = make_knowledge_package(issue_number=1611)
    result = chain.decide(pkg, days_since_last_update=1.0)

    assert result["decision"] in ("full", "incremental")

    cost = result["cost"]
    print(
        f"\n[真实调用] decision={result['decision']} "
        f"prompt_tokens={cost['prompt_tokens']} "
        f"completion_tokens={cost['completion_tokens']} "
        f"cost={cost['cost']:.8f} {cost['currency']}"
    )

    assert cost["prompt_tokens"] > 0, "取不到 prompt_tokens，callback 未生效"
    assert cost["completion_tokens"] > 0, "取不到 completion_tokens"
    assert cost["priced"] is True
    assert cost["cost"] > 0, "token 数为真但成本为 0，单价计算有问题"
