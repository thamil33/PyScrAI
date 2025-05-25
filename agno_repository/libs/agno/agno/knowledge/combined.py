from typing import Iterator, List

from agno_src.document import Document
from agno_src.knowledge.agent import AgentKnowledge
from agno_src.utils.log import log_debug


class CombinedKnowledgeBase(AgentKnowledge):
    sources: List[AgentKnowledge] = []

    @property
    def document_lists(self) -> Iterator[List[Document]]:
        """Iterate over knowledge bases and yield lists of documents.
        Each object yielded by the iterator is a list of documents.

        Returns:
            Iterator[List[Document]]: Iterator yielding list of documents
        """

        for kb in self.sources:
            log_debug(f"Loading documents from {kb.__class__.__name__}")
            yield from kb.document_lists
