import os

# SQLALCHEMY
SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]
AWS_ACCESS_KEY = os.environ["AWS_ACCESS_KEY"]
AWS_SECRET_KEY = os.environ["AWS_SECRET_KEY"]
AWS_HOTELS_PREFIX = os.environ.get("AWS_HOTELS_PREFIX")
CORS_ALLOW_ORIGINS = os.environ.get("CORS_ALLOW_ORIGINS")
GOOGLE_CREDENTIALS_PATH = os.environ["GOOGLE_CREDENTIALS_PATH"]
GOOGLE_MAPS_KEY = os.environ["GOOGLE_MAPS_KEY"]

# Logging
tmp = os.environ.get("SUMM_LOG_FILE")
if tmp:
    SUMM_LOG_FILE = tmp

tmp = os.environ.get("SUMM_LOG_FILE_SIZE")
if tmp:
    SUMM_LOG_FILE_SIZE = tmp
