FROM ubuntu:20.04

# Install dependencies
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    ffmpeg \
    espeak espeak-data libespeak-dev \
    libespeak-ng1 libespeak-ng-dev \
    locales \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set UTF-8 locale and encoding
RUN locale-gen en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
ENV PYTHONIOENCODING=UTF-8
ENV AENEAS_FORCE_AUDIOREAD=ffmpeg
ENV AENEAS_FORCE_TTS=espeak

RUN pip3 install --no-cache-dir numpy scipy librosa soundfile audioread

# Install aeneas (via pip or from source)
RUN pip3 install --no-cache-dir aeneas==1.7.3

# Copy entrypoint or working scripts (if any)
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

WORKDIR /data

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
