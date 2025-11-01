"""Command line interface for running the autoScript CrewAI pipeline."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from .crew import build_crew, build_output_paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the CrewAI adaptation pipeline.")
    parser.add_argument("style_template", type=Path, help="Path to the剧本风格模版文本文件")
    parser.add_argument("novel_text", type=Path, help="Path to the原著小说文本文件")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs"),
        help="Directory for all intermediate与最终输出文件",
    )
    return parser.parse_args()


def load_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"无法找到文件: {path}")
    return path.read_text(encoding="utf-8")


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def merge_analysis_with_script(*, analysis_path: Path, script_path: Path, output_path: Path) -> None:
    analysis = analysis_path.read_text(encoding="utf-8")
    script = script_path.read_text(encoding="utf-8")
    output_path.write_text(f"{analysis}\n\n{script}", encoding="utf-8")


def make_serialisable(value: Any) -> Any:
    try:
        json.dumps(value)
    except TypeError:
        if isinstance(value, dict):
            return {key: make_serialisable(val) for key, val in value.items()}
        if isinstance(value, list):
            return [make_serialisable(item) for item in value]
        return str(value)
    return value


def main() -> Dict[str, Any]:
    args = parse_args()
    style_template = load_text(args.style_template)
    novel_text = load_text(args.novel_text)
    ensure_directory(args.output_dir)

    crew = build_crew(
        style_template=style_template,
        novel_text=novel_text,
        output_dir=args.output_dir,
    )
    results = crew.kickoff()

    output_paths = build_output_paths(args.output_dir)
    merge_analysis_with_script(
        analysis_path=output_paths.analysis,
        script_path=output_paths.compiled_script,
        output_path=output_paths.final_with_analysis,
    )

    summary = {
        "results": make_serialisable(results),
        "outputs": {
            "blueprint": str(output_paths.blueprint),
            "screenplay": str(output_paths.screenplay),
            "qa_report": str(output_paths.qa_report),
            "formatted_screenplay": str(output_paths.formatted_screenplay),
            "compiled_script": str(output_paths.compiled_script),
            "analysis": str(output_paths.analysis),
            "final_with_analysis": str(output_paths.final_with_analysis),
        },
    }
    summary_path = args.output_dir / "pipeline_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    main()
