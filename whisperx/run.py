import requests
import json
import os
import csv
from pydub import AudioSegment

# Config
whisper_url = "http://localhost:9000/asr"
audio_file_path = "../assets/Actual Test 05.mp3"  # file gốc
chunk_length_ms = 10 * 60 * 1000  # 10 phút
params = {
    "encode": "true",
    "task": "transcribe",
    "language": "en",
    "output": "json",
    "temperature": 0.0
}

# Tạo thư mục tạm để lưu chunk
os.makedirs("chunks", exist_ok=True)

# Load audio
audio = AudioSegment.from_file(audio_file_path)
duration_ms = len(audio)
print(f"📏 Audio length: {duration_ms/1000:.2f} seconds")

all_results = []
offset_seconds = 0.0
segment_id = 1

# Cắt thành các chunk 10 phút
for i in range(0, duration_ms, chunk_length_ms):
    chunk = audio[i:i + chunk_length_ms]
    chunk_filename = f"chunks/chunk_{i//chunk_length_ms}.wav"
    chunk.export(chunk_filename, format="wav")
    print(f"✂️ Exported {chunk_filename}")

    try:
        # Gửi chunk tới Whisper
        with open(chunk_filename, "rb") as audio_file:
            files = {"audio_file": audio_file}
            print(f"🔄 Sending chunk {i//chunk_length_ms} to Whisper...")
            response = requests.post(whisper_url, params=params, files=files)
            response.raise_for_status()
            chunk_json = response.json()

            # Cộng dồn timestamp và lưu vào list
            for seg in chunk_json.get("segments", []):
                start_time = round(seg["start"] + offset_seconds, 3)
                end_time = round(seg["end"] + offset_seconds, 3)
                text = seg["text"].strip()
                all_results.append([segment_id, start_time, end_time, text])
                segment_id += 1

    finally:
        # Xóa file chunk sau khi xử lý xong
        if os.path.exists(chunk_filename):
            os.remove(chunk_filename)
            print(f"🗑️ Removed {chunk_filename}")

    # Cộng offset thời gian cho chunk tiếp theo
    offset_seconds += len(chunk) / 1000.0

# Lưu file CSV
csv_file_path = "raw.csv"
with open(csv_file_path, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["id", "start", "end", "text"])
    writer.writerows(all_results)

print(f"✅ Done! Saved merged transcription to {csv_file_path}")
