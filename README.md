# autoScript

自动化部署的 CrewAI 百集短剧改编流水线。该项目提供一个可执行的脚本，将原著小说与风格模版输入后，由多智能体协作完成蓝图设计、剧本撰写、字数校验、格式整理、合并与分析总结。

## 系统亮点

- **LangGraph 状态机**：通过 `StateGraph` 将 Human Input、Planner、Retrieval、Writer、Validator、Reviewer、Deliver 等节点连接成可回溯的状态机，天然支持条件路由与 retry 统计。
- **双重 RAG**：`DualRAGIndex` 同时维护内容与风格两个向量空间。Writer 节点每次写作前都会并行检索原著场景与风格样本，实现“情节+风格”双重对齐。
- **叙事感知分块**：`SceneSplitter` 依据时间/地点/角色线索自动划分场景，避免粗暴的固定字符切片带来的剧情断裂。
- **确定性 Validator**：字数、标点、格式、动作情绪、审查底线全部使用 Python 代码校验，LLM 只负责创意输出。
- **辅导式重写循环**：Validator 失败时自动进入 Reviewer 节点，将客观错误翻译成可执行的改写建议，最多三次自动返工后再升级人工。


## 安装依赖

```bash
pip install -r requirements.txt
```

> 说明：`transformers` 仅在需要动作情绪检测使用大模型时才会自动加载，未安装时系统会回退到关键字规则。


## 输入准备

运行脚本前需要准备三类输入文件：

1. **宏观蓝图**（JSON）：包含剧名、分集概要、RAG 检索关键词等结构化信息，示例：

   ```json
   {
     "title": "炼气练成了执法官",
     "outline": "第一幕讲述主角获得金手指……",
     "episodes": [
       {
         "episode_number": 1,
         "title": "系统降临",
         "summary": "主角在出租屋觉醒系统，遭遇房东催租",
         "rag_query": "觉醒系统 房东 催租",
         "style_query": "高压对峙 场景"
       }
     ]
   }
   ```

2. **风格语料**（文本）：例如《神仙vx群》成片剧本，可直接将 `.docx` 转换为纯文本。
3. **原著小说**（文本）：长篇原著完整内容。


## 命令行用法

```bash
python -m autoScript blueprint.json style_corpus.txt novel.txt \
    --output-dir ./outputs \
    --max-retries 3 \
    --min-scene-chars 300 \
    --max-scene-chars 3200
```

执行后，输出目录将包含：

- `episode_001.md` 等：Validator 通过的剧集剧本。
- `workflow_summary.json`：记录产出文件、重写次数、是否需要人工介入等信息。

如需接入真实 LLM，可在 `PlannerAgent` / `WriterAgent` / `ReviewerAgent` 中替换为 API 调用，LangGraph 状态机与 Validator 逻辑无需改动。
