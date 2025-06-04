from ..repositories import repository_manager
from .kb import KnowledgeBase
from ..lyzr_rag import rag, parse
from ..s3_handler import s3


def get_kb_service():
    kb = KnowledgeBase(repository_manager, rag, parse, s3)
    return kb
