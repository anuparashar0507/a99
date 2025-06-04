from lib.repositories.outline_repository import OutlineRepository
from lib.repositories.topic_repository import TopicsRepository
from lib.repositories.user_repository import UserRepository
from lib.repositories.kb_repository import KnowledgeBaseRepository
from lib.repositories.ideation_repository import IdeationRepository
from lib.repositories.content_repository import ContentRepository
from lib.repositories.content_desk_repository import ContentDeskRepository
from lib.repositories.post_repository import PostRepository
from ..db.db_protocol import Persister


class RepositoryManager:
    kb_repository: KnowledgeBaseRepository
    user_repository: UserRepository
    topic_repository: TopicsRepository
    ideation_repository: IdeationRepository
    outline_repository: OutlineRepository
    content_repository: ContentRepository
    content_desk_repository: ContentDeskRepository
    post_repository: PostRepository

    def __init__(self, db: Persister):
        self.db = db
        self.kb_repository = KnowledgeBaseRepository(db)
        self.user_repository = UserRepository(db)
        self.topic_repository = TopicsRepository(db)
        self.ideation_repository = IdeationRepository(db)
        self.outline_repository = OutlineRepository(db)
        self.content_repository = ContentRepository(db)
        self.content_desk_repository = ContentDeskRepository(db)
        self.post_repository = PostRepository(db)
