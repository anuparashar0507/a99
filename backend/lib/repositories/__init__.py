from .repository_manager_impl import RepositoryManager
from ..db import db

repository_manager = RepositoryManager(db)
