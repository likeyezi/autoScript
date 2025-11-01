"""Task definitions for the autoScript CrewAI workflow."""
from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from crewai import Agent, Task


def create_blueprint_task(
    agent: Agent,
    *,
    style_template: str,
    novel_preview: str,
    chunk_instructions: str,
    output_file: Path,
) -> Task:
    """Create the blueprint generation task."""
    return Task(
        agent=agent,
        description=dedent(
            f"""
            【任务目标】根据以下剧本风格模版与原著小说，产出满足 V6.2 规范的
            【改编蓝图】。你必须在保持原著故事因果链完整性的前提下，输出
            5-8 幕的宏观结构规划。

            【剧本风格模版】
            {style_template}

            【原著获取方式】
            {chunk_instructions}

            【原著预览片段】
            {novel_preview}
            """
        ).strip(),
        expected_output=dedent(
            """
            需完整覆盖：核心故事线提炼、10-15个关键情节节点、以及分幕结构。
            输出采用【改编蓝图】模板，标明每幕对应的集数范围与关键事件。"""
        ).strip(),
        output_file=str(output_file),
    )


def create_scriptwriting_task(
    agent: Agent,
    *,
    blueprint_task: Task,
    style_template: str,
    novel_preview: str,
    chunk_instructions: str,
    output_file: Path,
) -> Task:
    """Create the screenplay generation task."""
    return Task(
        agent=agent,
        description=dedent(
            f"""
            【任务目标】在保证原著逻辑与蓝图一致的前提下，使用风格模版完成
            120 集短剧剧本创作。每集 1000-1200 字，包含 2-3 个场景，且每集末
            必须留下强钩子。

            【剧本风格模版】
            {style_template}

            【原著获取方式】
            {chunk_instructions}

            【原著预览片段】
            {novel_preview}
            """
        ).strip(),
        expected_output=dedent(
            """
            输出【剧本正文】，严格遵循提供的分集、场景、旁白、对话、动作、OS
            格式要求，并保持 V6.2 所有铁律。"""
        ).strip(),
        context=[blueprint_task],
        output_file=str(output_file),
    )


def create_wordcount_task(agent: Agent, *, screenplay_task: Task, output_file: Path) -> Task:
    """Create the quality assurance word-count task."""
    return Task(
        agent=agent,
        description=dedent(
            """
            使用 EpisodeWordCountTool 对上一阶段剧本逐集统计字数。若任何一集
            字数低于1000或高于1200，必须明确指出集数并要求编剧重新交付该集。
            给出字数统计表以及最终判定。"""
        ).strip(),
        expected_output="Markdown 表格列出集数与字数，并给出是否全部达标的结论。",
        context=[screenplay_task],
        output_file=str(output_file),
    )


def create_formatting_task(agent: Agent, *, screenplay_task: Task, output_file: Path) -> Task:
    """Create the formatting normalisation task."""
    return Task(
        agent=agent,
        description=dedent(
            """
            在确保不破坏剧情与字数的前提下，将剧本整理为标准格式：
            1. 场景行满足 [集数-场景编号] 地点 - 内/外 - 日/夜。
            2. 每行仅包含一种元素（旁白、动作、对话、OS）。
            3. 确保旁白大量存在且与 OS 区分。
            输出的剧本必须完整覆盖所有集数。
            """
        ).strip(),
        expected_output="输出格式化后的完整剧本文本，不得遗漏任何集。",
        context=[screenplay_task],
        output_file=str(output_file),
    )


def create_compiler_task(agent: Agent, *, blueprint_task: Task, formatted_task: Task, output_file: Path) -> Task:
    """Create the compilation task that merges blueprint and screenplay."""
    return Task(
        agent=agent,
        description=dedent(
            """
            将【改编蓝图】与格式化剧本合并成单一文档。先留蓝图供参考，随后
            依次附上 120 集正文。保留所有场景编号与分集标题，确保章节顺序正确。"""
        ).strip(),
        expected_output="合并后的完整剧本文档，蓝图在前，剧本在后。",
        context=[blueprint_task, formatted_task],
        output_file=str(output_file),
    )


def create_analysis_task(agent: Agent, *, compiled_task: Task, output_file: Path) -> Task:
    """Create the story analysis task."""
    return Task(
        agent=agent,
        description=dedent(
            """
            阅读完整剧本后，输出指定结构的分析内容：
            一、故事梗概（300-500字）；
            二、人物小传列表（使用 Markdown 表格，按重要性排序）；
            三、关键场景列表（按时间顺序，列出场景名、时间、场景描述）；
            四、前情提要 / 故事背景。
            所有信息必须基于剧本内容，不得添加外部设定。
            """
        ).strip(),
        expected_output="严格按指令格式输出的四部分结构化文本。",
        context=[compiled_task],
        output_file=str(output_file),
    )

__all__ = [
    "create_blueprint_task",
    "create_scriptwriting_task",
    "create_wordcount_task",
    "create_formatting_task",
    "create_compiler_task",
    "create_analysis_task",
]
