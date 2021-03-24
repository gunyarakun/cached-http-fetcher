from .base import StorageBase

class S3Storage(StorageBase):
    def __init__(self, *, bucket: str, boto3_s3_client):
        if not bucket:
            raise ValueError

        self.bucket = bucket
        self.client = boto3_s3_client

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
