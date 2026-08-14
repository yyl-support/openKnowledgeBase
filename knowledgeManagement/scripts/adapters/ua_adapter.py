"""
Understand-Anything (UA) 适配器

UA 是 Claude Code 插件，没有 HTTP API，也没有独立 CLI：它由 LLM 编排执行
`skills/understand/SKILL.md` 描述的多阶段分析流程，产物落盘到目标仓库的
`.ua/knowledge-graph.json`（新版）或 `.understand-anything/knowledge-graph.json`（旧版兼容）。

本适配器既能读取磁盘上已生成的产物，也能自己驱动 UA 完成分析（auto_run=True，默认）：
以 `claude -p --plugin-dir <UA插件目录>` 启动一个非交互会话，让它调用
`understand-anything:understand` skill。

驱动 UA 必须用 `--permission-mode bypassPermissions`（配合
`--allow-dangerously-skip-permissions`）：UA 每个阶段都要通过 Bash 运行自带的 node
脚本（scan-project.mjs / extract-structure.mjs / compute-batches.mjs /
build-fingerprints.mjs 等），`dontAsk` 模式下 Bash 被全部拒绝，UA 会直接放弃执行。
这是一次实际的权限放开，因此：
- 默认只在目标仓库目录内执行，产物只落 `<repo>/.ua/`
- auto_run 必须由调用方显式保留（可关掉退回纯读取模式）

实测耗时基准：2 个文件约 10 分钟、5 个文件约 12 分钟走完全部 7 个阶段。可见固定开销
占大头，但大仓的分析批次会显著变多，因此 run_timeout 默认给到 10800 秒（3 小时）。
UA 的文件分析阶段是分批并发的，不随文件数线性放大。

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
import subprocess
from datetime import datetime
from typing import Dict, List, Optional

from .base import BaseAdapter


logger = logging.getLogger(__name__)


# 产物目录名候选：新版 .ua/ 优先，旧版 .understand-anything/ 兼容
UA_DIR_CANDIDATES = ('.ua', '.understand-anything')
KNOWLEDGE_GRAPH_FILENAME = 'knowledge-graph.json'
META_FILENAME = 'meta.json'

# UA 插件位置的探测顺序。不写死绝对路径 —— 换一台机器路径就不存在，
# 而 UA 是 Layer 2 的唯一入口，路径错了整条流水线跑不起来。
#
# 顺序：环境变量 > install.sh 的标准安装位置 > 与本仓库并列的源码克隆
PLUGIN_DIR_ENV = 'UA_PLUGIN_DIR'


def _default_plugin_dir_candidates() -> List[str]:
    """UA 插件的候选位置，按优先级从高到低。"""
    home = os.path.expanduser('~')
    # 本文件位于 <repo>/knowledgeManagement/scripts/adapters/，上溯 4 级到仓库父目录
    repo_parent = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     '..', '..', '..', '..')
    )
    return [
        # install.sh: PLUGIN_LINK="$HOME/.understand-anything-plugin"
        os.path.join(home, '.understand-anything-plugin'),
        # install.sh: REPO_DIR="${UA_DIR:-$HOME/.understand-anything/repo}"
        os.path.join(home, '.understand-anything', 'repo',
                     'understand-anything-plugin'),
        # Claude Code 插件目录
        os.path.join(home, '.claude', 'plugins', 'understand-anything',
                     'understand-anything-plugin'),
        # 与本仓库并列的源码克隆
        os.path.join(repo_parent, 'Understand-Anything',
                     'understand-anything-plugin'),
    ]


def resolve_plugin_dir(explicit: Optional[str] = None) -> Optional[str]:
    """
    解析 UA 插件目录。找不到返回 None，由调用方给出可操作的错误提示。

    优先级：显式传入 > 环境变量 UA_PLUGIN_DIR > 标准安装位置 > 并列源码克隆
    """
    if explicit:
        return explicit

    env = os.getenv(PLUGIN_DIR_ENV)
    if env:
        return env

    for cand in _default_plugin_dir_candidates():
        if os.path.isdir(cand):
            logger.info("UAAdapter: 自动探测到 UA 插件目录 %s", cand)
            return cand
    return None

# skill 全名：必须带插件前缀，不带前缀模型找不到
UNDERSTAND_SKILL = 'understand-anything:understand'

# 驱动 UA 的 prompt。明确要求走完全部阶段，并点出 SKILL.md 里那条会静默丢数据的坑：
# 融合 batch 时输出文件名必须仍按原 batchIndex 命名，否则 merge 脚本的正则
# batch-(\d+)(?:-part-(\d+))?\.json 会静默丢掉整个文件的节点和边。
UNDERSTAND_PROMPT = """调用 Skill 工具执行 {skill}，对当前目录（{repo}）做完整分析，\
严格按 SKILL.md 的全部阶段执行到底，产出 .ua/{graph} 。

