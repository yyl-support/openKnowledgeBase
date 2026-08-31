"""
Phase 5 任务 1：SectionRegenerationChain 测试

覆盖 4 个方法：
- _extract_section（纯函数，测边界）
- identify_affected_sections（用 path 字段的 files）
- regenerate_section（真实 LLM，火山 ARK minimax-m3）
- regenerate_all_affected（断言写回真的发生）
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from update.regeneration_chain import SectionRegenerationChain
from extraction.models import (
    IssueKnowledgePackage,
    CodeChange,
    PRReference,
)

TEST_PROJECT = "test-phase5-regen"

ARK_KEY_MISSING = not os.getenv("ARK_API_KEY")
ARK_SKIP_REASON = (
    "SKIP 原因：环境变量 ARK_API_KEY 未设置，无法调用真实 LLM"
    "（火山 ARK minimax-m3）。设置后重跑本用例。"
)

# LLM 常见报错串，出现即说明拿到的不是真的生成结果
ERROR_MARKERS = [
    "Traceback", "Error code", "error code", "APIError",
    "AuthenticationError", "Invalid API key", "invalid_api_key",
    "RateLimitError", "Connection error", "章节生成失败",
]


@pytest.fixture(scope="module", autouse=True)
def cleanup_vectordb():
    """向量库目录只在本模块全部用例跑完后清理

    注意：chromadb 0.4.x 会按 settings 缓存 System 实例，
    如果在每个用例后删除 persist_directory，后续用例复用缓存的
    System 时会因 sqlite 文件消失而报 tenant 连接失败。
    """
    yield
    shutil.rmtree(os.path.join("vectordb", TEST_PROJECT), ignore_errors=True)


@pytest.fixture
def chain():
    """构造 SectionRegenerationChain 实例"""
    return SectionRegenerationChain(project_name=TEST_PROJECT)


@pytest.fixture
def kb_dir():
    """构造临时知识库目录，含 overview.md / techstack.md"""
    temp_dir = tempfile.mkdtemp()

    # 章节名与 identify_affected_sections 的映射表保持一致，
    # 且带编号前缀（"## 4. 核心能力"），对齐 UA 实际产出的格式
    Path(temp_dir, "overview.md").write_text(
        "# 项目概览\n\n"
        "## 1. 职责\n\n这是一个测试项目。\n\n"
        "## 4. 核心能力\n\n旧的核心能力描述：main.py 启动后直接退出。\n\n"
        "## 3. 边界\n\n本地运行。\n",
        encoding="utf-8",
    )
    Path(temp_dir, "techstack.md").write_text(
        "# 技术栈\n\n"
        "## 2. 构建与依赖\n\n旧的依赖说明：requirements.txt 里只有 requests。\n\n"
        "## 4. 调用链\n\n旧的调用链描述。\n",
        encoding="utf-8",
    )

    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


def _make_package(files):
    """构造 IssueKnowledgePackage；PRReference 需要 5 个必需参数"""
    pr = PRReference(
        repo="test/repo",
        number=42,
        title="测试 PR",
        state="MERGED",
        url="https://github.com/test/repo/pull/42",
    )
    return IssueKnowledgePackage(
        issue_number=1750,
        issue_title="重构主流程启动逻辑",
        issue_labels=["enhancement"],
        issue_body="调整 main.py 的启动流程，并更新依赖。",
        requirement=None,
        code_change=CodeChange(
            pr=pr,
            diff="test diff",
            files=files,
            total_additions=10,
            total_deletions=2,
        ),
    )


# ---------------- _extract_section（纯函数，边界） ----------------

def test_extract_section_normal(chain):
    """正常提取中间章节"""
    content = "# T\n\n## A\n\n内容 A\n\n## B\n\n内容 B\n"
    assert chain._extract_section(content, "A") == "内容 A"


def test_extract_section_not_found_returns_none(chain):
    """章节不存在时返回 None"""
    content = "# T\n\n## A\n\n内容 A\n"
    assert chain._extract_section(content, "不存在的章节") is None


def test_extract_section_last_section_reaches_end(chain):
    """末尾章节能取到文档结尾"""
    content = "# T\n\n## A\n\n内容 A\n\n## 末章\n\n第一行\n第二行\n最后一行\n"
    extracted = chain._extract_section(content, "末章")
    assert extracted is not None
    assert "第一行" in extracted
    assert "最后一行" in extracted


def test_extract_section_regex_special_chars(chain):
    """章节名含正则特殊字符（. * + ( ) [ ]）时不应报错且能命中"""
    name = "CI/CD (v2.0) [beta]+"
    content = f"# T\n\n## {name}\n\n特殊字符章节内容\n\n## 其他\n\n无关\n"
    assert chain._extract_section(content, name) == "特殊字符章节内容"


def test_extract_section_special_chars_no_false_match(chain):
    """正则特殊字符必须被转义：'a.c' 不应匹配到 'abc'"""
    content = "# T\n\n## abc\n\n不该被匹配\n"
    assert chain._extract_section(content, "a.c") is None


# ---------------- identify_affected_sections ----------------

def test_identify_affected_sections_with_path_field(chain):
    """files 用 path 字段（gh CLI 的真实字段名）时能被正确识别"""
    package = _make_package([
        {"path": "src/main.py", "additions": 5, "deletions": 1},
        {"path": "requirements.txt", "additions": 2, "deletions": 0},
    ])

    sections = chain.identify_affected_sections(package)
    pairs = {(s["document"], s["section"]) for s in sections}

    assert len(sections) > 0, "path 字段未被识别，说明字段名错配未修复"
    assert ("overview.md", "核心能力") in pairs
    assert ("techstack.md", "构建与依赖") in pairs
    # reason 里应带上真实文件名，而不是空串
    for s in sections:
        assert s["reason"].strip() not in ("变更", " 变更")


def test_identify_affected_sections_filename_still_works(chain):
    """兼容旧的 filename 字段"""
    package = _make_package([
        {"filename": "src/main.py", "additions": 5, "deletions": 1},
    ])
    pairs = {
        (s["document"], s["section"])
        for s in chain.identify_affected_sections(package)
    }
    assert ("overview.md", "核心能力") in pairs


def test_identify_affected_sections_no_code_change(chain):
    """无代码变更时返回空列表"""
    package = _make_package([])
    package.code_change = None
    assert chain.identify_affected_sections(package) == []


def test_identify_affected_sections_dedup(chain):
    """同一 (文档, 章节) 只出现一次"""
    package = _make_package([
        {"path": "src/main.py"},
        {"path": "app/app.py"},
    ])
    sections = chain.identify_affected_sections(package)
    pairs = [(s["document"], s["section"]) for s in sections]
    assert len(pairs) == len(set(pairs))


# ---------------- _replace_section / 写回 ----------------

def test_replace_section_writes_new_body(chain):
    """替换后：新内容在、旧内容不在、其他章节不受影响"""
    content = "# T\n\n## A\n\n旧的 A\n\n## B\n\n内容 B\n"
    updated = chain._replace_section(content, "A", "全新的 A 内容")

    assert updated is not None
    assert "全新的 A 内容" in updated
    assert "旧的 A" not in updated
    assert "## A" in updated
    assert "内容 B" in updated


def test_replace_section_not_found_returns_none(chain):
    """章节不存在时替换返回 None"""
    assert chain._replace_section("## A\n\n内容\n", "不存在", "x") is None


def test_replace_section_handles_backslash(chain):
    """新内容含反斜杠不应被当作正则转义序列处理"""
    content = "## A\n\n旧\n"
    updated = chain._replace_section(content, "A", r"路径 C:\temp\g<1> 和 \n")
    assert r"C:\temp\g<1>" in updated


# ---------------- regenerate_all_affected（断言写回真的发生） ----------------

def test_regenerate_all_affected_writes_back(chain, kb_dir, monkeypatch):
    """写回必须真的发生：读回文件确认内容变了（用受控生成内容，不烧 LLM 额度）"""
    new_body = "这是重新生成的章节内容，用于验证写回链路确实落盘。"

    monkeypatch.setattr(
        chain,
        "regenerate_section",
        lambda doc, sec, pkg, cur=None: f"{new_body}（{sec}）",
    )

    package = _make_package([
        {"path": "src/main.py"},
        {"path": "requirements.txt"},
    ])
    before = Path(kb_dir, "overview.md").read_text(encoding="utf-8")

    result = chain.regenerate_all_affected(package, kb_dir)

    after = Path(kb_dir, "overview.md").read_text(encoding="utf-8")
    tech_after = Path(kb_dir, "techstack.md").read_text(encoding="utf-8")

    assert result["success"] is True
    # main.py 触发 2 个 + requirements.txt 触发 1 个 = 3 个
    assert result["sections_regenerated"] == 3
    assert result["sections_failed"] == 0
    # 文件内容真的变了
    assert after != before
    assert new_body in after
    assert "旧的核心能力描述" not in after
    assert new_body in tech_after
    # 未受影响的章节保持原样
    assert "这是一个测试项目" in after
    assert set(result["updated_documents"]) == {"overview.md", "techstack.md"}


def test_regenerate_all_affected_no_silent_skip(chain, kb_dir, monkeypatch):
    """文档/章节缺失时必须明确记录到 sections_skipped，不静默跳过"""
    monkeypatch.setattr(
        chain, "regenerate_section", lambda *a, **k: "生成内容"
    )
    # 删掉 techstack.md，制造「文档不存在」
    Path(kb_dir, "techstack.md").unlink()
    # 制造「章节不存在」：overview.md 里没有 CI/CD 章节
    package = _make_package([
        {"path": "requirements.txt"},          # techstack.md 不存在
        {"path": ".github/workflows/ci.yml"},  # standards.md 不存在
    ])

    result = chain.regenerate_all_affected(package, kb_dir)
    reasons = {(s["document"], s["reason"]) for s in result["sections_skipped"]}

    assert len(result["sections_skipped"]) > 0
    assert ("techstack.md", "document_not_found") in reasons
    assert result["sections_regenerated"] == 0


def test_regenerate_all_affected_section_not_found_recorded(chain, kb_dir, monkeypatch):
    """文档存在但章节不存在：记录 section_not_found"""
    monkeypatch.setattr(chain, "regenerate_section", lambda *a, **k: "生成内容")
    # overview.md 存在但没有「核心能力」章节；techstack.md 也创建，但没有「调用链」
    Path(kb_dir, "overview.md").write_text(
        "# 项目概览\n\n## 项目简介\n\n只有简介。\n", encoding="utf-8"
    )
    Path(kb_dir, "techstack.md").write_text(
        "# 技术栈\n\n## 编程语言\n\nPython。\n", encoding="utf-8"
    )

    result = chain.regenerate_all_affected(_make_package([{"path": "src/main.py"}]), kb_dir)

    # main.py 触发 overview 核心能力 + techstack 调用链，两个章节都不存在
    assert {
        (s["document"], s["section"], s["reason"])
        for s in result["sections_skipped"]
    } == {
        ("overview.md", "核心能力", "section_not_found"),
        ("techstack.md", "调用链", "section_not_found")
    }
    assert result["sections_regenerated"] == 0


def test_regenerate_all_affected_generation_failure_counts(chain, kb_dir, monkeypatch):
    """生成失败（返回 None）计入 sections_failed，且文件不被改动"""
    monkeypatch.setattr(chain, "regenerate_section", lambda *a, **k: None)
    before = Path(kb_dir, "overview.md").read_text(encoding="utf-8")

    result = chain.regenerate_all_affected(_make_package([{"path": "src/main.py"}]), kb_dir)

    # main.py 触发 2 个章节，都生成失败
    assert result["sections_failed"] == 2
    assert result["sections_regenerated"] == 0
    assert Path(kb_dir, "overview.md").read_text(encoding="utf-8") == before


# ---------------- regenerate_section（真实 LLM） ----------------

@pytest.mark.skipif(ARK_KEY_MISSING, reason=ARK_SKIP_REASON)
def test_regenerate_section_real_llm(chain):
    """走真实 LLM（火山 ARK minimax-m3），断言拿到的是真的生成结果"""
    assert chain.llm is not None, "ARK_API_KEY 已设置但 LLM 未初始化"

    package = _make_package([
        {"path": "src/main.py", "additions": 20, "deletions": 3},
    ])

    content = chain.regenerate_section(
        document_name="overview.md",
        section_name="核心能力",
        knowledge_package=package,
        current_content="旧的核心能力描述：main.py 启动后直接退出。",
    )

    # 不能只断言 is not None —— 必须验证内容确实是生成结果
    assert content is not None, "LLM 返回 None，生成失败"
    assert content.strip(), "LLM 返回空内容"
    assert len(content) > 100, f"生成内容过短（{len(content)} 字符），疑似假成功"
    for marker in ERROR_MARKERS:
        assert marker not in content, f"生成内容含报错串: {marker}"
    # 生成结果不应只是把输入原样回吐
    assert content.strip() != "旧的核心能力描述：main.py 启动后直接退出。"


@pytest.mark.skipif(ARK_KEY_MISSING, reason=ARK_SKIP_REASON)
def test_regenerate_all_affected_real_llm_writes_back(chain, kb_dir):
    """真实 LLM + 真实写回：读回文件确认内容变了"""
    package = _make_package([{"path": "src/main.py", "additions": 20, "deletions": 3}])
    before = Path(kb_dir, "overview.md").read_text(encoding="utf-8")

    result = chain.regenerate_all_affected(package, kb_dir)
    after = Path(kb_dir, "overview.md").read_text(encoding="utf-8")

    assert result["success"] is True
    # main.py 变更现在触发 2 个章节：overview 核心能力 + techstack 调用链
    assert result["sections_regenerated"] == 2
    assert result["sections_skipped"] == []
    assert after != before, "写回未发生，文件内容未变化"
    assert len(after) > 50
    for marker in ERROR_MARKERS:
        assert marker not in after


def test_regenerate_section_without_llm_returns_none(chain):
    """LLM 不可用时明确返回 None，不假装成功"""
    chain.llm = None
    assert chain.regenerate_section(
        "overview.md", "核心能力", _make_package([{"path": "src/main.py"}])
    ) is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
