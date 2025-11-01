"""Assemble the CrewAI workflow for the adaptation pipeline."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from crewai import Crew, Process

from .agents import (
    create_analysis_agent,
    create_blueprint_agent,
    create_compiler_agent,
    create_formatter_agent,
    create_scriptwriter_agent,
    create_wordcount_agent,
)
from .tasks import (
    create_analysis_task,
    create_blueprint_task,
    create_compiler_task,
    create_formatting_task,
    create_scriptwriting_task,
    create_wordcount_task,
)
from .tools.word_count_tool import EpisodeWordCountTool


@dataclass
class CrewOutputPaths:
    """Container for all intermediate and final output file paths."""

    blueprint: Path
    screenplay: Path
    qa_report: Path
    formatted_screenplay: Path
    compiled_script: Path
    analysis: Path
    final_with_analysis: Path

    @classmethod
    def from_output_dir(cls, output_dir: Path) -> "CrewOutputPaths":
        return cls(
            blueprint=output_dir / "01_blueprint.md",
            screenplay=output_dir / "02_screenplay_raw.md",
            qa_report=output_dir / "03_wordcount_report.md",
            formatted_screenplay=output_dir / "04_screenplay_formatted.md",
            compiled_script=output_dir / "05_script_compiled.md",
            analysis=output_dir / "06_script_analysis.md",
            final_with_analysis=output_dir / "07_final_script_with_analysis.md",
        )


def build_crew(*, style_template: str, novel_text: str, output_dir: Path) -> Crew:
    """Create the Crew instance wired with all agents and tasks."""
    output_paths = CrewOutputPaths.from_output_dir(output_dir)
    wordcount_tool = EpisodeWordCountTool()

    blueprint_agent = create_blueprint_agent()
    scriptwriter_agent = create_scriptwriter_agent()
    qa_agent = create_wordcount_agent(wordcount_tool)
    formatter_agent = create_formatter_agent()
    compiler_agent = create_compiler_agent()
    analysis_agent = create_analysis_agent()

    blueprint_task = create_blueprint_task(
        blueprint_agent,
        style_template=style_template,
        novel_text=novel_text,
        output_file=output_paths.blueprint,
    )
    screenplay_task = create_scriptwriting_task(
        scriptwriter_agent,
        blueprint_task=blueprint_task,
        style_template=style_template,
        novel_text=novel_text,
        output_file=output_paths.screenplay,
    )
    wordcount_task = create_wordcount_task(
        qa_agent,
        screenplay_task=screenplay_task,
        output_file=output_paths.qa_report,
    )
    formatting_task = create_formatting_task(
        formatter_agent,
        screenplay_task=screenplay_task,
        output_file=output_paths.formatted_screenplay,
    )
    compiler_task = create_compiler_task(
        compiler_agent,
        blueprint_task=blueprint_task,
        formatted_task=formatting_task,
        output_file=output_paths.compiled_script,
    )
    analysis_task = create_analysis_task(
        analysis_agent,
        compiled_task=compiler_task,
        output_file=output_paths.analysis,
    )

    tasks = [
        blueprint_task,
        screenplay_task,
        wordcount_task,
        formatting_task,
        compiler_task,
        analysis_task,
    ]
    agents = [
        blueprint_agent,
        scriptwriter_agent,
        qa_agent,
        formatter_agent,
        compiler_agent,
        analysis_agent,
    ]

    return Crew(
        agents=agents,
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )


def build_output_paths(output_dir: Path) -> CrewOutputPaths:
    """Expose output path calculation for CLI tooling."""
    return CrewOutputPaths.from_output_dir(output_dir)


__all__ = ["build_crew", "build_output_paths", "CrewOutputPaths"]
