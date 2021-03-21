from .base import StorageBase
import boto3

MAX_POOL_CONNECTIONS= 100

class S3Storage(StorageBase):
    def __init__(self, **kwargs):
        aws_access_key_id = kwargs["aws_access_key_id"]
        aws_secret_access_key = kwargs["aws_secret_access_key"]
        bucket = kwargs["bucket"]

        if not bucket:
            raise ValueError

        if aws_access_key_id and aws_secret_access_key:
            self.client = boto3.client(
                "s3",
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                config=Config(max_pool_connections=MAX_POOL_CONNECTIONS)
            )
        else:
            self.client = boto3.client(
                "s3",
                config=Config(max_pool_connections=MAX_POOL_CONNECTIONS)
            )

        self.bucket = bucket

    def get(self, key: str) -> bytes:
        try:
            obj = self.client.get_object(Bucket=self.bucket, Key=key)
            return obj["Body"]
        except ClientError as ex:
            if ex.response["Error"]["Code"] == "NoSuchKey":
                return None
            else:
                raise

    def put(self, key: str, value: bytes, expire=None) -> None:
        config = dict(ACL="bucket-owner-full-control", Bucket=self.bucket, Key=key, ContentType=content_type, Body=value)
        if expire:
            # FIXME: set proper expire
            config["CacheControl"] = "FIXME"
        self.client.put_object(**config)

    def url_from_key(self, key: str) -> str:
        raise NotImplementedError
