#!/usr/bin/env python3
"""
UA 知识图谱 schema 归一化

UA 的 file-analyzer subagent 会输出两种不同的节点 schema。实测 codearts-workflow-image
（64 个批次）中有 16 个批次（25%）用了错误字段名：

    正确：{id, name, type, filePath, summary, tags, complexity}
    错误：{id, label, type, path,     purpose, ...}

UA 的 merge 脚本会补齐 name/summary，但不补 filePath，导致这些节点在最终图谱里缺
filePath。后果：下游按路径索引全部找不到，实测 644 个节点中 116 个（18%）失效，
其中包含 core 层的 cp_artifact_manager.go 与 heartbeat_manager.go。

SKILL.md 反复强调批次**文件命名**不能错（merge 正则会静默丢弃），但没有对**字段
schema** 做校验，merge 照单全收。这是 UA 侧的缺陷，本脚本在读入后修正。

修正规则（全部确定性，不调模型）：
1. 有 path 无 filePath  → filePath = path
2. 两者都无             → 通过边反推：与之相连的 file: 节点即其所属文件
3. 仍无法确定           → 保留原样并报告，不静默丢弃

用法：
    python normalize_ua_graph.py <repo_path> [--dry-run]
"""
import argparse
import json
import os
import shutil
import sys
from typing import Dict, List, Tuple


def normalize(graph: Dict) -> Tuple[Dict, Dict]:
    """
    归一化图谱节点的 filePath 字段。

    Returns:
        (归一化后的 graph, 统计信息)
    """
    nodes: List[Dict] = graph.get("nodes") or []
    edges: List[Dict] = graph.get("edges") or []

    stats = {"total": len(nodes), "already_ok": 0, "from_path": 0,
             "from_edges": 0, "unresolved": [], "aliased_fields": 0}

    # 先补齐别名字段：label→name、purpose→summary（merge 通常已做，这里兜底）
    for n in nodes:
        changed = False
        if not n.get("name") and n.get("label"):
            n["name"] = n["label"]; changed = True
        if not n.get("summary") and n.get("purpose"):
            n["summary"] = n["purpose"]; changed = True
        if changed:
            stats["aliased_fields"] += 1

    # 规则 1：path → filePath
    missing = []
    for n in nodes:
        if n.get("filePath"):
            stats["already_ok"] += 1
        elif n.get("path"):
            n["filePath"] = n["path"]
            stats["from_path"] += 1
        else:
            missing.append(n)

    # 规则 2：通过边反推。与该节点相连的 file: 节点即其所属文件
    if missing:
        by_id = {n.get("id"): n for n in nodes}
        linked_file: Dict[str, str] = {}
        for e in edges:
            s, t = e.get("source"), e.get("target")
            for a, b in ((s, t), (t, s)):
                if a and b and str(b).startswith("file:") and a not in linked_file:
                    linked_file[a] = str(b)

        for n in missing:
            nid = n.get("id")
            file_node_id = linked_file.get(nid)
            if not file_node_id:
                stats["unresolved"].append(nid)
                continue
            fnode = by_id.get(file_node_id)
            # 优先取该 file 节点已归一化的 filePath，退而从 id 去前缀
            path = (fnode or {}).get("filePath") or file_node_id[len("file:"):]
            if path:
                n["filePath"] = path
                stats["from_edges"] += 1
            else:
                stats["unresolved"].append(nid)

    return graph, stats


def main() -> int:
    ap = argparse.ArgumentParser(description="UA 知识图谱 schema 归一化")
    ap.add_argument("repo_path", help="目标仓库路径（含 .ua/ 目录）")
    ap.add_argument("--dry-run", action="store_true", help="只报告，不写回")
    args = ap.parse_args()

    for d in (".ua", ".understand-anything"):
        gp = os.path.join(args.repo_path, d, "knowledge-graph.json")
        if os.path.isfile(gp):
            break
    else:
        print(f"未找到 knowledge-graph.json（已试 .ua/ 与 .understand-anything/）",
              file=sys.stderr)
        return 1

    with open(gp, "r", encoding="utf-8") as f:
        graph = json.load(f)

    graph, st = normalize(graph)

    print(f"图谱: {gp}")
    print(f"  节点总数        {st['total']}")
    print(f"  原本已有 filePath {st['already_ok']}")
    print(f"  由 path 补齐      {st['from_path']}")
    print(f"  由边反推补齐      {st['from_edges']}")
    print(f"  补齐别名字段      {st['aliased_fields']}")
    print(f"  仍无法确定        {len(st['unresolved'])}")
    if st["unresolved"]:
        for i in st["unresolved"][:10]:
            print(f"    - {i}")

    fixed = st["from_path"] + st["from_edges"]
    if args.dry_run:
        print(f"\n--dry-run，未写回。可修正 {fixed} 个节点")
        return 0

    if fixed == 0:
        print("\n无需修正")
        return 0

    backup = gp + ".pre-normalize.bak"
    if not os.path.exists(backup):
        shutil.copy(gp, backup)
        print(f"\n已备份原图谱: {backup}")
    with open(gp, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)
    print(f"已写回，修正 {fixed} 个节点")
    return 0


if __name__ == "__main__":
    sys.exit(main())
