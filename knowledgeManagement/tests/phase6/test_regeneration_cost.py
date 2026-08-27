"""
Phase 6 章节重生成的成本统计测试

用 mock LLM 验证 cost_records 累加与 _fill_cost 汇总，不烧钱；
另有一个真实调用用例验证 callback 在 regenerate_section 里同样生效。
"""

import logging
import os
import pytest
from unittest.mock import MagicMock, patch

import config.env  # noqa: F401  收集期就加载 .env，否则 skipif 读不到密钥
from .conftest import make_knowledge_package

PRICING = {
    "minimax-m3": {
        "input_per_1m": 0.60,
        "output_per_1m": 2.40,
        "currency": "USD",
    },
}


def _make_chain(pricing=PRICING):
    """构造 SectionRegenerationChain，绕过真实 VectorStore"""
    from update.regeneration_chain import SectionRegenerationChain

    with patch("update.regeneration_chain.VectorStore") as mock_vs:
        mock_vs.return_value.similarity_search.return_value = []
        chain = SectionRegenerationChain("forum-reply-robot", pricing=pricing)
    return chain


def test_cost_records_reset_per_batch(tmp_path):
    """每次 regenerate_all_affected 独立统计，不跨调用累加"""
    chain = _make_chain()
    chain.cost_records = [{"cost": 99.0, "currency": "USD", "total_tokens": 1}]

    pkg = make_knowledge_package(files=[])  # 无变更文件 → 无受影响章节
    result = chain.regenerate_all_affected(pkg, str(tmp_path))

    assert result["cost_usd"] == 0.0
    assert result["cost_cny"] == 0.0
    assert result["total_tokens"] == 0


def test_missing_document_recorded_as_skipped(tmp_path):
    """知识库目录里没有文档 → 记进 sections_skipped，不算失败"""
    chain = _make_chain()
    pkg = make_knowledge_package()

    result = chain.regenerate_all_affected(pkg, str(tmp_path))

    assert result["success"] is True
    assert result["sections_regenerated"] == 0
    assert result["sections_failed"] == 0
    assert len(result["sections_skipped"]) > 0
    assert result["sections_skipped"][0]["reason"] == "document_not_found"


def test_cost_accumulated_across_sections(tmp_path, monkeypatch):
    """多章节重生成的成本按币种累加到结果里"""
    chain = _make_chain()

    doc = tmp_path / "overview.md"
    doc.write_text(
        "# 概览\n\n## 核心流程\n\n旧内容\n\n## 其他\n\n保持不变\n",
        encoding="utf-8"
    )

    call_count = {"n": 0}

    def fake_regenerate(document_name, section_name, knowledge_package,
                        current_content=None):
        """模拟一次带成本的生成"""
        from config.pricing import calc_cost
        call_count["n"] += 1
        chain.cost_records.append(
            calc_cost("minimax-m3", 1_000_000, 0, PRICING)
        )
        return "新内容"

    monkeypatch.setattr(chain, "regenerate_section", fake_regenerate)

    pkg = make_knowledge_package(files=[
        {"path": "main.py", "additions": 1, "deletions": 0, "patch": "x"},
    ])

    result = chain.regenerate_all_affected(pkg, str(tmp_path))

    assert call_count["n"] == 1
    assert result["sections_regenerated"] == 1
    assert result["cost_usd"] == pytest.approx(0.60)
    assert result["cost_cny"] == 0.0
    assert result["total_tokens"] == 1_000_000
    # 确认真的写回了文件
    assert "新内容" in doc.read_text(encoding="utf-8")


def test_unpriced_model_yields_zero_with_warning(tmp_path, monkeypatch, caplog):
    """单价缺失 → cost 记 0 且日志有 warning"""
    caplog.set_level(logging.WARNING)

    chain = _make_chain(pricing={})  # 空定价表

    doc = tmp_path / "overview.md"
    doc.write_text(
        "# 概览\n\n## 核心流程\n\n旧内容\n", encoding="utf-8"
    )

    def fake_regenerate(document_name, section_name, knowledge_package,
                        current_content=None):
        from config.pricing import calc_cost
        chain.cost_records.append(
            calc_cost("minimax-m3", 5000, 2000, chain.pricing)
        )
        return "新内容"

    monkeypatch.setattr(chain, "regenerate_section", fake_regenerate)

    pkg = make_knowledge_package(files=[
        {"path": "main.py", "additions": 1, "deletions": 0, "patch": "x"},
    ])

    result = chain.regenerate_all_affected(pkg, str(tmp_path))

    assert result["sections_regenerated"] == 1
    assert result["cost_usd"] == 0.0
    # token 数仍被记录，说明 0 不是因为没调用
    assert result["total_tokens"] == 7000
    assert "无定价配置，成本记 0" in caplog.text


@pytest.mark.skipif(
    not os.getenv("ARK_API_KEY"),
    reason="需要 ARK_API_KEY（.env）才能做真实 LLM 调用"
)
def test_real_llm_regenerate_section_reports_cost():
    """真实调用 regenerate_section：callback 应取到 token，成本非零"""
    import config.env  # noqa: F401

    chain = _make_chain()
    pkg = make_knowledge_package(issue_number=1611)

    content = chain.regenerate_section(
        "overview.md",
        "核心流程",
        pkg,
        current_content="本项目通过轮询论坛接口获取新帖，再调用模型生成回复。"
    )

    assert content, "章节生成返回空"
    assert len(chain.cost_records) == 1

    cost = chain.cost_records[0]
    print(
        f"\n[真实调用] regenerate_section "
        f"prompt_tokens={cost['prompt_tokens']} "
        f"completion_tokens={cost['completion_tokens']} "
        f"cost={cost['cost']:.8f} {cost['currency']}"
    )

    assert cost["prompt_tokens"] > 0
    assert cost["completion_tokens"] > 0
    assert cost["cost"] > 0
