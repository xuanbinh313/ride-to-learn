from pydub import AudioSegment
from gtts import gTTS
import json
import os

pause = AudioSegment.silent(duration=1000)
output = AudioSegment.empty()

with open("output.json", "r", encoding="utf-8") as f:
    timing = json.load(f)["fragments"]

with open("vietnamese.txt", "r", encoding="utf-8") as f:
    vietnamese_lines = [line.strip() for line in f.readlines()]

audio = AudioSegment.from_mp3("english.mp3")

for i, fragment in enumerate(timing):
    start = int(float(fragment["begin"]) * 1000)
    end = int(float(fragment["end"]) * 1000)
    en_clip = audio[start:end]

    vi_text = vietnamese_lines[i]
    tts = gTTS(vi_text, lang="vi")
    tts_path = f"vi_temp_{i}.mp3"
    tts.save(tts_path)
    vi_audio = AudioSegment.from_mp3(tts_path)
    os.remove(tts_path)

    output += vi_audio + pause + en_clip + pause

output.export("output_bilingual.mp3", format="mp3")
print("✅ DONE: output_bilingual.mp3")
