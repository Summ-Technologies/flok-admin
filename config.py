import os

# SQLALCHEMY
SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]
# AWS_ACCESS_KEY = os.environ["AWS_ACCESS_KEY"]
# AWS_SECRET_KEY = os.environ["AWS_SECRET_KEY"]
# CORS_ALLOW_ORIGINS = os.environ.get("CORS_ALLOW_ORIGINS")
GOOGLE_CREDENTIALS_PATH = os.environ["GOOGLE_CREDENTIALS_PATH"]

# Logging
tmp = os.environ.get("SUMM_LOG_FILE")
if tmp:
    SUMM_LOG_FILE = tmp

tmp = os.environ.get("SUMM_LOG_FILE_SIZE")
if tmp:
    SUMM_LOG_FILE_SIZE = tmp
