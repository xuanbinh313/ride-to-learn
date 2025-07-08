from pydub import AudioSegment
from gtts import gTTS
import json
import os

# Cấu hình file
SOURCE_FILE = "83-85.mp3"
SEGMENTS_FILE = "segments.json"

# Chuyển thời gian mm:ss => milliseconds
def to_ms(t):
    m, s = map(int, t.split(":"))
    return (m * 60 + s) * 1000
def time_to_ms(tstr: str) -> int:
    """
    Convert time string like '00:01.250' or '01:02.750' to milliseconds.
    """
    parts = tstr.split(":")
    minutes = int(parts[0])
    seconds, ms = map(float, parts[1].split("."))
    return int((minutes * 60 + seconds + ms / 1000) * 1000)

# Load dữ liệu
original = AudioSegment.from_mp3(SOURCE_FILE)
with open(SEGMENTS_FILE, "r", encoding="utf-8") as f:
    segments = json.load(f)
for _,parent_seg in enumerate(segments):
    final_audio = AudioSegment.silent(duration=0)
    # Tạo tên file xuất
    name = parent_seg["name"]
    output_file = f"{name}-output.mp3"
    for i, seg in enumerate(parent_seg["children"]):
        print(f"🔧 Xử lý đoạn {i+1}...")
        print(seg)
        start_ms = time_to_ms(seg["start"])
        end_ms = time_to_ms(seg["end"])

        # 1. Cắt đoạn TOEIC gốc
        clip = original[start_ms:end_ms]

        # 2. Chuyển bản dịch sang TTS
        tts = gTTS(text=seg["translation"], lang='vi')
        tts_path = f"temp_tts_{i}.mp3"
        tts.save(tts_path)
        tts_audio = AudioSegment.from_mp3(tts_path)

        # 3. Thêm im lặng
        pause = AudioSegment.silent(duration=seg["pause_after"] * 1000)

        # 4. Ghép lại: clip + TTS + silence
        combined =  tts_audio + pause + clip  + pause
        final_audio += combined

        os.remove(tts_path)

    # Xuất file cuối
    final_audio.export(output_file, format="mp3")
    print(f"✅ Xuất thành công: {output_file}")
