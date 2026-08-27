"""
Phase 6 增量路径测试

验证 _execute_incremental_update 的两级执行、成功判定与 detail 填充。
两级依赖（向量库 / LLM）都 mock 掉，只测编排逻辑。
"""

import logging
import pytest
from unittest.mock import MagicMock, patch

from .conftest import make_knowledge_package


def _patch_chains(upd_return, regen_return, regen_cost_records=None):
    """
    替换 orchestrator 里引用的两条链

    注意 patch 的是 orchestration.orchestrator 命名空间下的名字，
    因为 orchestrator 是 from ... import 进来的。
    """
    upd_chain = MagicMock()
    upd_chain.update_from_issue.return_value = upd_return

    regen_chain = MagicMock()
    regen_chain.regenerate_all_affected.return_value = regen_return
    regen_chain.cost_records = regen_cost_records or []

    return (
        patch(
            "orchestration.orchestrator.KnowledgeUpdateChain",
            return_value=upd_chain
        ),
        patch(
            "orchestration.orchestrator.SectionRegenerationChain",
            return_value=regen_chain
        ),
        upd_chain,
        regen_chain,
    )


def test_both_levels_succeed(orchestrator, knowledge_package):
    """向量库写入成功 + 章节重生成成功 → success=True，detail 计数都 > 0"""
    p_upd, p_regen, upd_chain, regen_chain = _patch_chains(
        {
            "status": "updated", "success": True,
            "documents_added": 3, "documents_deleted": 1, "chunks_created": 3,
            "error": None
        },
        {
            "sections_regenerated": 2, "sections_failed": 0,
            "sections_skipped": [], "updated_documents": ["overview.md"],
            "success": True, "error": None
        },
        regen_cost_records=[
            {"cost": 0.0012, "currency": "USD", "total_tokens": 500},
            {"cost": 0.0008, "currency": "USD", "total_tokens": 300},
        ]
    )

    project = orchestrator.config.projects["forum-reply-robot"]

    with p_upd, p_regen:
        result = orchestrator._execute_incremental_update(
            "forum-reply-robot", project, knowledge_package,
            decision_cost={"cost": 0.0005, "currency": "USD", "total_tokens": 200}
        )

    assert result.success is True
    assert result.mode == "incremental"
    assert result.detail["vector_status"] == "updated"
    assert result.detail["documents_added"] == 3
    assert result.detail["sections_regenerated"] == 2
    assert result.detail["updated_documents"] == ["overview.md"]
    # 决策成本 + 两次章节生成成本，分币种累加
    assert result.detail["cost_usd"] == pytest.approx(0.0005 + 0.0012 + 0.0008)
    assert result.detail["cost_cny"] == 0.0
    assert result.cost_usd == result.detail["cost_usd"]


def test_vector_no_changes_is_success(orchestrator, knowledge_package, caplog):
    """向量库 no_changes → success=True，但 detail 和日志必须明确标出"""
    caplog.set_level(logging.INFO)

    p_upd, p_regen, _, _ = _patch_chains(
        {
            "status": "no_changes", "success": True,
            "documents_added": 0, "documents_deleted": 0, "chunks_created": 0,
            "error": None
        },
        {
            "sections_regenerated": 1, "sections_failed": 0,
            "sections_skipped": [], "updated_documents": ["techstack.md"],
            "success": True, "error": None
        }
    )

    project = orchestrator.config.projects["forum-reply-robot"]

    with p_upd, p_regen:
        result = orchestrator._execute_incremental_update(
            "forum-reply-robot", project, knowledge_package
        )

    assert result.success is True
    assert result.detail["vector_status"] == "no_changes"
    assert "no_changes" in caplog.text


def test_vector_failed_stops_before_regeneration(
    orchestrator, knowledge_package
):
    """向量库 failed → success=False，且不继续调 regeneration"""
    p_upd, p_regen, upd_chain, regen_chain = _patch_chains(
        {
            "status": "failed", "success": False,
            "documents_added": 0, "documents_deleted": 0, "chunks_created": 0,
            "error": "embedding 服务 401"
        },
        {
            "sections_regenerated": 0, "sections_failed": 0,
            "sections_skipped": [], "updated_documents": [],
            "success": True, "error": None
        }
    )

    project = orchestrator.config.projects["forum-reply-robot"]

    with p_upd, p_regen:
        result = orchestrator._execute_incremental_update(
            "forum-reply-robot", project, knowledge_package
        )

    assert result.success is False
    assert "向量库更新失败" in result.error
    assert "embedding 服务 401" in result.error
    assert result.detail["vector_status"] == "failed"
    # 核心断言：第二级根本没被调用
    assert regen_chain.regenerate_all_affected.call_count == 0


