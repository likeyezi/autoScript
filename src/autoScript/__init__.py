"""autoScript package providing CrewAI screenplay adaptation pipeline."""
from .crew import build_crew, build_output_paths, CrewOutputPaths

__all__ = ["build_crew", "build_output_paths", "CrewOutputPaths"]
