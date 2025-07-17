# pyright: strict = false
# type: ignore
import aioboto3
from botocore.exceptions import ClientError
from fastapi import UploadFile
from urllib.parse import urlparse
from app.core.config import settings


AWS_REGION = settings.AWS_REGION
AWS_BUCKET_NAME = settings.AWS_BUCKET_NAME
AWS_ACCESS_KEY_ID = settings.AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY = settings.AWS_SECRET_ACCESS_KEY

session = aioboto3.Session()

async def upload_or_replace_file(file: UploadFile, key: str, replace: bool = True) -> str:
    async with session.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    ) as s3:
        if replace:
            # Delete the existing file (ignore if not exists)
            try:
                await s3.delete_object(Bucket=AWS_BUCKET_NAME, Key=key)
            except ClientError:
                pass  # Not found or already deleted

        await s3.upload_fileobj(file.file, AWS_BUCKET_NAME, key)
        return f"https://{AWS_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{key}"

async def delete_file(url: str) -> bool:
    async with session.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    ) as s3:
        # extract the key from the URL
        parsed_url = urlparse(url)
        key = parsed_url.path.lstrip('/')
        try:
            await s3.delete_object(Bucket=AWS_BUCKET_NAME, Key=key)
            return True
        except ClientError:
            return False
        

async def upload_multiple_files(files: list[UploadFile], keys: list[str], replace: bool = True) -> list[str]:
    urls = []
    for file, key in zip(files, keys):
        url = await upload_or_replace_file(file, key, replace)
        urls.append(url)
    return urls
