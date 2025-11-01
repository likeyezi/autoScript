"""Tool that serves novel text in manageable chunks for LLM consumption."""
from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import List

from crewai_tools import BaseTool


def _split_text(text: str, *, chunk_size: int, overlap: int) -> List[str]:
    """Split text into overlapping character chunks."""

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0:
        raise ValueError("overlap must be non-negative")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    cleaned = text.replace("\r\n", "\n")
    chunks: List[str] = []
    start = 0
    text_length = len(cleaned)
    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = cleaned[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap
        if start < 0:
            start = 0
    return chunks if chunks else [""]


@dataclass
class NovelChunkMetadata:
    """Metadata describing how the novel has been chunked."""

    total_characters: int
    chunk_size: int
    overlap: int
    chunk_count: int

    def usage_instructions(self) -> str:
        approx_tokens = math.ceil(self.chunk_size / 1.5)
        return (
            "小说内容已被切分为 {chunk_count} 个片段，每段约 {chunk_size} 字（约 {tokens} tokens）。"\
            "调用方式：\n"
            "- `chunk:<编号>` 以 1 开始获取对应片段。\n"
            "- `range:<起始>-<结束>` 获取连续片段（一次最多 5 个）。\n"
            "- `search:<关键词>` 返回包含关键词的片段列表。\n"
            "如需快速总览，可先阅读 `preview` 片段。"
        ).format(
            chunk_count=self.chunk_count,
            chunk_size=self.chunk_size,
            tokens=approx_tokens,
        )


class NovelChunkTool(BaseTool):
    """Expose large novel texts to Crew agents without exceeding context limits."""

    name = "NovelChunkTool"
    description = (
        "用于按需获取原著小说片段的工具，可通过编号或关键字检索，避免一次性"
        "加载超长文本导致的上下文溢出。"
    )

    def __init__(self, novel_text: str, *, chunk_size: int = 3500, overlap: int = 200):
        super().__init__()
        self._novel_text = novel_text
        self._chunk_size = chunk_size
        self._overlap = overlap
        self._chunks = _split_text(novel_text, chunk_size=chunk_size, overlap=overlap)
        self._metadata = NovelChunkMetadata(
            total_characters=len(novel_text),
            chunk_size=chunk_size,
            overlap=overlap,
            chunk_count=len(self._chunks),
        )

    @property
    def metadata(self) -> NovelChunkMetadata:
        return self._metadata

    @property
    def preview(self) -> str:
        """Return the first chunk as a lightweight preview."""

        if not self._chunks:
            return ""
        first_chunk = self._chunks[0]
        return first_chunk[:1000]

    def usage_guide(self) -> str:
        return self._metadata.usage_instructions()

    def _run(self, query: str) -> str:
        query = (query or "").strip()
        if not query:
            return self._help_text()
        if query.lower() == "preview":
            return self._render_preview()
        if query.lower().startswith("chunk:"):
            return self._fetch_single_chunk(query)
        if query.lower().startswith("range:"):
            return self._fetch_range(query)
        if query.lower().startswith("search:"):
            return self._search_chunks(query)
        return self._help_text()

    async def _arun(self, query: str) -> str:
        return self._run(query)

    def _help_text(self) -> str:
        return (
            "请输入以下指令之一：\n"
            "- preview\n"
            "- chunk:<编号>（例如 chunk:3）\n"
            "- range:<起始>-<结束>（例如 range:5-7）\n"
            "- search:<关键词>（例如 search:反派）\n"
            f"{self.usage_guide()}"
        )

    def _render_preview(self) -> str:
        preview_text = self.preview
        return f"[Preview 1/{len(self._chunks)}]\n{preview_text}"

    def _fetch_single_chunk(self, query: str) -> str:
        try:
            index = int(query.split(":", 1)[1]) - 1
        except (IndexError, ValueError):
            return "chunk 指令格式应为 chunk:<编号>，编号需为正整数。"
        if index < 0 or index >= len(self._chunks):
            return f"编号超出范围，目前共有 {len(self._chunks)} 个片段。"
        return f"[Chunk {index + 1}/{len(self._chunks)}]\n{self._chunks[index]}"

    def _fetch_range(self, query: str) -> str:
        try:
            payload = query.split(":", 1)[1]
            start_str, end_str = payload.split("-", 1)
            start = int(start_str) - 1
            end = int(end_str) - 1
        except (IndexError, ValueError):
            return "range 指令格式应为 range:<起始>-<结束>，编号需为正整数。"
        if start < 0 or end < start:
            return "起始与结束编号需为正序，且不得小于 1。"
        if end >= len(self._chunks):
            return f"结束编号超出范围，目前共有 {len(self._chunks)} 个片段。"
        if (end - start) + 1 > 5:
            return "一次最多获取 5 个连续片段，请缩小范围。"
        selected = self._chunks[start : end + 1]
        header = f"[Chunks {start + 1}-{end + 1}/{len(self._chunks)}]"
        return f"{header}\n" + "\n\n".join(selected)

    def _search_chunks(self, query: str) -> str:
        keyword = query.split(":", 1)[1].strip()
        if not keyword:
            return "search 指令需要提供关键词，例如 search:反派。"
        pattern = re.compile(re.escape(keyword))
        matches = [
            f"[Chunk {index + 1}]\n{self._chunks[index]}"
            for index, chunk in enumerate(self._chunks)
            if pattern.search(chunk)
        ]
        if not matches:
            return f"未找到包含“{keyword}”的片段。"
        return "\n\n".join(matches[:5])


__all__ = ["NovelChunkTool", "NovelChunkMetadata"]