## 本次为非交互运行，以下确认点已预先授权

SKILL.md 的 Phase 0.5（Ignore Configuration）在两个分支上都写了
「Wait for user confirmation before proceeding」。**本次运行中该确认视为已给出**：
生成或发现 `.ua/.understandignore` 后，直接采用其当前内容继续执行 Phase 1，
不要停下来等待确认。其他阶段若也有类似的「等待用户确认」步骤，同样视为已确认。

这条必须遵守：本会话没有交互对端，停下来等确认等于永久挂起 —— 实测会话会在
生成 ignore 文件后直接结束回合，导致整轮分析零产出。

## 强制要求
1. 不得跳过任何阶段，不得因为文件多而自行抽样或截断分析范围。
2. SKILL.md 中关于 batch 输出文件命名的约束必须遵守：若融合多个小 batch 做一次 \
dispatch，被派发的 agent 仍必须按原 batchIndex 逐个写出 batch-<batchIndex>.json；\
其他命名会被 merge 脚本的正则静默丢弃，导致该文件内全部节点和边丢失。
3. 每次 dispatch 返回后，逐个校验对应的 batch-<batchIndex>.json 是否已落盘，\
确认后再继续下一阶段。

完成后只报告三个数字：节点数、边数、分析文件数。"""

# 续跑 prompt。
#
# 为什么需要它：UA 的 Phase 2 是无条件遍历 batches.json，没有「已存在就跳过」的逻辑。
# 实测事故：分析 2191 个文件（204 batch）时，驱动会话在 wave 9 之后反复遇到 Agent
# 工具的 prompt 截断错误，派发不下去，停在 176/204 直接退出（退出码 0，无图谱）。
# 原样重跑会把已完成的 176 个 batch 全部重做，并很可能在同一位置再次撞上截断。
#
# 这是对 UA 标准流程的显式偏离，因此：
# - 只在检测到「有 batches.json 且部分 batch 已落盘」时启用
# - 缺失清单由 Python 精确算出后写进 prompt，不让模型自己去数
UNDERSTAND_RESUME_PROMPT = """继续一次被中断的 {skill} 分析，当前目录是 {repo}。

## 已有状态（由外部精确统计，直接采信，不要重新清点）

- `.ua/intermediate/batches.json` 已存在，共 {total} 个 batch
- 其中 {done} 个已完成并落盘（batch-<i>.json 或 batch-<i>-part-<k>.json）
- 缺失 {missing_count} 个，batchIndex 为：{missing_list}

## 本次为非交互运行，确认点已预先授权

SKILL.md 中任何「Wait for user confirmation」步骤（含 Phase 0.5 的
`.understandignore` 审阅）本次均视为已确认，直接采用当前内容继续，不要停下等待。
本会话没有交互对端，停下等确认等于永久挂起。

## 你要做的事

