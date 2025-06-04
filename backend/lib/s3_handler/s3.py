import boto3
import logging
from botocore.exceptions import (
    BotoCoreError,
    NoCredentialsError,
    PartialCredentialsError,
    ClientError,
)


class S3Handler:
    def __init__(
        self,
        bucket_name,
        aws_access_key_id=None,
        aws_secret_access_key=None,
        region_name="us-east-1",
    ):
        """
        Initialize the S3FileHandler class.
        """
        self.bucket_name = bucket_name
        self.region_name = region_name
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )
        self.logger = logging.getLogger(__name__)

    def upload_file(self, file, s3_key):
        """
        Uploads a file to S3.
        :param file_path: Local path to the file
        :param s3_key: The key (path) in the S3 bucket
        """
        try:
            file.file.seek(0)
            self.s3_client.upload_fileobj(file.file, self.bucket_name, s3_key)
            file_url = f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{s3_key}"
            self.logger.info(f"File uploaded successfully: {s3_key}")
            return file_url
        except NoCredentialsError:
            self.logger.error("AWS credentials not found.")
        except PartialCredentialsError:
            self.logger.error("Incomplete AWS credentials provided.")
        except ClientError as e:
            self.logger.error(f"AWS ClientError: {e}")
        except BotoCoreError as e:
            self.logger.error(f"BotoCoreError: {e}")
        return False

    def delete_file(self, s3_key):
        """
        Deletes a file from S3.
        :param s3_key: The key (path) in the S3 bucket
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            self.logger.info(f"File deleted successfully: {s3_key}")
            return True
        except NoCredentialsError:
            self.logger.error("AWS credentials not found.")
        except PartialCredentialsError:
            self.logger.error("Incomplete AWS credentials provided.")
        except ClientError as e:
            self.logger.error(f"AWS ClientError: {e}")
        except BotoCoreError as e:
            self.logger.error(f"BotoCoreError: {e}")
        return False
