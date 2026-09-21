import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'you-should-change-this')
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/capture_moments')
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_S3_BUCKET = os.environ.get('AWS_S3_BUCKET')
    AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
    # Optional SES settings
    AWS_SES_REGION = os.environ.get('AWS_SES_REGION', AWS_REGION)
    AWS_SES_SOURCE_EMAIL = os.environ.get('AWS_SES_SOURCE_EMAIL')
