"""Repo-relative paths; downloaded responses and generated results stay untracked."""
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WORK = REPO / "data" / "research-validation"
WORK.mkdir(parents=True, exist_ok=True)
(WORK / "source-responses").mkdir(exist_ok=True)
