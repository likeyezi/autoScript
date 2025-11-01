# autoScript

自动化部署的 CrewAI 百集短剧改编流水线。该项目提供一个可执行的脚本，将原著小说与风格模版输入后，由多智能体协作完成蓝图设计、剧本撰写、字数校验、格式整理、合并与分析总结。

## 功能特性

- **改编蓝图构筑师**：抽取核心故事线，拆分 5-8 幕的宏观结构。
- **百集短剧主笔**：依据风格模版生成 120 集剧本，每集 1000-1200 字，并保证强钩子。
- **字数巡逻官**：调用自定义 `EpisodeWordCountTool` 检查每集字数是否达标，提示返工。
- **剧本排版官**：输出符合 V6.2 剧本格式铁律的最终排版。
- **总编缉**：合并蓝图与剧本，形成统一文件。
- **专业故事分析师**：生成故事梗概、人物小传、关键场景与前情提要，并合并至剧本开头。

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用说明

```bash
python -m autoScript <风格模版路径> <原著小说路径> --output-dir ./outputs
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
