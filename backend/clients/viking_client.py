import os 
from openviking_sdk import AsyncHTTPClient

OPEN_VIKING_ENDPOINT = os.getenv("OPENVIKING_ENDPOINT")
OPEN_VIKING_TOKEN = os.getenv("OPENVIKING_TOKEN")
client = AsyncHTTPClient(url=OPEN_VIKING_ENDPOINT, api_key=OPEN_VIKING_TOKEN)
