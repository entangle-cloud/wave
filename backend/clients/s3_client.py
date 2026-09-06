import os 
import boto3
from botocore.config import Config

R2_ACCESS_TOKEN = os.getenv("R2_ACCESS_KEY")
R2_ACCESS_SECRET = os.getenv("R2_ACCESS_SECRET")
R2_ENDPOINT = os.getenv("R2_ENDPOINT")
BUCKET_NAME = os.getenv("BUCKET_NAME")

s3_client = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_TOKEN,
    aws_secret_access_key=R2_ACCESS_SECRET,
    config=Config(
        signature_version="s3v4",
        request_checksum_calculation="when_required",
        response_checksum_validation="when_required",
    ),
    region_name="auto",
)
