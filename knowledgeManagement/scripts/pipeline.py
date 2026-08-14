#!/usr/bin/env python3
"""
四层知识提取流水线

  Layer 1 预处理  repo_scanner（确定性清点）+ preprocess subagent（规则/功能分类、轻重缓急）
  Layer 2 解读    三方件 adapter（Python 调用）+ extract subagent（覆盖率核对）
  Layer 3 校验    verify subagent（以 rule_facts 为依据实际检索仓库，产出 check.md）
  Layer 4 提炼    refine subagent（按章节契约写最终报告）

四层 subagent 统一 claude-sonnet-5，职责约束见 agents/<layer>/CLAUDE.md，
全局强约束见 constraints.py，两者在每次调用时都注入。

退出码：
  0 全部完成
  1 执行错误
  3 预处理层需要用户决策（文件数超阈值或取舍无法裁定）—— 已写出决策请求，等待决策
  4 解读层阻塞（core 覆盖率缺口或产物污染）
  5 校验层阻塞（存在未修正的事实冲突）
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Optional

import agent_runner as ar
from repo_scanner import scan_repo, build_manifest_text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("pipeline")

EXIT_NEEDS_DECISION = 3
EXIT_EXTRACT_BLOCKED = 4
EXIT_VERIFY_BLOCKED = 5

# 预处理层的文件数阈值：超过即要求做轻重缓急划分，且取舍需用户确认
LARGE_PROJECT_THRESHOLD = 80


def _write_json(path: str, data: Dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("已写出 %s", path)


def _read_json(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _as_text(value) -> str:
    """
    把可能是 dict/list 的字段规范成文本。

    契约写的是字符串，但模型会返回结构化对象（实测 decision_request 返回了 dict，
    直接 .strip() 抛 AttributeError）。内容本身有效，没必要因为形态不同就判失败，
    所以统一转成可读文本而不是报错。
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, indent=2)


def _normalize_preprocess(data: Dict) -> None:
    """把 Layer 1 产物里的文本类字段规范成字符串，避免下游做 str 操作时崩。"""
    for key in ("core_flow", "decision_request"):
        if key in data:
            data[key] = _as_text(data[key])

    ii = data.get("interpret_inputs") or {}
    for tier in ("core", "auxiliary", "excluded"):
        for item in ii.get(tier) or []:
            if isinstance(item, dict) and "reason" in item:
                item["reason"] = _as_text(item["reason"])

    for r in data.get("rule_facts") or []:
        if isinstance(r, dict):
            r["assertions"] = [_as_text(a) for a in (r.get("assertions") or [])]


