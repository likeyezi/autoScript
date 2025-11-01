# autoScript

自动化部署的 CrewAI 百集短剧改编流水线。该项目提供一个可执行的脚本，将原著小说与风格模版输入后，由多智能体协作完成蓝图设计、剧本撰写、字数校验、格式整理、合并与分析总结。

## 功能特性

- **改编蓝图构筑师**：抽取核心故事线，拆分 5-8 幕的宏观结构。
- **百集短剧主笔**：依据风格模版生成 120 集剧本，每集 1000-1200 字，并保证强钩子。
- **字数巡逻官**：调用自定义 `EpisodeWordCountTool` 检查每集字数是否达标，提示返工。
- **剧本排版官**：输出符合 V6.2 剧本格式铁律的最终排版。
- **总编缉**：合并蓝图与剧本，形成统一文件。
- **专业故事分析师**：生成故事梗概、人物小传、关键场景与前情提要，并合并至剧本开头。
- **NovelChunkTool**：将超长原著切分为可按需检索的片段，避免触发 413 输入过长错误，并支持关键词或区段查阅。

## 安装依赖

```bash
pip install -r requirements.txt
```

## 环境配置

在运行流水线前，请先完成大模型与密钥配置：

1. **配置 API Key**：流水线默认使用 OpenAI 兼容接口。请在终端中导出密钥，或在项目根目录创建 `.env` 文件。

   ```bash
   export OPENAI_API_KEY="sk-xxxxxxxx"
   ```

   - 若使用兼容的代理服务，可同时设置 `OPENAI_API_BASE_URL`。项目同样兼容已有的 `OPENAI_BASE_URL` 与 `OPENAI_API_BASE` 变量，三者任意其一生效即可。
   
   ```bash
   export OPENAI_API_BASE_URL="https://your-proxy.example.com/v1"
   ```

2. **选择模型**：CrewAI 会读取以下任一环境变量来决定调用的模型，按优先级从高到低：`MODEL` → `MODEL_NAME` → `OPENAI_MODEL_NAME`。

   ```bash
   export OPENAI_MODEL_NAME="gpt-4o-mini"
   ```

   - 也可以使用 `MODEL=provider/model-name` 的格式指定其他厂商（例如 `MODEL="openai/gpt-4.1"` 或 `MODEL="anthropic/claude-3.5-sonnet"`），只要对应的 API Key 已按 CrewAI 官方要求配置。
   - 更多供应商（如 Azure、Anthropic 等）的环境变量说明可参考 CrewAI 文档，配置方式与上面类似。

完成以上步骤后即可运行脚本。

### 大文本处理说明

当原著文本超过单次上下文限制时，流水线会自动启用 `NovelChunkTool`：

- 原著会按字符切分为多段（默认每段 3500 字，重叠 200 字），每个智能体可通过 `chunk:<编号>`、`range:<起始>-<结束>` 或 `search:<关键词>` 指令按需读取。
- 剧本任务描述中仅保留首段预览以及工具使用说明，避免一次性注入数百万 tokens 触发 413 错误。
- 可通过 CLI 参数 `--chunk-size` 与 `--chunk-overlap` 调整分段粒度，以适配不同模型的上下文窗口。

## 使用说明

```bash
python -m autoScript <风格模版路径> <原著小说路径> \
    --output-dir ./outputs \
    --chunk-size 3500 \
    --chunk-overlap 200
```

脚本会在输出目录内生成以下文件：

1. `01_blueprint.md`：改编蓝图。
2. `02_screenplay_raw.md`：主笔初稿。
3. `03_wordcount_report.md`：字数巡检结果。
4. `04_screenplay_formatted.md`：格式化后的剧本。
5. `05_script_compiled.md`：合并后的蓝图 + 剧本。
6. `06_script_analysis.md`：结构化分析报告。
7. `07_final_script_with_analysis.md`：将分析附加到剧本开头的最终交付文件。
8. `pipeline_summary.json`：执行摘要与文件索引。

运行 CrewAI 需要设置 `OPENAI_API_KEY` 或其他兼容的 LLM 提供商环境变量，具体请参考 CrewAI 官方文档。
