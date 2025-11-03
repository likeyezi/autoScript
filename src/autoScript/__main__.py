"""Command line interface for running the LangGraph novel-to-script pipeline."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from .rag import DualRAGIndex, SceneSplitter
from .state import NovelAdaptationState
from .workflow import NovelToScriptOrchestrator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the LangGraph dual-RAG adaptation pipeline.")
    parser.add_argument("blueprint", type=Path, help="Path to the宏观蓝图 JSON 文件")
    parser.add_argument("style_corpus", type=Path, help="Path to the风格样本文本文件")
    parser.add_argument("novel_text", type=Path, help="Path to the原著小说文本文件")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs"),
        help="Directory for workflow outputs",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum automatic rewrite attempts before升级人工",
    )
    parser.add_argument(
        "--min-scene-chars",
        type=int,
        default=300,
        help="Minimum characters per scene when splitting原著",
    )
    parser.add_argument(
        "--max-scene-chars",
        type=int,
        default=3200,
        help="Maximum characters per scene when splitting原著",
    )
    return parser.parse_args()


def load_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"无法找到文件: {path}")
    return path.read_text(encoding="utf-8")


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


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


def build_rag_index(*, novel_text: str, style_text: str, min_scene_chars: int, max_scene_chars: int) -> DualRAGIndex:
    splitter = SceneSplitter(min_scene_chars=min_scene_chars, max_scene_chars=max_scene_chars)
    content_docs = splitter.split(novel_text, source="novel")
    style_docs = splitter.split(style_text, source="style")
    index = DualRAGIndex()
    index.index_content(content_docs)
    index.index_style(style_docs)
    return index


def persist_scripts(scripts: List[str], output_dir: Path) -> List[str]:
    files: List[str] = []
    for index, script in enumerate(scripts, start=1):
        path = output_dir / f"episode_{index:03d}.md"
        path.write_text(script, encoding="utf-8")
        files.append(str(path))
    return files


def main() -> Dict[str, Any]:
    args = parse_args()
    ensure_directory(args.output_dir)

    blueprint = json.loads(load_text(args.blueprint))
    style_text = load_text(args.style_corpus)
    novel_text = load_text(args.novel_text)

    rag_index = build_rag_index(
        novel_text=novel_text,
        style_text=style_text,
        min_scene_chars=args.min_scene_chars,
        max_scene_chars=args.max_scene_chars,
    )

    orchestrator = NovelToScriptOrchestrator(rag_index=rag_index, max_retries=args.max_retries)
    final_state: NovelAdaptationState = orchestrator.run(blueprint=blueprint)

    delivered_scripts = final_state.get("delivered_scripts", [])
    script_files = persist_scripts(delivered_scripts, args.output_dir)
    summary = {
        "delivered_scripts": script_files,
        "retry_count": final_state.get("retry_count", 0),
        "requires_human_review": final_state.get("requires_human_review", False),
    }
    summary_path = args.output_dir / "workflow_summary.json"
    summary_path.write_text(json.dumps(make_serialisable(summary), ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    main()