def _validate_preprocess_shape(repo_path: str, scan: Dict, data: Dict) -> None:
    """
    复核 Layer 1 产物的形状，不合契约直接失败。

    只靠约束文本指望模型自觉是不够的，实测事故都发生在没有 Python 复核的地方：
    subagent 曾在 core/auxiliary 里填目录（projects、manifests），导致下游按文件
    读取全部失败、且 80 阈值被绕过（6 个目录实际覆盖 2194 个文件）；同时 16 条
    rule_facts 里 14 条 assertions 为空，校验层拿到的是假的事实依据。

    检查项：
    1. core / auxiliary 的每个 path 必须是实际存在的**文件**（不能是目录）
    2. 每个条目必须有非空 reason —— 判定依据缺失等于无法复核这个分类
    3. rule_facts 的 path 必须存在，且 assertions 不得为空
    4. 同一路径不得跨 tier 重复出现（会让阈值重复计数）
    5. core 不得为空 —— 任何项目都有主流程
    6. needs_user_decision 为真时必须给出 decision_request

    Raises:
        ar.AgentError: 任一检查不通过
    """
    problems = []
    ii = data.get("interpret_inputs") or {}
    seen: Dict[str, str] = {}

    for tier in ("core", "auxiliary", "excluded"):
        for item in ii.get(tier) or []:
            item = item or {}
            rel = item.get("path") or ""
            if not rel:
                problems.append(f"{tier}: 存在空 path 条目")
                continue

            if not _as_text(item.get("reason")).strip():
                problems.append(f"{tier}: `{rel}` 缺少 reason，无法复核该分类是否成立")

            if rel in seen:
                problems.append(
                    f"`{rel}` 同时出现在 {seen[rel]} 和 {tier}，重复计数会让阈值失真"
                )
            else:
                seen[rel] = tier

            abspath = os.path.join(repo_path, rel)
            # excluded 允许填目录（它只表达「不解读」，不需要被读取）
            if tier == "excluded":
                if not os.path.exists(abspath):
                    problems.append(f"excluded: `{rel}` 不存在于仓库中")
                continue

            if os.path.isdir(abspath):
                n = sum(len(fs) for _, _, fs in os.walk(abspath))
                problems.append(
                    f"{tier}: `{rel}` 是目录（含约 {n} 个文件），契约要求单个文件路径。"
                    f"请逐个列出该目录下需解读的文件"
                )
            elif not os.path.isfile(abspath):
                problems.append(f"{tier}: `{rel}` 不存在于仓库中")

    if not (ii.get("core") or []):
        problems.append("core 为空 —— 任何项目都有主流程，空 core 说明分类未完成")

    for r in data.get("rule_facts") or []:
        r = r or {}
        rel = r.get("path") or ""
        if not rel:
            problems.append("rule_facts: 存在空 path 条目")
            continue
        if not os.path.isfile(os.path.join(repo_path, rel)):
            problems.append(
                f"rule_facts: `{rel}` 不是仓库中的实际文件，其 assertions 来源可疑"
            )
        if not (r.get("assertions") or []):
            problems.append(
                f"rule_facts: `{rel}` 的 assertions 为空 —— 校验层会以为该文件已被采信，"
                f"实际无从比对。摘不出断言就不要列入 rule_facts"
            )

    if data.get("needs_user_decision") and not _as_text(data.get("decision_request")).strip():
        problems.append("needs_user_decision 为真但 decision_request 为空，用户无从决策")

    if problems:
        raise ar.AgentError(
            "[preprocess] 产物不合契约，已停止 —— 不静默放过，否则错误会传导到下游：\n  - "
            + "\n  - ".join(problems)
        )


def _account_coverage(repo_path: str, scan: Dict, data: Dict) -> Dict:
    """
    核算文件归属：仓库里每个文件都该被分类到 core / auxiliary / excluded / rule_facts
    之一，否则就是被静默漏掉了。

    这一项是「禁止擅自遗弃」的实际执行手段。只检查形状拦不住漏文件 —— subagent
    完全可以只列 5 个 core 文件、对其余 2000 个一字不提，形状校验全部通过。

    excluded 允许是目录，因此按前缀展开计算覆盖。

    Returns:
        {"classified", "unaccounted", "unaccounted_sample", "total"}
    """
    all_files = {f["path"] for f in scan.get("files") or []}
    ii = data.get("interpret_inputs") or {}

    classified = set()
    for tier in ("core", "auxiliary"):
        for item in ii.get(tier) or []:
            p = (item or {}).get("path")
            if p:
                classified.add(p)
    for r in data.get("rule_facts") or []:
        p = (r or {}).get("path")
        if p:
            classified.add(p)

    # excluded 可能是目录，按前缀吸收
    excluded_prefixes = []
    for item in ii.get("excluded") or []:
        p = (item or {}).get("path")
        if not p:
            continue
        if os.path.isdir(os.path.join(repo_path, p)):
            excluded_prefixes.append(p.rstrip("/") + "/")
        else:
            classified.add(p)

    for f in all_files:
        if any(f.startswith(pref) for pref in excluded_prefixes):
            classified.add(f)

    unaccounted = sorted(all_files - classified)
    return {
        "total": len(all_files),
        "classified": len(classified & all_files),
        "unaccounted": len(unaccounted),
        "unaccounted_sample": unaccounted[:30],
    }


# ---------------------------------------------------------------- Layer 1

