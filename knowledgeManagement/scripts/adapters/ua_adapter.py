"""
Understand-Anything (UA) 适配器

UA 是 Claude Code 插件，没有 HTTP API，也没有独立 CLI：它由 LLM 编排执行
`skills/understand/SKILL.md` 描述的多阶段分析流程，产物落盘到目标仓库的
`.ua/knowledge-graph.json`（新版）或 `.understand-anything/knowledge-graph.json`（旧版兼容）。

本适配器只负责读取磁盘上已生成的产物并转换为 BaseAdapter 统一契约，不负责触发分析
流程——分析必须由用户先在 Claude Code 中对目标仓运行 `/understand` 完成。

已核实的 knowledge-graph.json 结构（参考产物：
/tmp/ua-trial/forum-reply-robot/.ua/knowledge-graph.json）：
{
  "version": "1.0.0",
  "project": {"name","languages","frameworks","description","analyzedAt","gitCommitHash"},
  "nodes": [{"id","type","name","filePath","summary","tags","complexity","languageNotes",...}],
  "edges": [{"source","target","type","direction","weight"}],
  "layers": [{"id","name","description","nodeIds"}],
  "tour": [{"order","title","description","nodeIds","languageLesson"}]
}
"""
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

from .base import BaseAdapter


logger = logging.getLogger(__name__)


# 产物目录名候选：新版 .ua/ 优先，旧版 .understand-anything/ 兼容
UA_DIR_CANDIDATES = ('.ua', '.understand-anything')
KNOWLEDGE_GRAPH_FILENAME = 'knowledge-graph.json'


