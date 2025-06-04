from .s3 import S3Handler
from ..config import settings

s3 = S3Handler(
    bucket_name=settings.aws_kb_files_bucket_name,
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
    region_name=settings.aws_region_name,
)
