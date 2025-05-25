from typing import Union

from agno_src.storage.session.agent import AgentSession
from agno_src.storage.session.team import TeamSession
from agno_src.storage.session.workflow import WorkflowSession

Session = Union[AgentSession, TeamSession, WorkflowSession]

__all__ = [
    "AgentSession",
    "TeamSession",
    "WorkflowSession",
    "Session",
]