1. **只处理上面列出的缺失 batchIndex，不要重跑已完成的 batch。** 已落盘的文件不得
   删除、覆盖或重写。
2. 按 SKILL.md 的 Phase 2 ANALYZE 规则派发 file-analyzer subagent 处理这些 batch，
   batch 参数从 `batches.json` 里对应下标取。输出文件名必须是
   `batch-<batchIndex>.json` 或 `batch-<batchIndex>-part-<k>.json` —— 其他命名会被
   merge 脚本的正则 `batch-(\\d+)(?:-part-(\\d+))?\\.json` 静默丢弃，导致该文件内
   全部节点和边丢失。
3. 每次 dispatch 返回后，逐个校验对应文件是否已落盘，确认后再继续下一批。
4. 全部缺失 batch 落盘后，确认 1..{total} 每个 batchIndex 都有对应文件，然后按
   SKILL.md 顺序执行剩余阶段直到结束：merge-batch-graphs.py、Phase 3 ASSEMBLE
   REVIEW、Phase 4 ARCHITECTURE、Phase 5 TOUR、Phase 6 REVIEW、Phase 7 SAVE，
   最终产出 .ua/{graph}。

## 硬约束

- 为控制上下文压力，每次最多并发 3 个 subagent，一次 dispatch 不要塞超过 4 个 batch。
- 不得因为剩余量大而自行跳过、抽样或截断任何 batch。确实无法继续时，停下来报告
  「已完成到 batchIndex X，剩余 Y 个未处理」，不要产出残缺的图谱。
- Phase 7 的 meta.json 必须在 fingerprints 基线成功写入之后再写。

