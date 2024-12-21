FROM python:3.11-bullseye

COPY ../requirements.txt /tmp/requirements.txt
COPY ../requirements_local.txt /tmp/requirements_local.txt

RUN pip install -r /tmp/requirements_local.txt