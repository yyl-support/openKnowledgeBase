"""
MemoryKnowledge (MK) 适配器
通过 HTTP API 调用 MemoryKnowledge 服务提取代码知识

MK 服务契约（已对照 TencentDB-Agent-Memory/MemoryKnowledge/
的 src/routes/wiki.ts 与 src/store/wiki-service.ts 核实）：
- 默认端口 8421，所有接口路径前缀 /v3（可配置，对应服务端 config.apiPrefix）
- 所有 wiki 相关接口均为 POST，统一响应包裹 {code, message, request_id?, data}
- 每个请求必须带 x-tdai-service-id 请求头（service_id），以及 body 中的 team_id
- wiki 状态机：draft -> pending/processing -> ready | failed
"""
import logging
import os
import time
from typing import Dict, List, Optional

import requests

from .base import BaseAdapter


logger = logging.getLogger(__name__)


# MK /raw/write 单次请求的硬限制（见 routes/wiki.ts）
MAX_FILE_SIZE = 512 * 1024
MAX_FILES_PER_REQUEST = 10
MAX_TOTAL_PER_REQUEST = 5 * 1024 * 1024

# MK /page/read 单次请求最多的 refs 数（见 store/wiki-service.ts PAGE_READ_MAX）
PAGE_READ_MAX = 20

# 内部兜底扫描时识别的源文件后缀（未提供外部 source_files 时使用）
DEFAULT_SCAN_EXTENSIONS = ('.py', '.js', '.ts', '.java', '.go', '.md', '.yaml', '.yml', '.json', '.sh')
DEFAULT_IGNORE_DIRS = {'.git', '.venv', 'venv', 'node_modules', '__pycache__', '.ua', '.understand-anything'}


