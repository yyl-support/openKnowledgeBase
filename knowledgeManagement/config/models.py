from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class IssueTrackingConfig(BaseModel):
    """Issue 跟踪配置"""
    backlog_repo: str = Field(
        default="opensourceways/backlog",
        description="Issue 所在仓库"
    )
    search_query: str = Field(
        ...,
        description="搜索条件，如 'forum-reply-robot state:closed'"
    )
    poll_interval: float = Field(
        default=3.5,
        description="轮询间隔（天），0.5周 = 3.5天"
    )


class UpdatePolicyConfig(BaseModel):
    """更新策略配置"""
    mode: Literal["auto", "manual"] = "auto"
    trigger: Literal["issue_polling", "manual"] = "issue_polling"
    incremental: bool = True
    full_update_interval: int = Field(
        default=7,
        description="强制全量更新的间隔（天）"
    )


class ProjectMetadata(BaseModel):
    """项目元数据（运行时更新）"""
    last_issue_number: Optional[int] = None
    last_update_time: Optional[datetime] = None
    last_update_mode: Optional[Literal["full", "incremental"]] = None
    total_updates: int = 0
    total_cost_usd: float = 0.0


class ProjectConfig(BaseModel):
    """单个项目配置"""
    repo_path: str
    description: str
    owner: str

    # Issue 跟踪
    issue_tracking: IssueTrackingConfig

    # 知识提取
    adapter: Literal["ua", "mk", "zread"]
    ua_profile: Optional[str] = "deepseek"
    output_types: List[str]

    # 更新策略
    update_policy: UpdatePolicyConfig

    # 优先级
    priority: Literal["high", "medium", "low"] = "medium"

    # 元数据
    metadata: ProjectMetadata = Field(default_factory=ProjectMetadata)


class GlobalConfig(BaseModel):
    """全局配置"""
    # 注意：当前 orchestrator.schedule_all_projects() 是串行执行，此配置尚未生效。
    # 项目数少时串行足够；如需并发，需在 orchestrator 中引入线程池并读取该值。
    max_concurrent_updates: int = 3

    github: dict = {
        "token_env": "GH_TOKEN",
        "cli_path": "gh"
    }

    embeddings: dict = {
        "provider": "openai",
        "model": "text-embedding-3-small"
    }

    storage: dict = {
        "base_dir": "/Users/gorden/huawei/code/openKnowledgeBase",
        "knowledge_dir": "knowledgeBase",
        "source_dir": "codeSource",
        "vector_dir": "vectordb",
        "metadata_db": "metadata.db"
    }

    notifications: dict = {
        "enabled": True,
        "slack_webhook": None
    }

    # 模型单价表，供 config/pricing.calc_cost() 读取。
    # 单价缺失时成本记 0 并打 warning（见 pricing.py），不静默放过。
    pricing: dict = {}


class SchedulerDaemonConfig(BaseModel):
    """调度器守护进程配置"""
    pid_file: str = "run/scheduler.pid"
    log_dir: str = "logs"


class SchedulerConfig(BaseModel):
    """调度器配置"""
    enabled: bool = True
    polling_interval_days: float = 3.5
    max_retries: int = 3
    retry_delay_seconds: int = 300
    daemon: SchedulerDaemonConfig = Field(default_factory=SchedulerDaemonConfig)


class SystemConfig(BaseModel):
    """系统完整配置"""
    projects: dict[str, ProjectConfig]
    global_config: GlobalConfig = Field(alias="global")
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
