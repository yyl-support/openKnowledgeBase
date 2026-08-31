"""
Phase 6 决策分派测试

验证 _extract_and_dispatch 按决策结果与配置开关正确分派，
以及决策链异常时直接失败（不降级走全量，避免烧掉约 $6）。
"""

import pytest
from unittest.mock import MagicMock

from orchestration.orchestrator import UpdateResult


def _stub_dispatch_targets(orch, monkeypatch):
    """把两条执行路径替换成打标记的 stub，只观察谁被调用"""
    full = MagicMock(return_value=UpdateResult(
        project_name="forum-reply-robot", success=True, mode="full",
        issue_number=9999, elapsed_seconds=0.1, cost_usd=6.0
    ))
    incr = MagicMock(return_value=UpdateResult(
        project_name="forum-reply-robot", success=True, mode="incremental",
        issue_number=9999, elapsed_seconds=0.1, cost_usd=0.001, detail={}
    ))
    monkeypatch.setattr(orch, "_execute_full_update", full)
    monkeypatch.setattr(orch, "_execute_incremental_update", incr)
    return full, incr


def _stub_decision_chain(orch, monkeypatch, decision=None, exc=None):
    """替换决策链，避免真实 LLM 调用"""
    chain = MagicMock()
    if exc is not None:
        chain.decide.side_effect = exc
    else:
        chain.decide.return_value = decision
    monkeypatch.setattr(orch, "_decision_chain", chain)
    return chain


def test_decision_full_goes_full(orchestrator, monkeypatch, knowledge_package):
    """决策 full → 走全量，不走增量"""
    orchestrator.issue_extractor.extract.return_value = knowledge_package
    full, incr = _stub_dispatch_targets(orchestrator, monkeypatch)
    _stub_decision_chain(orchestrator, monkeypatch, {
        "decision": "full", "reason": "变更大", "confidence": 0.9,
        "cost": {"cost": 0.001, "currency": "USD"}
    })

    project = orchestrator.config.projects["forum-reply-robot"]
    project.update_policy.incremental = True

    result = orchestrator._extract_and_dispatch(
        "forum-reply-robot", project, 9999
    )

    assert full.call_count == 1
    assert incr.call_count == 0
    assert result.mode == "full"


def test_decision_incremental_goes_incremental(
    orchestrator, monkeypatch, knowledge_package
):
    """决策 incremental → 走增量，不走全量"""
    orchestrator.issue_extractor.extract.return_value = knowledge_package
    full, incr = _stub_dispatch_targets(orchestrator, monkeypatch)
    _stub_decision_chain(orchestrator, monkeypatch, {
        "decision": "incremental", "reason": "影响小", "confidence": 0.8,
        "cost": {"cost": 0.001, "currency": "USD"}
    })

    project = orchestrator.config.projects["forum-reply-robot"]
    project.update_policy.incremental = True

    result = orchestrator._extract_and_dispatch(
        "forum-reply-robot", project, 9999
    )

    assert incr.call_count == 1
    assert full.call_count == 0
    assert result.mode == "incremental"


def test_config_forces_full(orchestrator, monkeypatch, knowledge_package, caplog):
    """update_policy.incremental=False 强制全量，优先于 LLM 决策"""
    import logging
    caplog.set_level(logging.INFO)

    orchestrator.issue_extractor.extract.return_value = knowledge_package
    full, incr = _stub_dispatch_targets(orchestrator, monkeypatch)
    chain = _stub_decision_chain(orchestrator, monkeypatch, {
        "decision": "incremental", "reason": "影响小", "confidence": 0.8
    })

    project = orchestrator.config.projects["forum-reply-robot"]
    project.update_policy.incremental = False
    try:
        orchestrator._extract_and_dispatch("forum-reply-robot", project, 9999)
    finally:
        project.update_policy.incremental = True

    assert full.call_count == 1
    assert incr.call_count == 0
    # 配置兜底优先，决策链根本没被调用
    assert chain.decide.call_count == 0
    assert "配置强制全量" in caplog.text


def test_decision_exception_fails_without_full(
    orchestrator, monkeypatch, knowledge_package
):
    """决策链抛异常 → 直接失败，绝不降级走全量（全量约 $6）"""
    orchestrator.issue_extractor.extract.return_value = knowledge_package
    full, incr = _stub_dispatch_targets(orchestrator, monkeypatch)
    _stub_decision_chain(
        orchestrator, monkeypatch, exc=RuntimeError("ARK 服务不可用")
    )

    project = orchestrator.config.projects["forum-reply-robot"]
    project.update_policy.incremental = True

    result = orchestrator._extract_and_dispatch(
        "forum-reply-robot", project, 9999
    )

    assert result.success is False
    assert "决策链异常" in result.error
    assert result.cost_usd == 0.0
    # 核心断言：没有走全量
    assert full.call_count == 0
    assert incr.call_count == 0


def test_days_since_last_update_none_is_zero(orchestrator):
    """last_update_time 为 None 时天数取 0.0"""
    project = orchestrator.config.projects["ascend-ci-deployment"]
    project.metadata.last_update_time = None
    assert orchestrator._days_since_last_update(project) == 0.0