class MKAdapter(BaseAdapter):
    """MemoryKnowledge 适配器"""

    def __init__(
        self,
        api_url: str,
        service_name: str = "trial-svc",
        team_name: str = "trial-team",
        api_prefix: str = "/v3",
        poll_interval: int = 10,
        poll_timeout: int = 1800,
    ):
        """
        初始化 MK 适配器

        Args:
            api_url: MemoryKnowledge API 地址（如 http://localhost:8421，不含路径前缀）
            service_name: 作为 x-tdai-service-id 请求头值的服务标识
            team_name: 作为请求体 team_id 字段的团队标识
            api_prefix: API 路径前缀（默认 /v3，需与服务端 config.apiPrefix 一致）
            poll_interval: 轮询 wiki 状态的间隔（秒）
            poll_timeout: 轮询等待 ready/failed 的最大总时长（秒），ingest 可能耗时较长故默认较宽松
        """
        self.base_url = api_url.rstrip('/') + api_prefix.rstrip('/')
        self.service_name = service_name
        self.team_name = team_name
        self.poll_interval = poll_interval
        self.poll_timeout = poll_timeout

    def get_tool_name(self) -> str:
        return "mk"

    def extract(
        self,
        repo_path: str,
        output_dir: str,
        source_files: Optional[List[Dict[str, str]]] = None,
        wiki_id: Optional[str] = None,
    ) -> Dict:
        """
        从 MemoryKnowledge 提取知识

        流程：
        1. 创建 wiki（或复用传入的 wiki_id）
        2. 批量写入源文件到 raw/write（遵守单文件/单请求/总量限制）
        3. 触发 ingest
        4. 轮询 get() 直到 status 为 ready 或 failed
        5. page/ls 获取页面列表，再逐批 page/read 读取内容
        6. 组装为 BaseAdapter 统一的 pages[] 契约

        Args:
            repo_path: 代码仓路径（本地目录）
            output_dir: 工作目录（本适配器未使用临时文件，保留以满足接口签名）
            source_files: 可选，外部已选好的源文件列表 [{"filename","content"}, ...]
                （用于配合 source_selector 模块；不传时内部按默认规则扫描 repo_path）
            wiki_id: 可选，复用已存在的 wiki（跳过创建步骤）

        Returns:
            提取结果字典
        """
        logger.info(f"MKAdapter: 开始提取知识，仓库路径: {repo_path}")

        if source_files is not None:
            files = source_files
            logger.info(f"MKAdapter: 使用外部传入的源文件列表，共 {len(files)} 个")
        else:
            files = self._scan_source_files(repo_path)
            logger.info(f"MKAdapter: 内部扫描到源文件，共 {len(files)} 个")

        if not files:
            raise RuntimeError(f"未找到任何可上传的源文件: {repo_path}")

        if wiki_id:
            detail = self._get_wiki(wiki_id)
            if detail is None:
                raise RuntimeError(f"指定的 wiki_id 不存在: {wiki_id}")
            logger.info(f"MKAdapter: 复用已有 wiki，wiki_id={wiki_id}")
        else:
            name = os.path.basename(repo_path.rstrip('/')) or repo_path
            detail = self._create_wiki(name)
            wiki_id = detail["wiki_id"]
            logger.info(f"MKAdapter: 创建 wiki 成功，wiki_id={wiki_id}")

        self._write_sources(wiki_id, files)
        self._ingest(wiki_id)
        final_detail = self._wait_for_ready(wiki_id)
        logger.info(
            f"MKAdapter: wiki 处理完成，status={final_detail['status']} "
            f"page_count={final_detail.get('page_count')}"
        )

        pages_data = self._fetch_all_pages(wiki_id)

        result = {
            "pages": pages_data,
            "tool": self.get_tool_name(),
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "repo": repo_path,
        }

        logger.info(f"MKAdapter: 提取完成，共 {len(pages_data)} 个页面")
        return result

    # ───────────────────────── 内部：HTTP 调用封装 ─────────────────────────

    def _post(self, path: str, body: Dict, timeout: int = 30) -> Dict:
        """
        向 MK 发起 POST 请求，解析统一响应包裹 {code, message, data}。
        code != 0 时抛出携带 message 的 RuntimeError（无论 HTTP 状态码是多少，
        MK 的错误信息都在 JSON body 里，不依赖状态码）。
        """
        url = f"{self.base_url}{path}"
        headers = {
            "Content-Type": "application/json",
            "x-tdai-service-id": self.service_name,
        }
        try:
            response = requests.post(url, json=body, headers=headers, timeout=timeout)
        except requests.RequestException as e:
            raise RuntimeError(f"请求 MK 失败 {path}: {e}")

        try:
            envelope = response.json()
        except ValueError:
            raise RuntimeError(f"MK 响应非 JSON（HTTP {response.status_code}）：{path}")

        code = envelope.get("code")
        if code != 0:
            message = envelope.get("message", "未知错误")
            raise RuntimeError(f"MK 接口 {path} 返回错误（code={code}）: {message}")

        return envelope.get("data") or {}

    # ───────────────────────── 内部：wiki 生命周期 ─────────────────────────

    def _create_wiki(self, name: str) -> Dict:
        body = {"team_id": self.team_name, "name": name}
        return self._post("/wiki/create", body)

    def _get_wiki(self, wiki_id: str) -> Optional[Dict]:
        try:
            return self._post("/wiki/get", {"wiki_id": wiki_id})
        except RuntimeError as e:
            if "not found" in str(e):
                return None
            raise

    def _write_sources(self, wiki_id: str, files: List[Dict[str, str]]):
        """
        批量写入源文件，遵守 MK /raw/write 的限制：
        单文件 <= 512KB，单请求 <= 10 个文件且总大小 <= 5MB。
        超过单文件大小限制的文件会被跳过并记录 warning（source_selector 已提前截断，
        正常情况下不会触发；内部兜底扫描时可能触发）。
        """
        batches: List[List[Dict[str, str]]] = []
        current: List[Dict[str, str]] = []
        current_size = 0

        for f in files:
            filename = f["filename"]
            content = f["content"]
            size = len(content.encode("utf-8"))

            if size > MAX_FILE_SIZE:
                logger.warning(
                    f"MKAdapter: 文件超过单文件大小限制（{size} > {MAX_FILE_SIZE} 字节），已跳过: {filename}"
                )
                continue

            if current and (len(current) >= MAX_FILES_PER_REQUEST or current_size + size > MAX_TOTAL_PER_REQUEST):
                batches.append(current)
                current = []
                current_size = 0

            current.append(f)
            current_size += size

        if current:
            batches.append(current)

        logger.info(f"MKAdapter: 源文件写入分 {len(batches)} 批（共 {sum(len(b) for b in batches)} 个文件）")

        for i, batch in enumerate(batches, start=1):
            body = {
                "team_id": self.team_name,
                "wiki_id": wiki_id,
                "files": [{"filename": f["filename"], "content": f["content"]} for f in batch],
            }
            self._post("/wiki/raw/write", body, timeout=300)
            logger.info(f"MKAdapter: 第 {i}/{len(batches)} 批写入成功（{len(batch)} 个文件）")

    def _ingest(self, wiki_id: str):
        body = {"wiki_id": wiki_id}
        try:
            data = self._post("/wiki/ingest", body, timeout=60)
            logger.info(f"MKAdapter: ingest 已触发，status={data.get('status')}")
        except RuntimeError as e:
            # busy（已有 ingest 在处理中）不是致命错误，交由后续轮询兜底
            if "busy" in str(e).lower():
                logger.info("MKAdapter: wiki 正在处理中（busy），转入轮询等待")
            else:
                raise

    def _wait_for_ready(self, wiki_id: str) -> Dict:
        """轮询 /wiki/get 直到 status 为 ready 或 failed，超时则抛出异常。"""
        start = time.time()
        while True:
            detail = self._get_wiki(wiki_id)
            if detail is None:
                raise RuntimeError(f"轮询期间 wiki 不存在: {wiki_id}")

            status = detail.get("status")
            logger.info(f"MKAdapter: wiki 状态 = {status}")

            if status == "ready":
                return detail
            if status == "failed":
                sync_error = detail.get("sync_error") or "未知错误"
                raise RuntimeError(f"wiki 处理失败: {sync_error}")

            if time.time() - start > self.poll_timeout:
                raise RuntimeError(
                    f"等待 wiki 处理完成超时（{self.poll_timeout}秒），当前状态: {status}"
                )

            time.sleep(self.poll_interval)

    # ───────────────────────── 内部：页面读取 ─────────────────────────

    def _fetch_all_pages(self, wiki_id: str) -> List[Dict]:
        page_list = self._post("/wiki/page/ls", {"wiki_id": wiki_id}).get("items", [])
        logger.info(f"MKAdapter: 获取到 {len(page_list)} 个页面")

        if not page_list:
            return []

        page_info_by_ref = {p["id"]: p for p in page_list}
        refs = [p["id"] for p in page_list]

        pages_data: List[Dict] = []
        for i in range(0, len(refs), PAGE_READ_MAX):
            batch_refs = refs[i:i + PAGE_READ_MAX]
            items = self._post("/wiki/page/read", {"wiki_id": wiki_id, "refs": batch_refs}).get("items", [])

            for item in items:
                ref = item.get("ref")
                if item.get("not_found"):
                    logger.warning(f"MKAdapter: 页面未找到，已跳过: {ref}")
                    continue

                info = page_info_by_ref.get(ref, {})
                pages_data.append({
                    "title": info.get("title", ref),
                    "content": item.get("content", ""),
                    "metadata": {
                        "id": ref,
                        "type": info.get("type", "unknown"),
                        "locked": info.get("locked", False),
                    },
                    "path": info.get("path", ""),
                })

        return pages_data

    # ───────────────────────── 内部：兜底源文件扫描 ─────────────────────────

    def _scan_source_files(self, repo_path: str) -> List[Dict[str, str]]:
        """
        未提供外部 source_files 时的默认扫描逻辑：递归收集常见源码/文档文件。
        MK 的 raw 存储原生支持带子目录的文件名（resolveRawPath 已确认），
        因此这里直接使用相对路径作为 filename，无需扁平化转义。
        """
        if not os.path.isdir(repo_path):
            raise ValueError(f"仓库路径不存在或不是目录: {repo_path}")

        files: List[Dict[str, str]] = []
        for root, dirs, filenames in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in DEFAULT_IGNORE_DIRS]

            for filename in filenames:
                if not filename.endswith(DEFAULT_SCAN_EXTENSIONS):
                    continue

                abspath = os.path.join(root, filename)
                relpath = os.path.relpath(abspath, repo_path).replace(os.sep, "/")

                try:
                    with open(abspath, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                except OSError as e:
                    logger.warning(f"读取文件失败 {abspath}: {e}")
                    continue

                files.append({"filename": relpath, "content": content})

        return files