完成后只报告三个数字：节点数、边数、分析文件数。"""


class UAAdapterError(RuntimeError):
    """UA 驱动失败或产物缺失"""


class UAAdapter(BaseAdapter):
    """Understand-Anything 适配器：驱动 UA 分析并读取其知识图谱"""

    def __init__(
        self,
        data_dir: Optional[str] = None,
        *,
        auto_run: bool = True,
        plugin_dir: Optional[str] = None,
        model: str = 'claude-sonnet-5',
        run_timeout: int = 10800,
        force_rerun: bool = False,
        require_fresh: bool = True,
    ):
        """
        初始化 UA 适配器

        Args:
            data_dir: 可选，直接指定知识图谱产物所在目录。不传时按 repo_path 下的
                .ua/ 或 .understand-anything/ 自动探测。
            auto_run: 产物缺失（或过期）时是否自己驱动 UA 生成。False 则退回纯读取，
                找不到就报错。
            plugin_dir: UA 插件目录。不传则按 resolve_plugin_dir 的顺序探测：
                环境变量 UA_PLUGIN_DIR > 标准安装位置 > 与本仓库并列的源码克隆。
            model: 驱动 UA 的会话所用模型。
            run_timeout: 驱动 UA 的超时秒数，默认 10800（3 小时）。
            force_rerun: 即使产物已存在也重跑。
            require_fresh: 产物的 gitCommitHash 与仓库当前 HEAD 不一致时视为过期。
                拿旧 commit 的图谱去核验新代码会得出错误结论，因此默认开启。
        """
        self.data_dir = data_dir
        self.auto_run = auto_run
        self.plugin_dir = resolve_plugin_dir(plugin_dir)
        self.model = model
        self.run_timeout = run_timeout
        self.force_rerun = force_rerun
        self.require_fresh = require_fresh

    def get_tool_name(self) -> str:
        return "ua"

    def extract(self, repo_path: str, output_dir: str, **kwargs) -> Dict:
        """
        提取知识：产物缺失或过期时先驱动 UA 分析，再读取知识图谱

        Args:
            repo_path: 代码仓路径（本地目录）
            output_dir: 工作目录，用于存放 UA 运行日志
            **kwargs: 忽略（兼容其他 adapter 的调用形式）

        Returns:
            提取结果字典（BaseAdapter 统一契约）

        Raises:
            UAAdapterError: 驱动失败，或 auto_run=False 且产物缺失
        """
        graph_path = self._resolve_graph(repo_path, output_dir)
        logger.info("UAAdapter: 读取知识图谱: %s", graph_path)

        with open(graph_path, 'r', encoding='utf-8') as f:
            graph = json.load(f)

        pages = self._build_pages(graph)
        self._normalize_page_paths(pages, repo_path)

        result = {
            "pages": pages,
            "tool": self.get_tool_name(),
            "timestamp": datetime.now().isoformat(),
            "repo": repo_path,
            "graph_stats": {
                "nodes": len(graph.get("nodes") or []),
                "edges": len(graph.get("edges") or []),
                "layers": len(graph.get("layers") or []),
                "tour_steps": len(graph.get("tour") or []),
            },
        }

        logger.info("UAAdapter: 提取完成，共 %d 个页面（节点 %d / 边 %d）",
                    len(pages), result["graph_stats"]["nodes"],
                    result["graph_stats"]["edges"])
        return result

    # ───────────────────────── 内部：驱动 UA ─────────────────────────

    def _resolve_graph(self, repo_path: str, output_dir: str) -> str:
        """
        拿到一份可用的知识图谱路径：已有且新鲜就直接用，否则按 auto_run 决定是否驱动。
        """
        existing = self._find_existing_graph(repo_path)

        if existing and not self.force_rerun:
            stale = self._staleness_reason(repo_path, existing)
            if not stale:
                return existing
            if not self.auto_run:
                raise UAAdapterError(
                    f"UA 产物已过期：{stale}。auto_run=False，拒绝使用过期产物 —— "
                    f"拿旧 commit 的图谱核验新代码会得出错误结论。"
                    f"请重新运行 UA，或显式设 require_fresh=False。"
                )
            logger.warning("UAAdapter: 产物过期（%s），重新驱动 UA", stale)
        elif existing and self.force_rerun:
            logger.info("UAAdapter: force_rerun=True，忽略已有产物重跑")
        else:
            if not self.auto_run:
                raise UAAdapterError(
                    f"未找到 UA 知识图谱产物，且 auto_run=False。"
                    f"请先在目标仓库运行 /understand，或改用 auto_run=True。"
                )
            logger.info("UAAdapter: 未找到产物，开始驱动 UA")

        return self._drive_until_done(repo_path, output_dir)

    def _drive_until_done(self, repo_path: str, output_dir: str) -> str:
        """
        反复驱动 UA 直到产出图谱。

        为什么要循环：实测大仓（2191 文件 / 204 batch）驱动会话会在中途正常结束
        （退出码 0、无图谱），第一次停在 176/204，续跑一次只推进到 185/204。
        单次会话跑不完全程，但每次都能推进若干 batch 且成果落盘，所以按「一次会话
        推进一段」来组织，比指望单次跑完更可靠。

        每轮结束后检查是否有推进：连续 max_stalls 轮没有任何 batch 增加就放弃，
        避免无进展空转。绝不产出残缺图谱。
        """
        max_passes = 12
        max_stalls = 2
        stalls = 0
        prev_done = -1

        for attempt in range(1, max_passes + 1):
            self._run_understand(repo_path, output_dir)

            graph_path = self._find_existing_graph(repo_path)
            if graph_path:
                logger.info("UAAdapter: 第 %d 轮驱动后产出图谱", attempt)
                return graph_path

            state = self._detect_resume_state(repo_path)
            if state is None:
                # 没有可续跑的中间状态，且没有图谱 —— 再驱动也是从头开始，不是进展
                break

            total, done, missing = state
            if done <= prev_done:
                stalls += 1
                logger.warning(
                    "UAAdapter: 第 %d 轮无进展（仍为 %d/%d），连续无进展 %d 次",
                    attempt, done, total, stalls,
                )
                if stalls >= max_stalls:
                    break
            else:
                stalls = 0
                logger.info("UAAdapter: 第 %d 轮推进到 %d/%d batch，继续驱动",
                            attempt, done, total)
            prev_done = done

        graph_path = self._find_existing_graph(repo_path)
        if graph_path:
            return graph_path

        state = self._detect_resume_state(repo_path)
        progress = (f"当前进度 {state[1]}/{state[0]} batch，缺失 {len(state[2])} 个"
                    if state else "无可用的中间状态")
        tried = [os.path.join(repo_path, d, KNOWLEDGE_GRAPH_FILENAME)
                 for d in UA_DIR_CANDIDATES]
        raise UAAdapterError(
            f"驱动 UA 多轮后仍未产出知识图谱。{progress}。已尝试: {tried}。"
            f"中间产物保留在 .ua/intermediate/，可再次运行继续续跑。"
            f"运行日志见 {os.path.join(output_dir, 'ua-run.log')}"
        )

    def _run_understand(self, repo_path: str, output_dir: str) -> None:
        """
        以非交互会话驱动 UA。

        必须 bypassPermissions：UA 每个阶段都要 Bash 跑自带的 node 脚本，
        dontAsk 下 Bash 全被拒，UA 会直接放弃执行并报「无法在受限模式下继续」。
        """
        if not self.plugin_dir or not os.path.isdir(self.plugin_dir):
            tried = "\n  ".join(_default_plugin_dir_candidates())
            raise UAAdapterError(
                f"找不到 UA 插件目录"
                + (f"（给定路径不存在：{self.plugin_dir}）" if self.plugin_dir else "")
                + f"。\n已尝试的标准位置：\n  {tried}\n"
                f"请任选其一解决：\n"
                f"  1. 安装 UA：见 https://github.com/Egonex-AI/Understand-Anything "
                f"的 install.sh\n"
                f"  2. 设置环境变量：export {PLUGIN_DIR_ENV}=<插件目录>\n"
                f"  3. 在 config.yaml 的 adapters.ua.plugin_dir 中指定\n"
                f"若只想读取已有的知识图谱产物、不需要驱动 UA，"
                f"可设 adapters.ua.auto_run: false"
            )

        os.makedirs(output_dir, exist_ok=True)
        log_path = os.path.join(output_dir, 'ua-run.log')

        resume = self._detect_resume_state(repo_path)
        if resume:
            total, done, missing = resume
            logger.info(
                "UAAdapter: 检测到中断的分析（%d/%d batch 已完成），改用续跑模式，"
                "只处理缺失的 %d 个", done, total, len(missing),
            )
            prompt = UNDERSTAND_RESUME_PROMPT.format(
                skill=UNDERSTAND_SKILL, repo=repo_path,
                graph=KNOWLEDGE_GRAPH_FILENAME,
                total=total, done=done, missing_count=len(missing),
                missing_list=", ".join(str(i) for i in missing),
            )
        else:
            prompt = UNDERSTAND_PROMPT.format(
                skill=UNDERSTAND_SKILL, repo=repo_path,
                graph=KNOWLEDGE_GRAPH_FILENAME,
            )
        # --output-format json：拿到 num_turns / stop_reason / terminal_reason /
        # total_cost_usd。实测两次中断时 text 模式只留下半句话（如
        # "Waiting for batch 185 to complete."），退出码 0，失败原因完全是黑盒。
        cmd = [
            'claude', '-p',
            '--output-format', 'json',
            '--plugin-dir', self.plugin_dir,
            '--model', self.model,
            '--allow-dangerously-skip-permissions',
            '--permission-mode', 'bypassPermissions',
            '--autocompact', '1000000',
            prompt,
        ]

        logger.info("UAAdapter: 驱动 UA（model=%s, timeout=%ds），日志: %s",
                    self.model, self.run_timeout, log_path)
        logger.info("UAAdapter: 这一步会实际调用模型，大仓可能耗时数十分钟")

        try:
            proc = subprocess.run(
                cmd, cwd=repo_path, capture_output=True,
                stdin=subprocess.DEVNULL, text=True, timeout=self.run_timeout,
            )
        except subprocess.TimeoutExpired:
            raise UAAdapterError(
                f"UA 运行超时（{self.run_timeout}s）。日志: {log_path}"
            )

        with open(log_path, 'a', encoding='utf-8') as log_file:
            log_file.write(f"\n{'='*60}\n[{datetime.now().isoformat()}] "
                           f"returncode={proc.returncode}\n")
            log_file.write(proc.stdout or '')
            if proc.stderr:
                log_file.write(f"\n--- stderr ---\n{proc.stderr}")

        if proc.returncode != 0:
            raise UAAdapterError(
                f"UA 运行失败，退出码 {proc.returncode}。"
                f"stderr: {(proc.stderr or '')[-1000:]}。日志: {log_path}"
            )

        self._log_session_result(proc.stdout)

    @staticmethod
    def _log_session_result(stdout: str) -> None:
        """
        解析 --output-format json 的会话结果并记日志。

        实测两次中断都是退出码 0 但没产图谱，text 模式下只留半句话。把
        num_turns / stop_reason / terminal_reason / total_cost_usd 打出来，
        中断原因才不是黑盒。
        """
        try:
            d = json.loads(stdout)
        except (json.JSONDecodeError, TypeError):
            logger.warning("UAAdapter: 会话结果非 JSON，无法解析停止原因")
            return

        logger.info(
            "UAAdapter: 会话结束 subtype=%s stop_reason=%s terminal_reason=%s "
            "num_turns=%s cost=$%.2f",
            d.get('subtype'), d.get('stop_reason'), d.get('terminal_reason'),
            d.get('num_turns'), d.get('total_cost_usd') or 0.0,
        )
        if d.get('is_error'):
            logger.warning("UAAdapter: 会话报错 api_error_status=%s",
                           d.get('api_error_status'))
        result = (d.get('result') or '')[-500:]
        if result:
            logger.info("UAAdapter: 会话最终回复尾部: %s", result)

    def _detect_resume_state(
        self, repo_path: str
    ) -> Optional[tuple]:
        """
        检测是否存在一次被中断的分析，可以续跑。

        条件：batches.json 存在，且已落盘的 batch 数在 (0, total) 之间。
        全都没跑 → 走完整流程；全跑完了 → 说明卡在 Phase 2 之后的阶段，
        此时也走完整流程（缺失清单为空，续跑 prompt 无意义）。

        Returns:
            (total, done_count, missing_indices) 或 None
        """
        import glob
        import re

        for d in self._candidate_dirs(repo_path):
            batches_path = os.path.join(d, 'intermediate', 'batches.json')
            if not os.path.isfile(batches_path):
                continue
            try:
                with open(batches_path, 'r', encoding='utf-8') as f:
                    raw = json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                logger.warning("UAAdapter: 读取 %s 失败: %s", batches_path, e)
                continue

            batches = raw if isinstance(raw, list) else raw.get('batches') or []
            total = len(batches)
            if total == 0:
                continue

            done = set()
            pattern = os.path.join(d, 'intermediate', 'batch-*.json')
            for f in glob.glob(pattern):
                m = re.match(r'batch-(\d+)', os.path.basename(f))
                if m:
                    done.add(int(m.group(1)))

            missing = sorted(set(range(1, total + 1)) - done)
            if not missing or not done:
                return None
            return (total, len(done), missing)

        return None

    def _find_existing_graph(self, repo_path: str) -> Optional[str]:
        """找现成的知识图谱，找不到返回 None。"""
        for d in self._candidate_dirs(repo_path):
            p = os.path.join(d, KNOWLEDGE_GRAPH_FILENAME)
            if os.path.isfile(p):
                return p
        return None

    def _candidate_dirs(self, repo_path: str) -> List[str]:
        if self.data_dir:
            return [self.data_dir]
        return [os.path.join(repo_path, d) for d in UA_DIR_CANDIDATES]

    def _staleness_reason(self, repo_path: str, graph_path: str) -> Optional[str]:
        """
        判断产物是否过期。返回原因字符串，新鲜则返回 None。

        依据 meta.json 的 gitCommitHash 与仓库当前 HEAD 比对。取不到任何一侧时
        不判过期（避免非 git 目录被误判），但会记 warning。
        """
        if not self.require_fresh:
            return None

        meta_path = os.path.join(os.path.dirname(graph_path), META_FILENAME)
        if not os.path.isfile(meta_path):
            logger.warning("UAAdapter: 无 %s，无法判断产物新鲜度", META_FILENAME)
            return None
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("UAAdapter: 读取 %s 失败: %s", meta_path, e)
            return None

        analyzed = meta.get('gitCommitHash')
        head = self._git_head(repo_path)
        if not analyzed or not head:
            logger.warning("UAAdapter: commit 信息不全（产物=%s HEAD=%s），跳过新鲜度判断",
                           analyzed, head)
            return None

        if analyzed != head:
            return (f"产物基于 commit {analyzed[:8]}，仓库当前 HEAD 为 {head[:8]}"
                    f"（analyzedFiles={meta.get('analyzedFiles')}）")
        return None

    @staticmethod
    def _git_head(repo_path: str) -> Optional[str]:
        try:
            out = subprocess.run(
                ['git', 'rev-parse', 'HEAD'], cwd=repo_path,
                capture_output=True, text=True, timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        return out.stdout.strip() if out.returncode == 0 else None

    @staticmethod
    def _tail(path: str, limit: int = 2000) -> str:
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                return f.read()[-limit:]
        except OSError:
            return '（日志不可读）'

    # ───────────────────────── 内部：路径归一化 ─────────────────────────

    @staticmethod
    def _normalize_page_paths(pages: List[Dict], repo_path: str) -> None:
        """
        把页面 path 统一成相对于仓库根的相对路径（原地修改）。

        UA 的节点 filePath 大多是相对路径，但有一部分是绝对路径（实测 2154 页里
        33 页），且 macOS 上 /tmp 是 /private/tmp 的符号链接，绝对路径会以
        /private/tmp/... 出现而仓库路径是 /tmp/...。两者字面不等，导致下游按路径
        匹配时把这些文件判成 missing —— 实测 core 因此假缺失 3 个文件并触发阻塞。

        这是确定性的路径换算，必须在这里做完，不能留给下游 subagent 靠字面
        相似度去猜（猜的结果是错的：它会把 other/Ascend/Ascend-CI/.../Chart.yaml
        匹配到 projects/vllm-project/.../Chart.yaml 这种同名不同源的文件）。
        """
        roots = {os.path.abspath(repo_path), os.path.realpath(repo_path)}
        converted = 0
        unresolved = []

        for page in pages:
            raw = page.get("path") or ""
            if not raw or not os.path.isabs(raw):
                continue

            real = os.path.realpath(raw)
            for root in roots:
                if real == root:
                    continue
                prefix = root.rstrip(os.sep) + os.sep
                if real.startswith(prefix):
                    page["path"] = real[len(prefix):].replace(os.sep, "/")
                    converted += 1
                    break
            else:
                unresolved.append(raw)

        if converted:
            logger.info("UAAdapter: 已将 %d 个绝对路径归一化为仓库相对路径", converted)
        if unresolved:
            # 不静默丢弃：这些路径指向仓库之外，下游需要知道
            logger.warning(
                "UAAdapter: %d 个页面路径不在仓库内，保持原样：%s",
                len(unresolved), unresolved[:3],
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
