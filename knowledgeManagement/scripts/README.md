# Scripts 工具集

本目录包含知识工程项目的核心自动化脚本，用于消除重复性的手动验证工作。

---

## 核心脚本

### 1. `test_phase.sh` - Phase 测试执行

**用途**：自动运行指定 Phase 的所有测试并统计结果，替代手动执行 pytest 和统计输出。

**用法**：

```bash
./scripts/test_phase.sh <phase_number>
```

**示例**：

```bash
# 运行 Phase 3 的所有测试
./scripts/test_phase.sh 3
```

**输出示例**：

```
正在运行 Phase 3 测试...
========================================
Phase 3 测试结果
========================================
通过: 19
失败: 0
跳过: 0
总计: 19
========================================
```

**退出码**：
- `0`: 所有测试通过
- `1`: 有测试失败或目录/文件不存在

---

### 2. `check_deps.py` - 依赖检查

**用途**：检查指定 Phase 所需的 Python 依赖是否已安装，替代手动 `pip list | grep` 逐个查询。

**用法**：

```bash
python scripts/check_deps.py --phase <phase_number>
```

**示例**：

```bash
# 检查 Phase 4 的依赖
python scripts/check_deps.py --phase 4
```

**输出示例（所有依赖已安装）**：

```
========================================
Phase 4 依赖检查
========================================
✅ apscheduler (已安装: 3.10.4)
✅ python-daemon (已安装: 2.3.2)

所有依赖已安装
========================================
```

**输出示例（有缺失依赖）**：

```
========================================
Phase 4 依赖检查
========================================
✅ apscheduler (已安装: 3.10.4)
❌ python-daemon (未安装)

安装缺失依赖：
  pip3 install python-daemon --user
========================================
```

**退出码**：
- `0`: 所有依赖已安装
- `1`: 有依赖缺失
- `2`: Phase 编号无效

**依赖清单**：
- **Phase 1**: `pyyaml`, `pydantic`
- **Phase 2**: `PyGithub`, `requests`
- **Phase 3**: `langchain`, `langchain-community`, `chromadb`, `openai`
- **Phase 4**: `apscheduler`, `python-daemon`
- **Phase 5**: 无新增依赖

---

### 3. `verify_no_fake_success.py` - 假成功检查

**用途**：验证向量库是否真实写入数据，而非只是返回 `success: True`。这是本项目反复踩的坑，脚本自动化检查三个关键指标。

**用法**：

```bash
python scripts/verify_no_fake_success.py --project <project_name> [--base-dir <vectordb_dir>]
```

**示例**：

```bash
# 检查 forum-reply-robot 项目的向量库
python scripts/verify_no_fake_success.py --project forum-reply-robot

# 指定向量库根目录
python scripts/verify_no_fake_success.py --project forum-reply-robot --base-dir /path/to/vectordb
```

**输出示例（检查通过）**：

```
========================================
假成功检查: forum-reply-robot
========================================
✅ 向量库目录存在: vectordb/forum-reply-robot/
✅ 向量库非空: chroma.sqlite3 (12.3 KB)
✅ 相似度检索返回结果: 3 个
✅ 文档内容非空: page_content 平均长度 245 字符
========================================
结论: 未发现假成功
```

**输出示例（检查失败）**：

```
========================================
假成功检查: forum-reply-robot
========================================
✅ 向量库目录存在: vectordb/forum-reply-robot/
✅ 向量库非空: chroma.sqlite3 (0.5 KB)
❌ 相似度检索失败: 相似度搜索返回空结果
========================================
结论: 检查失败（相似度搜索无结果）
```

**检查项**：

1. **向量库目录存在且非空**：检查 `vectordb/{project}/` 下的 `chroma.sqlite3` 文件是否存在且大小 > 0
2. **相似度搜索返回结果**：执行 `similarity_search("test", k=5)` 并验证返回结果数 > 0
3. **文档内容非空**：检查返回文档的 `page_content` 平均长度 > 50 字符（排除空串占位）

**退出码**：
- `0`: 未发现假成功，向量库正常
- `1`: 检查失败，发现假成功或向量库异常
- `2`: 无法检查（缺少 `SILICONFLOW_API_KEY` 或向量库不存在）

**前置条件**：

脚本需要访问 SiliconFlow API 来初始化向量存储，请确保设置环境变量：

```bash
export SILICONFLOW_API_KEY=<your_api_key>
```

---

## 使用场景

### 场景 1：完成某个 Phase 后的快速验证

```bash
# 1. 检查依赖
python scripts/check_deps.py --phase 3

# 2. 运行测试
./scripts/test_phase.sh 3

# 3. 验证向量库（如果该 Phase 涉及向量存储）
python scripts/verify_no_fake_success.py --project forum-reply-robot
```

### 场景 2：排查"测试通过但功能不工作"的问题

```bash
# 先确认测试确实通过了
./scripts/test_phase.sh 3

# 再检查是否是假成功
python scripts/verify_no_fake_success.py --project forum-reply-robot
```

### 场景 3：切换环境或机器后的环境验证

```bash
# 逐个 Phase 检查依赖
for phase in {1..5}; do
    echo "检查 Phase $phase..."
    python scripts/check_deps.py --phase $phase
done
```

---

## 开发说明

### 添加新的 Phase 依赖

编辑 `check_deps.py` 中的 `PHASE_DEPENDENCIES` 字典：

```python
PHASE_DEPENDENCIES = {
    1: ["pyyaml", "pydantic"],
    2: ["PyGithub", "requests"],
    # 添加新 Phase
    6: ["new-package1", "new-package2"],
}
```

### 扩展假成功检查项

在 `verify_no_fake_success.py` 的 `main()` 函数中添加新的检查逻辑，遵循现有模式：

```python
# 检查4: 新检查项
passed4, msg4 = check_something_new(project, base_dir)
if passed4:
    print(f"✅ 新检查项: {msg4}")
else:
    print(f"❌ 新检查项失败: {msg4}")
    return 1
```

---

## 故障排查

### `test_phase.sh` 报错 "pytest: command not found"

确保 pytest 已安装：

```bash
pip3 install pytest --user
```

### `check_deps.py` 误报包未安装

某些包的 PyPI 名称与 import 名称不同（如 `PyGithub` vs `github`）。脚本使用 `importlib.metadata.version()` 检查 PyPI 包名，如果包已安装但检查失败，请检查包名是否正确。

### `verify_no_fake_success.py` 退出码 2

检查 `SILICONFLOW_API_KEY` 是否已设置：

```bash
echo $SILICONFLOW_API_KEY
```

如果未设置，执行：

```bash
export SILICONFLOW_API_KEY=<your_key>
```

---

## 版本历史

- **2026-08-27**: 初始版本，包含 3 个核心脚本
  - `test_phase.sh`: Phase 测试自动化
  - `check_deps.py`: 依赖检查
  - `verify_no_fake_success.py`: 假成功检查
