from .db_impl import MongoDB
from .db_protocol import Persister
from lib.config import settings

db: Persister = MongoDB(uri=settings.mongodb_uri, db_name=settings.mongodb_db_name)