def layer1_preprocess(repo_path: str, work_dir: str, *, model: str,
                      threshold: int = LARGE_PROJECT_THRESHOLD) -> Dict:
    """
    预处理层：扫描 → 分类 → 轻重缓急划分。

    Returns:
        preprocess.json 内容
    """
    logger.info("=== Layer 1 预处理：扫描仓库 ===")
    scan = scan_repo(repo_path)
    _write_json(os.path.join(work_dir, "scan.json"), scan)

    manifest = build_manifest_text(scan)
    manifest_path = os.path.join(work_dir, "scan-manifest.md")
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(manifest)

    if not scan["claude_md"]:
        logger.warning(
            "仓库内没有 CLAUDE.md —— 校验层将缺少规则事实依据，"
            "只能依赖依赖清单与 CI 定义"
        )

    logger.info("=== Layer 1 预处理：subagent 分类 ===")
    prompt = f"""对以下代码仓做预处理分类。

仓库路径：{scan['repo_path']}
文件总数：{scan['total_files']}
大项目阈值：{threshold}（core + auxiliary 文件数超过此值时必须要求用户决策）

扫描清单已写入：{manifest_path}
请先 Read 这份清单，再按你的 CLAUDE.md 契约输出 JSON。

清单内容摘要（完整内容请读文件）：
- 目录数 {len(scan['dir_stats'])}，规则候选文件 {len(scan['rule_candidates'])} 个
- CLAUDE.md {len(scan['claude_md'])} 份

只输出 JSON，不要任何其他文字。"""

    out = ar.run_agent("preprocess", prompt, cwd=repo_path, model=model,
                       extra_dirs=[work_dir])

    # 先把原始输出落盘，再做解析和校验。subagent 在大仓上要跑十几分钟，
    # 校验失败就丢掉全部产物是不可接受的 —— 实测踩过：校验代码自身的类型 bug
    # 让 14 分钟的产物直接蒸发，连排查依据都没留下。
    raw_out_path = os.path.join(work_dir, "preprocess-raw.txt")
    with open(raw_out_path, "w", encoding="utf-8") as f:
        f.write(out)
    logger.info("Layer 1 原始输出已留存: %s", raw_out_path)

    data = ar.parse_json_output("preprocess", out)
    _write_json(os.path.join(work_dir, "preprocess-unvalidated.json"), data)

    ar.require_keys("preprocess", data, [
        "project_name", "total_files", "rule_facts", "interpret_inputs",
        "core_flow", "needs_user_decision",
    ])

    _normalize_preprocess(data)
    _validate_preprocess_shape(repo_path, scan, data)

    # 核算文件归属：漏掉的文件必须暴露出来，不能静默消失
    coverage = _account_coverage(repo_path, scan, data)
    data["file_accounting"] = coverage
    logger.info("Layer 1 归属核算：%d/%d 已分类，%d 未归属",
                coverage["classified"], coverage["total"], coverage["unaccounted"])

    if coverage["unaccounted"] > 0:
        data["needs_user_decision"] = True
        sample = "\n  ".join(coverage["unaccounted_sample"])
        more = (f"\n  ...（另有 {coverage['unaccounted'] - 30} 个未列出）"
                if coverage["unaccounted"] > 30 else "")
        existing = _as_text(data.get("decision_request")).strip()
        data["decision_request"] = (
            existing + f"\n\n【文件归属缺口】仓库共 {coverage['total']} 个文件，"
            f"其中 {coverage['unaccounted']} 个既未纳入 core/auxiliary，也未列入 "
            f"excluded 或 rule_facts —— 等于被静默漏掉。样本：\n  {sample}{more}\n"
            f"请决定这些文件是纳入解读、还是明确排除。"
        ).strip()

    ii = data["interpret_inputs"]
    n_core = len(ii.get("core", []))
    n_aux = len(ii.get("auxiliary", []))
    if n_core + n_aux > threshold and not data.get("needs_user_decision"):
        logger.warning(
            "core+auxiliary=%d 超过阈值 %d 但 subagent 未标记需决策，由 Python 强制标记",
            n_core + n_aux, threshold,
        )
        data["needs_user_decision"] = True
        data["decision_request"] = data.get("decision_request") or (
            f"core({n_core}) + auxiliary({n_aux}) = {n_core + n_aux} 个文件，"
            f"超过阈值 {threshold}。subagent 未主动提出决策请求，"
            f"请人工确认解读范围与详略划分。"
        )

    if scan["oversized_rule_files"]:
        data["needs_user_decision"] = True
        existing = _as_text(data.get("decision_request"))
        paths = ", ".join(o["path"] for o in scan["oversized_rule_files"])
        data["decision_request"] = (existing + f"\n另：约定文件超限未读取（{paths}），"
                                              f"需决定是否分批读取。").strip()

    logger.info("Layer 1 完成：rule_facts=%d core=%d auxiliary=%d excluded=%d",
                len(data["rule_facts"]), n_core, n_aux,
                len(ii.get("excluded", [])))
    return data


