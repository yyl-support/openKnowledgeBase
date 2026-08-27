# Phase 3: 增量更新层（RAG 系统）

## 概述

Phase 3 实现了基于 RAG（Retrieval-Augmented Generation）的知识增量更新能力，包括：

- **UpdateDecisionChain**: 基于 LLM 智能决策全量/增量更新
- **VectorStore**: 项目隔离的向量存储（基于 ChromaDB）
- **KnowledgeUpdateChain**: 文档分块、向量化、增量更新
- **SectionRegenerationChain**: 基于 RAG 重新生成受影响的文档章节

## 目录结构

```
update/
├── __init__.py                # 模块导出
├── decision_chain.py          # UpdateDecisionChain（LLM 决策）
├── vector_store.py            # VectorStore 封装（项目隔离）
├── update_chain.py            # KnowledgeUpdateChain（增量更新）
├── regeneration_chain.py      # SectionRegenerationChain（章节生成）
└── README.md                  # 本文档
```

## 核心组件

### 1. UpdateDecisionChain

**功能**: 基于 LLM 分析 Issue 变更情况，决定使用全量更新还是增量更新。

**决策规则**:
- 全量更新：Issue 标签包含 `need_design` 或 `need_security`，需求文档 > 500 行，变更文件 >= 30%，距上次更新 > 7 天
- 增量更新：以上条件都不满足

**降级方案**: 如果 LLM 不可用，使用规则引擎决策。

**使用示例**:
```python
from update.decision_chain import UpdateDecisionChain

chain = UpdateDecisionChain()
result = chain.decide(knowledge_package, days_since_last_update=3.5)

print(result["decision"])  # "full" 或 "incremental"
print(result["reason"])    # 决策理由
```

### 2. VectorStore

**功能**: 基于 ChromaDB 的向量存储封装，提供项目隔离能力。

**特性**:
- 使用 SiliconFlow Qwen3-Embedding-8B 向量化模型
- 每个项目独立的 collection 和存储目录
- 支持增量更新（删除旧文档 + 添加新文档）

**存储路径**: `vectordb/{project_name}/`

**使用示例**:
```python
from update.vector_store import VectorStore

store = VectorStore(project_name="forum-reply-robot")

# 添加文档
store.add_documents(documents)

# 删除旧版本
store.delete_by_source("src/main.py")

# 相似度搜索
results = store.similarity_search("核心流程", k=5)
```

### 3. KnowledgeUpdateChain

**功能**: 处理文档分块、向量化、增量更新向量库。

**核心流程**:
1. 处理需求分析文档（分块、向量化）
2. 处理代码变更（删除旧版本 + 添加新版本）
3. 更新向量库

**使用示例**:
```python
from update.update_chain import KnowledgeUpdateChain

chain = KnowledgeUpdateChain(project_name="forum-reply-robot")

# 增量更新
result = chain.update_from_issue(knowledge_package)

# 全量向量化
result = chain.vectorize_all(knowledge_base_dir)
```

### 4. SectionRegenerationChain

**功能**: 基于 RAG 检索相关知识，使用 LLM 重新生成受影响的文档章节。

**章节映射规则**:
- `main.py` 变更 → `overview.md` 的 "核心流程"
- `requirements.txt` 变更 → `techstack.md` 的 "依赖管理"
- `.github/workflows/` 变更 → `standards.md` 的 "CI/CD"
- `Dockerfile` 变更 → `techstack.md` 的 "容器化"

**使用示例**:
```python
from update.regeneration_chain import SectionRegenerationChain

chain = SectionRegenerationChain(project_name="forum-reply-robot")

# 识别受影响的章节
affected = chain.identify_affected_sections(knowledge_package)

# 重新生成单个章节
new_content = chain.regenerate_section(
    document_name="overview.md",
    section_name="核心流程",
    knowledge_package=knowledge_package
)

# 重新生成所有受影响的章节
result = chain.regenerate_all_affected(
    knowledge_package,
    knowledge_base_dir
)
```

## LLM 配置

### Embeddings（SiliconFlow）

```python
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(
    model="Qwen/Qwen3-Embedding-8B",
    openai_api_key=os.getenv("SILICONFLOW_API_KEY"),
    openai_api_base="https://api.siliconflow.cn/v1"
)
```

### LLM（火山 ARK）

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="minimax-m3",
    openai_api_key=os.getenv("ARK_API_KEY"),
    openai_api_base="https://ark.cn-beijing.volces.com/api/v3"
)
```

**注意**: 需要设置环境变量 `ARK_API_KEY`

## 项目隔离

所有组件都严格按项目隔离：

- **VectorStore**: 每个项目独立的 `collection_name` 和存储目录
- **元数据**: 所有文档都带有 `project` 字段
- **搜索过滤**: 自动过滤只返回当前项目的文档

## 与 Orchestrator 集成

修改 `orchestration/orchestrator.py`，在 `_execute_full_update` 后调用增量更新：

```python
from update.decision_chain import UpdateDecisionChain
from update.update_chain import KnowledgeUpdateChain
from update.regeneration_chain import SectionRegenerationChain

# 在 KnowledgeOrchestrator 中
self.decision_chain = UpdateDecisionChain()

def _execute_update(self, project_name, project, issue_number):
    # 1. 提取知识
    knowledge_package = self.issue_extractor.extract(...)
    
    # 2. 决策
    decision = self.decision_chain.decide(knowledge_package, days_since_last_update)
    
    if decision["decision"] == "full":
        # 全量更新（调用现有流水线）
        result = self._execute_full_update(...)
        
        # 全量向量化
        update_chain = KnowledgeUpdateChain(project_name)
        update_chain.vectorize_all(knowledge_base_dir)
    else:
        # 增量更新
        result = self._execute_incremental_update(...)
```

## 依赖安装

```bash
pip install langchain==0.1.0
pip install langchain-openai==0.0.5
pip install langchain-community==0.0.13
pip install chromadb==0.4.22
```

## 测试

测试文件位于 `tests/phase3/`:

```bash
# 测试决策链
python -m pytest tests/phase3/test_decision_chain.py

# 测试向量存储
python -m pytest tests/phase3/test_vector_store.py

# 测试增量更新
python -m pytest tests/phase3/test_update_chain.py

# 测试章节生成
python -m pytest tests/phase3/test_regeneration_chain.py
```

## 注意事项

1. **API Key 安全**: 
   - SiliconFlow API Key 已硬编码（测试用）
   - 火山 ARK API Key 必须通过环境变量设置

2. **错误处理**:
   - LLM 不可用时自动降级到规则引擎
   - 向量化失败不应阻止流程继续

3. **成本优化**:
   - 优先使用增量更新
   - 每 7 天强制全量更新（兜底）

4. **项目隔离**:
   - 绝不交叉污染不同项目的知识
   - 所有操作都带项目命名空间

## 未来优化

- [ ] 实现 Reranker（Qwen3-Reranker-8B）提高检索准确度
- [ ] 章节替换逻辑（目前只生成，未写回文档）
- [ ] 支持更多文档格式（除了 Markdown）
- [ ] 向量库性能优化（批量操作、缓存）
