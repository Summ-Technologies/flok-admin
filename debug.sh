# Run this from the root of the repo and ensure your .env file exists
FLASK_APP=$PWD/server/ APP_CONFIG=$PWD/config.py env $(cat .env) flask run --host 0.0.0.0 --port 4444
