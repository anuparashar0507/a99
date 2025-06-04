from typing import Protocol
from lib.repositories.ideation_repository import IdeationRepository
from lib.repositories.user_repository import UserRepository
from lib.repositories.kb_repository import KnowledgeBaseRepository
from lib.repositories.topic_repository import TopicsRepository
from lib.repositories.outline_repository import OutlineRepository
from lib.repositories.content_repository import ContentRepository
from lib.repositories.content_desk_repository import ContentDeskRepository
from lib.repositories.post_repository import PostRepository


class RepositoryManagerProtocol(Protocol):
    kb_repository: KnowledgeBaseRepository
    user_repository: UserRepository
    topic_repository: TopicsRepository
    ideation_repository: IdeationRepository
    outline_repository: OutlineRepository
    content_repository: ContentRepository
    content_desk_repository: ContentDeskRepository
    post_repository: PostRepository
