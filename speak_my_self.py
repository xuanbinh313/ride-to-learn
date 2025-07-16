from gtts import gTTS
from pydub import AudioSegment
import os

def text_to_audio(vi_line, en_line, index):
    vi_tts = gTTS(vi_line, lang='vi')
    en_tts = gTTS(en_line, lang='en')

    vi_path = f"temp_vi_{index}.mp3"
    en_path = f"temp_en_{index}.mp3"

    vi_tts.save(vi_path)
    en_tts.save(en_path)

    vi_audio = AudioSegment.from_file(vi_path)
    en_audio = AudioSegment.from_file(en_path)
    silence = AudioSegment.silent(duration=5000)

    combined = vi_audio + silence + en_audio + silence

    # Clean up temp files
    os.remove(vi_path)
    os.remove(en_path)

    return combined

# Đọc file input.txt
with open("input-02.txt", "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f if line.strip()]

# Kiểm tra định dạng hợp lệ
if len(lines) % 2 != 0:
    raise ValueError("⚠️ File input.txt phải chứa số dòng chẵn (mỗi 2 dòng là 1 cặp song ngữ).")

# Gộp tất cả audio
final_audio = AudioSegment.empty()

for i in range(0, len(lines), 2):
    en = lines[i]
    vi = lines[i + 1]
    print(f"🎤 Processing pair {i//2 + 1}: {vi} / {en}")
    pair_audio = text_to_audio(vi, en, i // 2)
    final_audio += pair_audio

# Xuất file cuối
final_audio.export("final_output.mp3", format="mp3")
print("✅ Done! Saved as final_output.mp3")