class UAAdapter(BaseAdapter):
    """Understand-Anything 适配器：从磁盘读取已生成的知识图谱"""

    def __init__(self, data_dir: Optional[str] = None):
        """
        初始化 UA 适配器

        Args:
            data_dir: 可选，直接指定知识图谱产物所在目录（该目录下应有 knowledge-graph.json）。
                不传时按 repo_path 下的 .ua/ 或 .understand-anything/ 自动探测。
        """
        self.data_dir = data_dir

    def get_tool_name(self) -> str:
        return "ua"

    def extract(self, repo_path: str, output_dir: str) -> Dict:
        """
        从 UA 已生成的知识图谱提取知识

        Args:
            repo_path: 代码仓路径（本地目录），用于自动探测 .ua/ 目录
            output_dir: 工作目录（本适配器为纯读取，未使用，保留以满足接口签名）

        Returns:
            提取结果字典（BaseAdapter 统一契约）

        Raises:
            RuntimeError: 找不到知识图谱产物时抛出，提示用户先运行 /understand
        """
        graph_path = self._locate_knowledge_graph(repo_path)
        logger.info(f"UAAdapter: 读取知识图谱: {graph_path}")

        with open(graph_path, 'r', encoding='utf-8') as f:
            graph = json.load(f)

        pages = self._build_pages(graph)

        result = {
            "pages": pages,
            "tool": self.get_tool_name(),
            "timestamp": datetime.now().isoformat(),
            "repo": repo_path,
        }

        logger.info(f"UAAdapter: 提取完成，共 {len(pages)} 个页面")
        return result

    # ───────────────────────── 内部：定位产物 ─────────────────────────

    def _locate_knowledge_graph(self, repo_path: str) -> str:
        """
        定位 knowledge-graph.json：
        1. 若显式指定 data_dir，只在该目录下查找
        2. 否则依次尝试 repo_path/.ua/ 与 repo_path/.understand-anything/

        找不到时抛出清晰的错误（绝不静默返回空结果），提示用户先运行 /understand。
        """
        if self.data_dir:
            candidate_dirs = [self.data_dir]
        else:
            candidate_dirs = [os.path.join(repo_path, d) for d in UA_DIR_CANDIDATES]

        for candidate_dir in candidate_dirs:
            graph_path = os.path.join(candidate_dir, KNOWLEDGE_GRAPH_FILENAME)
            if os.path.isfile(graph_path):
                return graph_path

        tried = [os.path.join(d, KNOWLEDGE_GRAPH_FILENAME) for d in candidate_dirs]
        raise RuntimeError(
            f"未找到 UA 知识图谱产物，已尝试路径: {tried}。"
            f"UA 是 Claude Code 插件，没有 HTTP API，需要先在目标仓库对应的 Claude Code 会话中"
            f"运行 /understand 完成分析，生成 .ua/{KNOWLEDGE_GRAPH_FILENAME} 后再重试。"
        )

    # ───────────────────────── 内部：图谱转换 ─────────────────────────

    def _build_pages(self, graph: Dict) -> List[Dict]:
        """
        将 knowledge-graph.json 的 project/nodes/layers/tour/edges 转换为 pages[]：
        - 1 个项目概览页（来自 project）
        - 1 个项目导览页（来自 tour，按 order 顺序拼接各步骤）
        - 每个 layer 一个子系统页（来自 layers）
        - 每个 node 一个页面（来自 nodes；content 取 summary/description，
          metadata 保留 nodeType/layer/tags/relations，path 取 filePath）
        """
        pages: List[Dict] = []

        project = graph.get("project") or {}
        nodes = graph.get("nodes") or []
        layers = graph.get("layers") or []
        tour = graph.get("tour") or []
        edges = graph.get("edges") or []

        node_id_to_layer = self._build_node_layer_map(layers)
        node_id_to_relations = self._build_node_relations_map(edges)

        if project:
            pages.append(self._build_project_page(project))

        if tour:
            pages.append(self._build_tour_page(tour))

        for layer in layers:
            pages.append(self._build_layer_page(layer))

        for node in nodes:
            pages.append(self._build_node_page(node, node_id_to_layer, node_id_to_relations))

        return pages

    def _build_node_layer_map(self, layers: List[Dict]) -> Dict[str, str]:
        """构建 node_id -> 所属 layer 名称 的映射"""
        mapping: Dict[str, str] = {}
        for layer in layers:
            layer_name = layer.get("name") or layer.get("id", "")
            for node_id in layer.get("nodeIds", []):
                mapping[node_id] = layer_name
        return mapping

    def _build_node_relations_map(self, edges: List[Dict]) -> Dict[str, List[Dict]]:
        """构建 node_id -> 与其相关的边列表 的映射（同时记录出边和入边方向）"""
        mapping: Dict[str, List[Dict]] = {}
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            edge_type = edge.get("type")

            if source:
                mapping.setdefault(source, []).append({
                    "direction": "outgoing", "type": edge_type, "with": target,
                })
            if target:
                mapping.setdefault(target, []).append({
                    "direction": "incoming", "type": edge_type, "with": source,
                })
        return mapping

    def _build_project_page(self, project: Dict) -> Dict:
        name = project.get("name", "项目概览")
        lines = [f"# {name}", ""]

        description = project.get("description")
        if description:
            lines.append(description)
            lines.append("")

        languages = project.get("languages")
        if languages:
            lines.append(f"**语言**：{', '.join(languages)}")

        frameworks = project.get("frameworks")
        if frameworks:
            lines.append(f"**框架/依赖**：{', '.join(frameworks)}")

        return {
            "title": f"{name} - 项目概览",
            "content": "\n".join(lines),
            "metadata": {
                "nodeType": "project",
                "gitCommitHash": project.get("gitCommitHash"),
                "analyzedAt": project.get("analyzedAt"),
            },
            "path": "",
        }

    def _build_tour_page(self, tour: List[Dict]) -> Dict:
        steps = sorted(tour, key=lambda s: s.get("order", 0))
        lines = ["# 项目导览", ""]

        for step in steps:
            lines.append(f"## {step.get('order')}. {step.get('title', '')}")
            lines.append("")
            if step.get("description"):
                lines.append(step["description"])
                lines.append("")
            if step.get("languageLesson"):
                lines.append(f"> 语言要点：{step['languageLesson']}")
                lines.append("")
            node_ids = step.get("nodeIds") or []
            if node_ids:
                lines.append(f"相关节点：{', '.join(node_ids)}")
                lines.append("")

        return {
            "title": "项目导览",
            "content": "\n".join(lines),
            "metadata": {
                "nodeType": "tour",
                "stepCount": len(steps),
            },
            "path": "",
        }

    def _build_layer_page(self, layer: Dict) -> Dict:
        name = layer.get("name") or layer.get("id", "未命名子系统")
        node_ids = layer.get("nodeIds") or []

        content_lines = [layer.get("description", "")]
        if node_ids:
            content_lines.append("")
            content_lines.append(f"包含节点：{', '.join(node_ids)}")

        return {
            "title": name,
            "content": "\n".join(content_lines),
            "metadata": {
                "nodeType": "layer",
                "layerId": layer.get("id"),
                "nodeIds": node_ids,
            },
            "path": "",
        }

    def _build_node_page(
        self,
        node: Dict,
        node_id_to_layer: Dict[str, str],
        node_id_to_relations: Dict[str, List[Dict]],
    ) -> Dict:
        node_id = node.get("id", "")
        content = node.get("summary") or node.get("description") or ""
        if node.get("languageNotes"):
            content = f"{content}\n\n语言/实现要点：{node['languageNotes']}"

        return {
            "title": node.get("name", node_id),
            "content": content,
            "metadata": {
                "nodeType": node.get("type"),
                "layer": node_id_to_layer.get(node_id),
                "tags": node.get("tags", []),
                "complexity": node.get("complexity"),
                "relations": node_id_to_relations.get(node_id, []),
            },
            "path": node.get("filePath", ""),
        }
