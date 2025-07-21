FROM python:3.10-slim

# Cài các gói cần thiết
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Tạo thư mục làm việc
WORKDIR /app

# Cài whisperx và torch CPU (nếu dùng GPU thì đổi sau)
RUN pip install --upgrade pip && \
    pip install git+https://github.com/m-bain/whisperx.git \
    torch==2.2.2 torchaudio==2.2.2 torchvision==0.17.2 --index-url https://download.pytorch.org/whl/cpu

# Copy toàn bộ project vào container
COPY . .

CMD ["python", "run.py"]