def write_decision_request(work_dir: str, pre: Dict) -> str:
    """把决策请求写成 Markdown，供用户直接阅读后回复。"""
    ii = pre["interpret_inputs"]
    lines = [
        f"# 需用户决策：{pre['project_name']}",
        "",
        f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"文件总数：{pre['total_files']}",
        "",
        "## 触发原因", "", str(pre.get("decision_request") or "（未说明）"), "",
        "## 当前划分", "",
        f"- core（主流程，全面细致）：{len(ii.get('core', []))} 个",
        f"- auxiliary（辅助能力，熟悉作用即可）：{len(ii.get('auxiliary', []))} 个",
        f"- excluded（不解读）：{len(ii.get('excluded', []))} 个",
        "",
        f"判定的主流程：{pre.get('core_flow', '（未给出）')}",
        "",
    ]
    acct = pre.get("file_accounting") or {}
    if acct:
        lines += [
            "## 文件归属核算", "",
            f"- 仓库文件总数：{acct.get('total')}",
            f"- 已分类：{acct.get('classified')}",
            f"- **未归属：{acct.get('unaccounted')}**（未纳入解读也未明确排除）",
            "",
        ]
    lines += [
        "## core 清单", "",
    ]
    lines += [f"- `{x['path']}` — {x.get('reason', '')}" for x in ii.get("core", [])] or ["（空）"]
    lines += ["", "## auxiliary 清单", ""]
    lines += [f"- `{x['path']}` — {x.get('reason', '')}" for x in ii.get("auxiliary", [])] or ["（空）"]
    lines += ["", "## excluded 清单", ""]
    lines += [f"- `{x['path']}` — {x.get('reason', '')}" for x in ii.get("excluded", [])] or ["（空）"]
    lines += ["", "---", "",
              "确认后用 `--decision-approved` 重跑，或先编辑 preprocess.json 调整划分。"]

    path = os.path.join(work_dir, "decision-request.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    logger.info("决策请求已写出：%s", path)
    return path


# ---------------------------------------------------------------- Layer 2

def layer2_extract(repo_path: str, work_dir: str, pre: Dict, *, adapter_name: str,
                   config: Dict, model: str) -> tuple:
    """
    解读层：调用三方件 + subagent 核对覆盖率。

    Returns:
        (raw_path, coverage_json)
    """
    from extract import create_adapter
    from source_selector import select_sources

    logger.info("=== Layer 2 解读：调用 %s ===", adapter_name)
    adapter = create_adapter(adapter_name, config)

    ii = pre["interpret_inputs"]
    wanted = [x["path"] for x in ii.get("core", []) + ii.get("auxiliary", [])]

    if adapter_name == "mk":
        # 按预处理层的判定精确投喂，不再走目录抽样 —— 抽样是覆盖率缺口的来源
        sources = select_sources(repo_path, include_paths=wanted)
        logger.info("投喂 %d 个源文件（预处理层判定 %d 个）", len(sources), len(wanted))
        pages_data = adapter.extract(repo_path, work_dir, source_files=sources)
    else:
        pages_data = adapter.extract(repo_path, work_dir)

    raw_path = os.path.join(work_dir, "raw.json")
    _write_json(raw_path, pages_data)

    logger.info("=== Layer 2 解读：subagent 核对覆盖率 ===")
    pre_path = os.path.join(work_dir, "preprocess.json")
    prompt = f"""核对三方件产物的覆盖率。

三方件：{adapter_name}
预处理层产物：{pre_path}（读取其中的 interpret_inputs）
三方件原始产物：{raw_path}
产物页面数：{len(pages_data.get('pages', []))}
预处理层判定应解读的文件数：{len(wanted)}（core {len(ii.get('core', []))} +
auxiliary {len(ii.get('auxiliary', []))}）

Read 这两份 JSON，按你的 CLAUDE.md 契约输出 JSON。只输出 JSON。"""

    out = ar.run_agent("extract", prompt, cwd=work_dir, model=model,
                       extra_dirs=[repo_path])
    cov = ar.parse_json_output("extract", out)
    ar.require_keys("extract", cov, [
        "tool", "actual_page_count", "missing", "unexpected", "blocking",
    ])

    # Python 侧复核阻塞判定：
    # 1. core 有缺口 → 必须阻塞（主流程不允许缺失）
    # 2. 有外部路径（foreign_count>0）→ 必须阻塞（污染）
    # 3. 仅范围超集（unexpected 多但都属于本仓）→ 不阻塞。UA 总是分析整仓，
    #    这是固有行为，实测占比 97.2%，据此阻塞会让每次 UA 运行都停下
    missing_core = [m for m in cov["missing"] if (m or {}).get("tier") == "core"]
    foreign = int(cov.get("foreign_count") or 0)

    if missing_core:
        cov["blocking"] = True
        cov["blocking_reason"] = (
            f"core 层缺失 {len(missing_core)} 个文件，主流程有缺口："
            + ", ".join((m or {}).get("path", "?") for m in missing_core[:8])
        )
    elif foreign > 0:
        cov["blocking"] = True
        cov["blocking_reason"] = (
            f"产物疑似被污染：{foreign} 个 unexpected 路径不属于本仓库。"
            + (cov.get("blocking_reason") or "")
        )
    elif cov["blocking"]:
        # subagent 判了阻塞，但既无 core 缺口也无外部路径 —— 降级为范围提示
        logger.warning(
            "Layer 2 范围超集（unexpected=%d，均属本仓），降级为提示不阻塞。"
            "原阻塞理由：%s",
            len(cov["unexpected"]), (cov.get("blocking_reason") or "")[:200],
        )
        cov["scope_note"] = (cov.get("scope_note")
                             or cov.get("blocking_reason") or "范围超集")
        cov["blocking"] = False
        cov["blocking_reason"] = None

    logger.info(
        "Layer 2 完成：页面=%s core覆盖=%s aux覆盖=%s missing=%d unexpected=%d "
        "foreign=%d blocking=%s",
        cov["actual_page_count"], cov.get("coverage_core"),
        cov.get("coverage_auxiliary"), len(cov["missing"]),
        len(cov["unexpected"]), foreign, cov["blocking"],
    )
    return raw_path, cov


# ---------------------------------------------------------------- Layer 3

def layer3_verify(repo_path: str, work_dir: str, output_dir: str, *,
                  model: str) -> Dict:
    """
    校验层：两类核验。

    1. 规则冲突：三方件断言 vs rule_facts，实际检索裁定
    2. 结构性：core 层每个文件的摘要断言 vs 源文件实际结构

    第 2 类是后加的。实测漏过两处错误：UA 把 pod 标签说成 nodeSelector、把
    「每 runner 需 2 张 NPU」说成「2 副本」，两者字面量全对、不与 CLAUDE.md 冲突，
    因此只做第 1 类核验时全部漏过，最终原样进了交付报告。
    """
    logger.info("=== Layer 3 校验 ===")
    pre_path = os.path.join(work_dir, "preprocess.json")
    raw_path = os.path.join(work_dir, "raw.json")
    check_path = os.path.join(output_dir, "check.md")
    os.makedirs(output_dir, exist_ok=True)

    pre = _read_json(pre_path)
    core = (pre.get("interpret_inputs") or {}).get("core") or []
    core_paths = [(x or {}).get("path", "?") for x in core]
    core_list = "\n".join(f"- {p}" for p in core_paths)
    core_count = len(core_paths)

    prompt = f"""校验三方件解读的事实正确性。

被校验仓库：{repo_path}
规则事实依据：{pre_path} 中的 rule_facts
三方件产物：{raw_path}
校验记录写入：{check_path}

请 Read 这两份 JSON，做两类校验：

**第一类 规则冲突**：对产物中的每条事实性断言，与 rule_facts 比对。遇到冲突的
不要武断判错 —— 定位双方事实来源后用 Grep/Bash grep 实际检索本仓库，以你实际
检查的结果为准，并把实际计数写进 evidence。

**第二类 结构性核验**：core 层共 {core_count} 个文件，清单如下：
{core_list}

逐个打开这些源文件，与 raw.json 里对应页面的摘要对照，检查每条结构性断言的
位置、量纲、主体、存在性是否成立（详见你的 CLAUDE.md 第 2b 条）。字面量拼对了
但位置或含义说错了，同样是 fact_conflict。用 grep -n 给出行号作为 evidence。
把核验数量填进 structural_check 字段。

**第三类 作用域核验**：上面这 {core_count} 个文件是从 2000+ 个同构文件里抽出的
代表样本。对样本里的每个关键字段（schedulerName、storageClassName、image、
version、replicas、nodeSelector、队列注解、资源限制等），用
`grep -rhoE '<字段>:\\s*[^\\s]+' --include='*.yaml' .` 统计它在**全仓**的取值分布，
再判断样本取值是不是多数派。

不是多数派就必须报 conflict（check_type=scope），corrected_fact 里给出完整分布。
把统计结果填进 scope_check 字段。详见你的 CLAUDE.md 第 2c 条。

**第四类 枚举完整性**：核实「类型清单」类断言是否穷举。用 find/grep 数出实际种类数，
与产物所列比对，少了就报 conflict（check_type=enumeration）。详见第 2d 条。

执行顺序：
1. 用 Write 写出 {check_path}
2. 然后你的**最终回复必须是一个 JSON 对象，且只有这个 JSON 对象**

最终回复的格式要求（硬性）：
- 第一个字符必须是 `{{`，最后一个字符必须是 `}}`
- 不要写任何前言、总结、markdown 标题、要点列表或 ✅ 之类的符号
- 不要把 check.md 的内容重复到 JSON 里
- 即使结论是「无冲突」，也必须用 JSON 表达：
  `{{"checked_count": N, "conflicts": [], "corrections_for_refiner": [], "blocking": false, "blocking_reason": null}}`

必需字段：checked_count、conflicts、corrections_for_refiner、blocking、blocking_reason。"""

    out = ar.run_agent("verify", prompt, cwd=repo_path, model=model,
                       extra_dirs=[work_dir, output_dir])

    # 先留存原始输出再解析。校验层要实际检索仓库，跑几分钟，
    # 解析失败就丢掉全部结论是不可接受的
    raw_out_path = os.path.join(work_dir, "verify-raw.txt")
    with open(raw_out_path, "w", encoding="utf-8") as f:
        f.write(out)
    logger.info("Layer 3 原始输出已留存: %s", raw_out_path)

    data = ar.parse_json_output("verify", out)
    ar.require_keys("verify", data, [
        "checked_count", "conflicts", "corrections_for_refiner", "blocking",
    ])

    # 复核结构性核验的覆盖面：声称核了多少个 core 文件，必须等于实际 core 数量。
    # 不复核的话，subagent 只挑几个容易的核一下就能过关，而漏过的正是最隐蔽的那类错误。
    sc = data.get("structural_check") or {}
    checked = int(sc.get("core_files_checked") or 0)
    if checked < core_count:
        logger.warning(
            "Layer 3 结构性核验覆盖不全：声称核了 %d/%d 个 core 文件，缺 %d 个",
            checked, core_count, core_count - checked,
        )
        data.setdefault("coverage_warning",
                        f"结构性核验只覆盖 {checked}/{core_count} 个 core 文件")
    else:
        logger.info("Layer 3 结构性核验覆盖 %d/%d 个 core 文件，检查断言 %s 条",
                    checked, core_count, sc.get("claims_examined"))

    # 复核作用域核验是否真的做了统计。这条防线针对的错误是：core 样本的属性被当成
    # 全局事实。实测事故：样本写 schedulerName: npu-scheduler（全仓 180 次），
    # 而全仓多数派是 volcano（255 次），错误结论进了交付报告，由领域专家指出才发现。
    # 只在契约里写 C5「不得放大作用域」而不要求实际统计，约束落不了地。
    scope = data.get("scope_check") or {}
    fields = int(scope.get("key_fields_examined") or 0)
    if fields == 0:
        logger.warning(
            "Layer 3 未做作用域核验（key_fields_examined=0）—— 代表样本的属性"
            "可能被当成全局事实，这类错误最难发现"
        )
        data.setdefault("coverage_warning", "")
        data["coverage_warning"] = (
            _as_text(data.get("coverage_warning")) + " 未做作用域核验"
        ).strip()
    else:
        minority = int(scope.get("fields_where_sample_is_minority") or 0)
        logger.info(
            "Layer 3 作用域核验：检查 %d 个关键字段，其中 %d 个样本取值为少数派",
            fields, minority,
        )

    unresolved = [c for c in data["conflicts"]
                  if c.get("severity") == "fact_conflict"
                  and c.get("verdict") in ("unresolved", None)]
    if unresolved and not data["blocking"]:
        logger.warning("存在 %d 条未裁定的事实冲突但 subagent 未阻塞，由 Python 强制阻塞",
                       len(unresolved))
        data["blocking"] = True
        data["blocking_reason"] = (
            f"{len(unresolved)} 条事实冲突未裁定："
            + ", ".join(c.get("id", "?") for c in unresolved)
        )

    n_fact = sum(1 for c in data["conflicts"] if c.get("severity") == "fact_conflict")
    by_type = {}
    for c in data["conflicts"]:
        t = c.get("check_type") or "unknown"
        by_type[t] = by_type.get(t, 0) + 1
    logger.info(
        "Layer 3 完成：校验 %s 条，冲突 %d（事实冲突 %d），分类 %s，blocking=%s",
        data["checked_count"], len(data["conflicts"]), n_fact, by_type,
        data["blocking"],
    )
    return data


# ---------------------------------------------------------------- Layer 4

def layer4_refine(repo_path: str, work_dir: str, output_path: str, *,
                  output_type: str, model: str) -> str:
    """提炼层：按章节契约写最终报告。"""
    from refine.refiner import Refiner

    logger.info("=== Layer 4 提炼：%s ===", output_type)
    pre_path = os.path.join(work_dir, "preprocess.json")
    raw_path = os.path.join(work_dir, "raw.json")
    verify_path = os.path.join(work_dir, "verify.json")
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    contract = Refiner.SECTION_CONTRACTS[output_type]
    prompt = f"""生成最终交付报告。

输出类型：{output_type}
输出文件：{output_path}
被解读仓库：{repo_path}

输入（请逐份 Read）：
- 三方件解读产物：{raw_path}
- 校验层修正（**优先级高于上一份**）：{verify_path} 的 corrections_for_refiner
- 规则事实与详略划分：{pre_path} 的 rule_facts 与 interpret_inputs

## 章节契约
{contract}

用 Write 写出 {output_path}，然后只回复一行 `OK: <文件路径>`。"""

    out = ar.run_agent("refine", prompt, cwd=repo_path, model=model,
                       extra_dirs=[work_dir, os.path.dirname(output_path)])

    if not os.path.isfile(output_path):
        raise ar.AgentError(
            f"[refine] subagent 未写出 {output_path}，其输出：{out[:500]}"
        )
    logger.info("Layer 4 完成：%s（%d 字节）", output_path,
                os.path.getsize(output_path))
    return output_path


# ---------------------------------------------------------------- main

def main():
    parser = argparse.ArgumentParser(
        description="四层知识提取流水线：预处理 → 解读 → 校验 → 提炼",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 首次运行，跑到预处理层若需决策会停下（退出码 3）
  python pipeline.py --repo /path/to/repo --adapter mk --output-type architecture

  # 阅读 work/<项目名>/decision-request.md 后确认，带 --decision-approved 继续
  python pipeline.py --repo /path/to/repo --adapter mk --output-type architecture \\
      --decision-approved

  # 只跑预处理层，看划分结果
  python pipeline.py --repo /path/to/repo --adapter mk --output-type architecture \\
      --stop-after preprocess
        """,
    )
    parser.add_argument("--repo", required=True, help="代码仓本地路径")
    parser.add_argument("--adapter", required=True, choices=["mk", "zread", "ua"])
    parser.add_argument("--output-type", required=True,
                        choices=["architecture", "quickstart", "api-reference",
                                 "onboarding", "overview", "techstack", "standards"])
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--work-root", default="./work")
    parser.add_argument("--output-root",
                        help="覆盖 config.yaml 的 output.root")
    parser.add_argument("--model", default=ar.DEFAULT_MODEL,
                        help=f"四层 subagent 统一使用的模型（默认 {ar.DEFAULT_MODEL}）")
    parser.add_argument("--threshold", type=int, default=LARGE_PROJECT_THRESHOLD,
                        help=f"大项目文件数阈值（默认 {LARGE_PROJECT_THRESHOLD}）")
    parser.add_argument("--decision-approved", action="store_true",
                        help="已阅读并认可预处理层的范围划分，跳过决策闸门继续执行")
    parser.add_argument("--stop-after",
                        choices=["preprocess", "extract", "verify"],
                        help="跑完指定层后停止")
    parser.add_argument("--reuse-preprocess", action="store_true",
                        help="复用 work 目录下已有的 preprocess.json，不重跑 Layer 1")

    args = parser.parse_args()

    from extract import load_config, resolve_output_root

    try:
        config = load_config(args.config)
        repo_path = os.path.abspath(args.repo)
        project_name = os.path.basename(repo_path.rstrip("/")) or repo_path

        work_dir = os.path.abspath(os.path.join(args.work_root, project_name))
        os.makedirs(work_dir, exist_ok=True)
        output_root = resolve_output_root(config, args.output_root)
        output_dir = os.path.join(output_root, project_name, args.adapter)
        output_path = os.path.join(output_dir, f"{args.output_type}.md")

        logger.info("项目=%s work=%s 产物=%s", project_name, work_dir, output_path)

        # ---- Layer 1
        pre_path = os.path.join(work_dir, "preprocess.json")
        if args.reuse_preprocess and os.path.isfile(pre_path):
            logger.info("复用已有 preprocess.json")
            pre = _read_json(pre_path)
        else:
            pre = layer1_preprocess(repo_path, work_dir, model=args.model,
                                    threshold=args.threshold)
            _write_json(pre_path, pre)

        if pre.get("needs_user_decision") and not args.decision_approved:
            path = write_decision_request(work_dir, pre)
            logger.warning(
                "预处理层需要用户决策，流水线停止。请阅读 %s，"
                "确认后加 --decision-approved 重跑（可配 --reuse-preprocess 跳过重扫）",
                path,
            )
            sys.exit(EXIT_NEEDS_DECISION)

        if args.stop_after == "preprocess":
            logger.info("--stop-after preprocess，结束")
            return

        # ---- Layer 2
        raw_path, cov = layer2_extract(repo_path, work_dir, pre,
                                       adapter_name=args.adapter, config=config,
                                       model=args.model)
        _write_json(os.path.join(work_dir, "coverage.json"), cov)

        if cov.get("blocking"):
            logger.error("解读层阻塞：%s", cov.get("blocking_reason"))
            sys.exit(EXIT_EXTRACT_BLOCKED)

        if args.stop_after == "extract":
            logger.info("--stop-after extract，结束")
            return

        # ---- Layer 3
        ver = layer3_verify(repo_path, work_dir, output_dir, model=args.model)
        _write_json(os.path.join(work_dir, "verify.json"), ver)

        if ver.get("blocking"):
            logger.error("校验层阻塞：%s\n详见 %s",
                         ver.get("blocking_reason"),
                         os.path.join(output_dir, "check.md"))
            sys.exit(EXIT_VERIFY_BLOCKED)

        if args.stop_after == "verify":
            logger.info("--stop-after verify，结束")
            return

        # ---- Layer 4
        final = layer4_refine(repo_path, work_dir, output_path,
                              output_type=args.output_type, model=args.model)
        logger.info("✅ 流水线完成：%s", final)
        logger.info("校验记录：%s", os.path.join(output_dir, "check.md"))

    except ar.AgentError as e:
        logger.error("❌ subagent 失败: %s", e)
        sys.exit(1)
    except Exception as e:
        logger.error("❌ 执行失败: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
