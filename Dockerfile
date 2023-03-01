#!/bin/bash
FROM python:3.10-slim
WORKDIR /app
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

RUN apt-get update -qq \
    && apt-get install --no-install-recommends --yes \
        build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get autoremove --purge --yes \
        build-essential

RUN pip install psycopg2-binary
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 443
CMD ["python", "app.py"]