def test_all_sections_failed_is_failure(orchestrator, knowledge_package):
    """章节全部失败 → success=False（假成功防线）"""
    p_upd, p_regen, _, _ = _patch_chains(
        {
            "status": "updated", "success": True,
            "documents_added": 2, "documents_deleted": 0, "chunks_created": 2,
            "error": None
        },
        {
            "sections_regenerated": 0, "sections_failed": 3,
            "sections_skipped": [], "updated_documents": [],
            "success": True, "error": None
        }
    )

    project = orchestrator.config.projects["forum-reply-robot"]

    with p_upd, p_regen:
        result = orchestrator._execute_incremental_update(
            "forum-reply-robot", project, knowledge_package
        )

    assert result.success is False
    assert "章节重生成全部失败" in result.error
    assert result.detail["sections_failed"] == 3
    assert result.detail["sections_regenerated"] == 0


def test_partial_failure_still_succeeds(orchestrator, knowledge_package):
    """部分成功部分失败 → 仍算成功，但 detail 里失败数可见"""
    p_upd, p_regen, _, _ = _patch_chains(
        {
            "status": "updated", "success": True,
            "documents_added": 2, "documents_deleted": 0, "chunks_created": 2,
            "error": None
        },
        {
            "sections_regenerated": 2, "sections_failed": 1,
            "sections_skipped": [], "updated_documents": ["overview.md"],
            "success": True, "error": None
        }
    )

    project = orchestrator.config.projects["forum-reply-robot"]

    with p_upd, p_regen:
        result = orchestrator._execute_incremental_update(
            "forum-reply-robot", project, knowledge_package
        )

    assert result.success is True
    assert result.detail["sections_failed"] == 1


def test_missing_knowledge_base_dir_warns(
    orchestrator, knowledge_package, caplog, monkeypatch
):
    """知识库目录不存在 → 日志提示只更新了向量库，sections_skipped 非空"""
    caplog.set_level(logging.INFO)

    # 指向一个确定不存在的目录
    storage = dict(orchestrator.config.global_config.storage)
    storage["base_dir"] = "/tmp/phase6-nonexistent-base"
    orchestrator.config.global_config.storage = storage

    p_upd, p_regen, _, _ = _patch_chains(
        {
            "status": "updated", "success": True,
            "documents_added": 2, "documents_deleted": 0, "chunks_created": 2,
            "error": None
        },
        {
            "sections_regenerated": 0, "sections_failed": 0,
            "sections_skipped": [
                {"document": "overview.md", "section": "核心流程",
                 "reason": "document_not_found"}
            ],
            "updated_documents": [], "success": True, "error": None
        }
    )

    project = orchestrator.config.projects["forum-reply-robot"]

    with p_upd, p_regen:
        result = orchestrator._execute_incremental_update(
            "forum-reply-robot", project, knowledge_package
        )

    assert result.success is True
    assert len(result.detail["sections_skipped"]) == 1
    assert "知识库目录不存在" in caplog.text
    assert "只更新了向量库" in caplog.text


def test_knowledge_base_dir_path_composition(orchestrator, knowledge_package):
    """知识库目录由 storage 配置拼出：base_dir/knowledge_dir/project_name"""
    p_upd, p_regen, _, regen_chain = _patch_chains(
        {
            "status": "updated", "success": True,
            "documents_added": 1, "documents_deleted": 0, "chunks_created": 1,
            "error": None
        },
        {
            "sections_regenerated": 1, "sections_failed": 0,
            "sections_skipped": [], "updated_documents": ["overview.md"],
            "success": True, "error": None
        }
    )

    project = orchestrator.config.projects["forum-reply-robot"]
    storage = orchestrator.config.global_config.storage
    expected = (
        f"{storage['base_dir']}/{storage['knowledge_dir']}/forum-reply-robot"
    )

    with p_upd, p_regen:
        orchestrator._execute_incremental_update(
            "forum-reply-robot", project, knowledge_package
        )

    args = regen_chain.regenerate_all_affected.call_args[0]
    assert args[1] == expected


def test_vector_exception_is_failure(orchestrator, knowledge_package):
    """向量库构造/调用抛异常 → success=False，不继续第二级"""
    p_regen = patch(
        "orchestration.orchestrator.SectionRegenerationChain",
        side_effect=AssertionError("第二级不应被调用")
    )

    project = orchestrator.config.projects["forum-reply-robot"]

    with patch(
        "orchestration.orchestrator.KnowledgeUpdateChain",
        side_effect=RuntimeError("SILICONFLOW_API_KEY 未设置")
    ), p_regen:
        result = orchestrator._execute_incremental_update(
            "forum-reply-robot", project, knowledge_package
        )

    assert result.success is False
    assert "向量库更新异常" in result.error
    assert result.detail["vector_status"] == "failed"
