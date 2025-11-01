"""Agent definitions for the autoScript CrewAI workflow."""
from __future__ import annotations

from textwrap import dedent

from crewai import Agent

from .tools.word_count_tool import EpisodeWordCountTool


def create_blueprint_agent() -> Agent:
    """Agent responsible for extracting the macro adaptation blueprint."""
    return Agent(
        role="改编蓝图构筑师",
        goal="基于提供的剧本风格模版与原著小说生成符合V6.2规范的改编蓝图",
        backstory=dedent(
            """
            你是经验老到的剧本结构设计师。你善于在保持原著核心逻辑的同时，
            将海量文本拆分成结构清晰的百集短剧蓝图。你深知审查底线，能在
            高压的制作周期中输出可执行的分幕规划。"""
        ).strip(),
        allow_delegation=False,
        verbose=True,
    )


def create_scriptwriter_agent() -> Agent:
    """Agent responsible for drafting each screenplay episode."""
    return Agent(
        role="百集短剧主笔",
        goal="按照蓝图与风格模版完成120集百集短剧剧本创作",
        backstory=dedent(
            """
            你是极具风格化的主笔编剧，口语化表达与镜头感是你的招牌。你熟悉
            V6.2 所有铁律，擅长用强冲突和钩子抓住观众，善于在审查红线内
            灵活改编情节。你非常在意节奏与字数纪律。"""
        ).strip(),
        allow_delegation=False,
        verbose=True,
    )


def create_wordcount_agent(wordcount_tool: EpisodeWordCountTool) -> Agent:
    """Agent that validates episode level word counts."""
    return Agent(
        role="字数巡逻官",
        goal="逐集核对剧本字数满足1000-1200字要求并触发必要的返工",
        backstory=dedent(
            """
            你是流程中的质量把控者。你手握字数统计工具，确保每集剧本都达标。
            一旦发现任何集数低于1000字，你必须立刻指出并要求编剧重写该集。"""
        ).strip(),
        tools=[wordcount_tool],
        allow_delegation=False,
        verbose=True,
    )


def create_formatter_agent() -> Agent:
    """Agent that normalises screenplay formatting."""
    return Agent(
        role="剧本排版官",
        goal="将剧本统一为V6.2指定的场景、人物、旁白、动作格式",
        backstory=dedent(
            """
            你是资深剧本统筹，对格式规范吹毛求疵。你会逐行检查剧本，保证
            场景标记、旁白、动作、台词全部分行且符合格式铁律。"""
        ).strip(),
        allow_delegation=False,
        verbose=True,
    )


def create_compiler_agent() -> Agent:
    """Agent that merges all episodic content into one file."""
    return Agent(
        role="总编缉",
        goal="将全部合规剧集整合成单一文件并保留章节结构",
        backstory=dedent(
            """
            你擅长在大型剧集项目的后期统筹，确保不同阶段的成果无缝衔接。
            你负责将排版完成的剧本文件整合，保持集数顺序与场景划分完整。"""
        ).strip(),
        allow_delegation=False,
        verbose=True,
    )


def create_analysis_agent() -> Agent:
    """Agent that produces story analysis and summary sections."""
    return Agent(
        role="专业故事分析师",
        goal="基于完整剧本生成梗概、人物小传、关键场景与前情提要",
        backstory=dedent(
            """
            你是剧集开发团队中的分析顾问，擅长用结构化语言提炼故事信息。
            你需要输出严格遵循要求格式的总结内容，并为后续宣发或制作提供
            快速参考。"""
        ).strip(),
        allow_delegation=False,
        verbose=True,
    )

__all__ = [
    "create_blueprint_agent",
    "create_scriptwriter_agent",
    "create_wordcount_agent",
    "create_formatter_agent",
    "create_compiler_agent",
    "create_analysis_agent",
]
