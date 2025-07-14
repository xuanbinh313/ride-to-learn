FROM python:3.10-slim

RUN pip install gtts pydub
RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /data
COPY merge_bilingual.py /data/
