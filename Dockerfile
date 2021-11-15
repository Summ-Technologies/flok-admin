FROM jaredhanson11/serverbase

# Pickup security patches
RUN apt-get update && apt-get upgrade -y

# Allows requirements to be downloaded from custom pypi
ARG PIP_EXTRA_INDEX_URL
ARG PIP_TRUSTED_HOST

# Install required packages
COPY requirements.txt ./requirements.txt
RUN apt-get install -y libpq-dev python3-dev gcc \
    && pip install --pre --no-cache -r requirements.txt \
    && rm requirements.txt

# Copy server code to the /app/ dir
COPY ./config.py ./
COPY ./server ./server
COPY ./static ./static

ENV APP_CONFIG /app/config.py

RUN apt-get install nginx -y
COPY nginx.conf /etc/nginx/sites-enabled/default

COPY entrypoint.sh /entrypoint.sh