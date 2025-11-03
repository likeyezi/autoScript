"""LangGraph orchestration for the novel-to-script pipeline."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from langgraph.graph import END, START, StateGraph

from .rag import DualRAGIndex
from .state import DEFAULT_STATE, EpisodeTask, NovelAdaptationState
from .validator import validate_script


@dataclass
class PlannerAgent:
    """Planner responsible for turning the blueprint into episode tasks."""

    episodes_per_batch: int = 1

    def plan(self, blueprint: Dict[str, Any]) -> List[EpisodeTask]:
        episodes = blueprint.get("episodes") or []
        tasks: List[EpisodeTask] = []
        if not episodes:
            outline = blueprint.get("outline", "")
            synopsis = outline[:200] if outline else "自动生成集任务"
            tasks.append(
                EpisodeTask(
                    episode_number=1,
                    title=blueprint.get("title", "第1集"),
                    synopsis=synopsis,
                    rag_content_query=synopsis,
                    rag_style_query=blueprint.get("style_keywords", synopsis),
                )
            )
            return tasks
        for index, episode in enumerate(episodes, start=1):
            synopsis = episode.get("summary") or episode.get("synopsis") or episode.get("beats", "")
            query = episode.get("rag_query") or synopsis or episode.get("title", "")
            style_query = episode.get("style_query") or episode.get("tone", "") or query
            tasks.append(
                EpisodeTask(
                    episode_number=episode.get("episode_number", index),
                    title=episode.get("title", f"第{index}集"),
                    synopsis=synopsis or f"Episode {index} synopsis pending",
                    rag_content_query=query or synopsis,
                    rag_style_query=style_query or query,
                )
            )
        return tasks


@dataclass
class WriterAgent:
    """Writer agent assembling screenplay drafts from retrieved material."""

    def write(
        self,
        *,
        task: EpisodeTask,
        content_chunks: List[str],
        style_chunks: List[str],
        feedback: str | None = None,
    ) -> str:
        header = f"第{task.episode_number}集 {task.title}"
        synopsis_block = f"旁白：{task.synopsis.strip()}"
        if feedback:
            synopsis_block += f"\n旁白：【返工指令】{feedback.strip()}"
        scenes = []
        for scene_index, content in enumerate(content_chunks[:3], start=1):
            scene_header = f"[{task.episode_number}-{scene_index}] 改编场景 - 内 - 夜"
            style_hint = style_chunks[scene_index - 1] if scene_index - 1 < len(style_chunks) else ""
            dialogue = style_hint.splitlines()[:3]
            dialogue_lines = [line for line in dialogue if line.strip()][:2]
            excerpt = content.strip().splitlines()
            excerpt_text = excerpt[0][:120] if excerpt else "根据原著扩写冲突"
            scene = [scene_header, synopsis_block, f"旁白：改编依据——{excerpt_text}"]
            for idx, line in enumerate(dialogue_lines, start=1):
                scene.append(f"角色{idx}：{line.strip()}")
            scene.append(f"△ 角色{scene_index}：整理道具显示动作回应原著情节")
            scenes.append("\n".join(scene))
        if not scenes:
            scenes.append(
                "\n".join(
                    [
                        f"[{task.episode_number}-1] 改编场景 - 内 - 夜",
                        synopsis_block,
                        "角色1：根据原著补全对话",
                        "△ 角色1：摆放关键道具强调冲突",
                    ]
                )
            )
        return f"{header}\n\n" + "\n\n".join(scenes)


@dataclass
class ReviewerAgent:
    """Reviewer translating validator errors into actionable feedback."""

    def review(self, errors: List[str], task: EpisodeTask) -> str:
        if not errors:
            return ""
        prefix = (
            f"第{task.episode_number}集《{task.title}》需要修订："
        )
        advice = []
        for error in errors:
            if "WordCountError" in error:
                advice.append("补足剧情信息但避免灌水，优先扩写关键冲突场景。")
            elif "PunctuationError" in error:
                advice.append("替换所有省略号或破折号为符合铁律的标点。")
            elif "FormatError" in error:
                advice.append("逐行核对场景、旁白、动作格式，确保一行只含一个元素。")
            elif "ActionLineError" in error:
                advice.append("把动作行的情绪描述改写为可见的物理动作。")
            elif "CensorshipError" in error:
                advice.append("重新处理触犯审查底线的内容，改用隐喻或安全表达。")
            else:
                advice.append(error)
        joined = "\n".join(advice)
        return prefix + "\n" + joined


class NovelToScriptOrchestrator:
    """High level interface for building and running the LangGraph workflow."""

    def __init__(
        self,
        *,
        rag_index: DualRAGIndex,
        planner: PlannerAgent | None = None,
        writer: WriterAgent | None = None,
        reviewer: ReviewerAgent | None = None,
        max_retries: int = 3,
    ) -> None:
        self._rag_index = rag_index
        self._planner = planner or PlannerAgent()
        self._writer = writer or WriterAgent()
        self._reviewer = reviewer or ReviewerAgent()
        self._max_retries = max_retries
        self._graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(NovelAdaptationState)
        graph.add_node("human_input", self._human_input_node)
        graph.add_node("planner", self._planner_node)
        graph.add_node("retrieval", self._retrieval_node)
        graph.add_node("writer", self._writer_node)
        graph.add_node("validator", self._validator_node)
        graph.add_node("reviewer", self._reviewer_node)
        graph.add_node("deliver", self._deliver_node)

        graph.add_edge(START, "human_input")
        graph.add_edge("human_input", "planner")
        graph.add_edge("planner", "retrieval")
        graph.add_edge("retrieval", "writer")
        graph.add_edge("writer", "validator")
        graph.add_conditional_edges("validator", self._validator_router, {
            "deliver": "deliver",
            "review": "reviewer",
            "human": "human_input",
        })
        graph.add_edge("reviewer", "writer")
        graph.add_conditional_edges("deliver", self._delivery_router, {
            "continue": "retrieval",
            "done": END,
        })
        return graph.compile(checkpointer=None)

    def run(self, *, blueprint: Dict[str, Any]) -> NovelAdaptationState:
        initial_state: NovelAdaptationState = DEFAULT_STATE.copy()
        initial_state["human_blueprint"] = blueprint
        return self._graph.invoke(initial_state)

    # Node implementations -------------------------------------------------
    def _human_input_node(self, state: NovelAdaptationState) -> NovelAdaptationState:
        if state.get("requires_human_review"):
            return state
        state.setdefault("requires_human_review", False)
        return state

    def _planner_node(self, state: NovelAdaptationState) -> NovelAdaptationState:
        if not state.get("episode_tasks"):
            tasks = [task.to_dict() for task in self._planner.plan(state["human_blueprint"])]
            state["episode_tasks"] = tasks
            if tasks:
                state["current_task"] = tasks[0]
        return state

    def _retrieval_node(self, state: NovelAdaptationState) -> NovelAdaptationState:
        task_dict = state.get("current_task") or {}
        if not task_dict:
            return state
        task = EpisodeTask(**task_dict)
        content_results = self._rag_index.retrieve_content(task.rag_content_query, top_k=3)
        style_results = self._rag_index.retrieve_style(task.rag_style_query, top_k=3)
        state["content_chunks"] = "\n\n".join(result.text for result in content_results)
        state["style_chunks"] = "\n\n".join(result.text for result in style_results)
        return state

    def _writer_node(self, state: NovelAdaptationState) -> NovelAdaptationState:
        task_dict = state.get("current_task") or {}
        if not task_dict:
            return state
        task = EpisodeTask(**task_dict)
        content_chunks = state.get("content_chunks", "").split("\n\n") if state.get("content_chunks") else []
        style_chunks = state.get("style_chunks", "").split("\n\n") if state.get("style_chunks") else []
        draft = self._writer.write(
            task=task,
            content_chunks=[chunk for chunk in content_chunks if chunk.strip()],
            style_chunks=[chunk for chunk in style_chunks if chunk.strip()],
            feedback=state.get("feedback"),
        )
        state["draft_script"] = draft
        return state

    def _validator_node(self, state: NovelAdaptationState) -> NovelAdaptationState:
        draft = state.get("draft_script", "")
        errors = validate_script(draft)
        state["validation_errors"] = errors
        return state

    def _reviewer_node(self, state: NovelAdaptationState) -> NovelAdaptationState:
        task_dict = state.get("current_task") or {}
        if not task_dict:
            state["feedback"] = ""
            return state
        task = EpisodeTask(**task_dict)
        errors = state.get("validation_errors", [])
        state["feedback"] = self._reviewer.review(errors, task)
        state["retry_count"] = state.get("retry_count", 0) + 1
        return state

    def _deliver_node(self, state: NovelAdaptationState) -> NovelAdaptationState:
        delivered = list(state.get("delivered_scripts", []))
        delivered.append(state.get("draft_script", ""))
        state["delivered_scripts"] = delivered
        state["retry_count"] = 0
        state["feedback"] = ""
        state["validation_errors"] = []
        episode_index = state.get("episode_index", 0) + 1
        state["episode_index"] = episode_index
        tasks = state.get("episode_tasks", [])
        if episode_index < len(tasks):
            state["current_task"] = tasks[episode_index]
        return state

    # Routing helpers ------------------------------------------------------
    def _validator_router(self, state: NovelAdaptationState) -> str:
        errors = state.get("validation_errors", [])
        if not errors:
            return "deliver"
        if state.get("retry_count", 0) >= self._max_retries:
            state["requires_human_review"] = True
            return "human"
        return "review"

    def _delivery_router(self, state: NovelAdaptationState) -> str:
        tasks = state.get("episode_tasks", [])
        if state.get("episode_index", 0) >= len(tasks):
            return "done"
        return "continue"


__all__ = [
    "PlannerAgent",
    "WriterAgent",
    "ReviewerAgent",
    "NovelToScriptOrchestrator",
]
