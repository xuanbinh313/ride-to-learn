FROM python:3.9-bullseye

RUN apt-get update && apt-get install -y \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    ffmpeg \
    espeak \
    python3-dev \
    git \
    pkg-config \
    libmagic-dev

RUN pip install --upgrade pip setuptools wheel
RUN pip install numpy
RUN pip install aeneas

WORKDIR /data
