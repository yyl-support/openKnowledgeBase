# Phase 4 设计方案：触发器层（Trigger Layer）

## 1. 目标

实现自动化定时调度，让系统无需人工干预即可周期性更新知识库。

## 2. 核心功能

### 2.1 定时调度器
- **周期性 Issue 轮询**：每 3.5 天自动检查新 Issue
- **可配置间隔**：支持自定义轮询频率
- **并发控制**：同一时刻只运行一个调度任务

### 2.2 后台服务
- **守护进程模式**：长期运行，不阻塞终端
- **优雅启停**：支持 start/stop/restart/status
- **PID 管理**：防止重复启动

### 2.3 日志与监控
- **完整日志记录**：每次调度的详细日志
- **按日期归档**：logs/scheduler_YYYYMMDD.log
- **错误追踪**：异常栈完整记录

### 2.4 错误处理
- **失败重试**：任务失败自动重试（最多 3 次）
- **降级运行**：单个项目失败不影响其他项目
- **告警通知**：关键错误可发送通知（预留接口）

---

## 3. 架构设计

```
triggers/
├── scheduler.py          # 调度器核心
├── daemon.py            # 守护进程管理
├── __init__.py
└── README.md

tests/phase4/
├── test_scheduler.py    # 调度器测试
└── test_daemon.py       # 守护进程测试

logs/
└── scheduler_YYYYMMDD.log

run/
└── scheduler.pid        # PID 文件
```

---

## 4. 模块设计

### 4.1 KnowledgeScheduler（调度器核心）

**职责**：
- 管理定时任务
- 调用 Orchestrator 执行调度
- 记录执行日志

**接口**：
```python
class KnowledgeScheduler:
    def __init__(self, config_path: str)
    def add_polling_job(self, days: float = 3.5) -> None
    def start(self) -> None  # 阻塞启动
    def shutdown(self) -> None
    def run_once(self) -> dict  # 立即执行一次（测试用）
```

**依赖**：
- APScheduler（定时任务）
- orchestration.Orchestrator（执行调度）

---

### 4.2 SchedulerDaemon（守护进程管理）

**职责**：
- 后台运行调度器
- PID 文件管理
- 进程生命周期控制

**接口**：
```python
class SchedulerDaemon:
    def __init__(self, config_path: str, pid_file: str)
    def start(self) -> None      # 启动守护进程
    def stop(self) -> None       # 停止守护进程
    def restart(self) -> None    # 重启
    def status(self) -> dict     # 查询状态
```

**依赖**：
- python-daemon（守护进程）
- KnowledgeScheduler

---

## 5. 技术选型

### 5.1 定时任务
**APScheduler**
- 优点：Python 原生、功能强大、支持多种触发器
- 配置：BlockingScheduler（守护进程模式）

### 5.2 守护进程
**python-daemon**
- 优点：标准实现、稳定可靠
- 配置：detach_process=True, working_directory=/path/to/project

### 5.3 日志
**logging 标准库**
- 文件日志：FileHandler（按日期）
- 控制台日志：StreamHandler（守护进程模式禁用）

---

## 6. 配置文件扩展

在 `config/projects.yaml` 中增加调度配置：

```yaml
# 调度器配置
scheduler:
  enabled: true
  polling_interval_days: 3.5
  max_retries: 3
  retry_delay_seconds: 300
  daemon:
    pid_file: "run/scheduler.pid"
    log_dir: "logs"
```

---

## 7. CLI 命令扩展

### 7.1 前台运行（测试）
```bash
python3 triggers/scheduler.py --config config/projects.yaml --interval 3.5
```

### 7.2 守护进程模式
```bash
python3 triggers/daemon_mgr.py start   # 启动
python3 triggers/daemon_mgr.py stop    # 停止
python3 triggers/daemon_mgr.py restart # 重启
python3 triggers/daemon_mgr.py status  # 状态
```

### 7.3 测试模式
```bash
python3 triggers/scheduler.py --run-once  # 立即执行一次
```

---

## 8. 测试用例

### 8.1 test_scheduler.py

```python
def test_scheduler_initialization()
    """测试调度器初始化"""

def test_add_polling_job()
    """测试添加轮询任务"""

def test_run_once()
    """测试立即执行一次"""

def test_job_execution_success()
    """测试任务执行成功"""

def test_job_execution_failure()
    """测试任务执行失败（重试机制）"""

def test_event_listeners()
    """测试事件监听器"""
```

### 8.2 test_daemon.py

```python
def test_daemon_start()
    """测试守护进程启动"""

def test_daemon_stop()
    """测试守护进程停止"""

def test_daemon_restart()
    """测试守护进程重启"""

def test_daemon_status()
    """测试守护进程状态查询"""

def test_pid_file_management()
    """测试 PID 文件管理"""

def test_duplicate_start_prevention()
    """测试防止重复启动"""
```

---

## 9. 实施步骤

### Step 1: 安装依赖
```bash
pip3 install apscheduler python-daemon --user
```

### Step 2: 实现 KnowledgeScheduler
- triggers/scheduler.py
- 包含日志、事件监听、错误处理

### Step 3: 实现 SchedulerDaemon
- triggers/daemon_mgr.py
- PID 管理、进程控制

### Step 4: 编写测试
- tests/phase4/test_scheduler.py
- tests/phase4/test_daemon.py

### Step 5: 运行测试验证
```bash
pytest tests/phase4/ -v
```

### Step 6: 端到端测试
```bash
# 测试立即执行
python3 triggers/scheduler.py --run-once

# 测试守护进程
python3 triggers/daemon_mgr.py start
python3 triggers/daemon_mgr.py status
python3 triggers/daemon_mgr.py stop
```

---

## 10. 风险与限制

### 10.1 风险
1. **长时间运行稳定性**：需要测试 7 天以上的连续运行
2. **资源占用**：守护进程可能占用内存
3. **时区问题**：APScheduler 默认使用系统时区

### 10.2 限制
1. **单机运行**：不支持分布式调度
2. **简单重试**：重试策略较简单（固定间隔）
3. **无 Web UI**：无法通过 Web 界面管理

### 10.3 缓解措施
1. 完整的日志记录
2. 守护进程自动重启机制
3. PID 文件防止重复启动

---

## 11. 后续优化方向

1. **Celery 集成**：支持分布式任务队列
2. **Web 管理界面**：可视化管理调度任务
3. **告警通知**：集成钉钉/企业微信/邮件通知
4. **动态调整间隔**：根据 Issue 活跃度动态调整轮询频率
5. **健康检查**：定期检查调度器状态

---

## 12. 预期成果

### 12.1 功能成果
- ✅ 自动定时调度（每 3.5 天）
- ✅ 守护进程后台运行
- ✅ 完整日志记录
- ✅ 失败重试机制

### 12.2 测试成果
- ✅ 单元测试覆盖 > 80%
- ✅ 端到端测试通过
- ✅ 长时间运行测试（可选）

### 12.3 文档成果
- ✅ 设计文档
- ✅ 使用文档
- ✅ 部署指南

---

## 13. 时间估算

- **设计方案**：0.5 天（已完成）
- **实现代码**：1 天
- **编写测试**：0.5 天
- **测试验证**：0.5 天

**总计**：2.5 天

---

**方案完成，等待审核！**
