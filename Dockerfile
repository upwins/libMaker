FROM nvcr.io/nvidia/pytorch:24.01-py3

WORKDIR /app

COPY requirements.txt .
RUN apt-get update \
    && python -m pip install --no-cache-dir -v -r requirements.txt

COPY . .