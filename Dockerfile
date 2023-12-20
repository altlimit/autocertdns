FROM google/cloud-sdk:latest

RUN apt update && apt -y install python3-venv libaugeas0
RUN python3 -m venv /opt/certbot/ && /opt/certbot/bin/pip install --upgrade pip && /opt/certbot/bin/pip install certbot
RUN ln -s /opt/certbot/bin/certbot /usr/bin/certbot

WORKDIR /home
COPY renew.py .
