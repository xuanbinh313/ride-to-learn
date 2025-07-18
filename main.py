import re

VIETNAMESE_CHARS = "àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ"


def is_vietnamese_line(line):
    return any(char in VIETNAMESE_CHARS for char in line.lower())


def is_question_number_or_title(line):
    stripped = line.strip()
    return (
        re.match(r"^\*{0,2}\d+([–-]\d+)?(.*?)\*{0,2}$", stripped) or stripped.isdigit()
    )
def is_title_line(line):
    return re.match(r"^\d{2,3}([–-]\d{2,3})?(\.| refer)", line.strip()) is not None

def split_raw_to_english_vietnamese(input_path="raw.txt", en_path="temp.txt",final_line=None):
    with open(input_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    en_lines = []
    vn_lines = []
    for line in lines:
        if is_title_line(line):
            raw_title = re.sub(r"[–—-]", " to ", line)
            en_lines.append(f"questions {raw_title}")
        elif is_vietnamese_line(line):
            vn_lines.append(line)
        else:
            en_lines.append(line)
    if final_line:
        en_lines.append(final_line)
    # Ghi tiếng Anh
    with open(en_path, "w", encoding="utf-8") as f:
        for line in en_lines:
            f.write(line + "\n")
    return en_lines, vn_lines


import json
from gtts import gTTS
from pydub import AudioSegment
import os


def create_combined_audio(
    vn_texts,
    en_audio_path="audio.mp3",
    json_path="output.json",
    out_path="output_final.mp3",
    time_stop=0,
):
    delay = AudioSegment.silent(duration=5000)
    output = AudioSegment.empty()

    # Cắt tiếng Anh theo json
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    full_en_audio = AudioSegment.from_mp3(en_audio_path)
    if time_stop > 0:
        data["fragments"][len(data["fragments"]) - 1]["end"] = str(time_stop)
    fragments = data["fragments"]
    for i, vi_text in enumerate(vn_lines):
        start = float(fragments[i+1]["begin"]) * 1000
        end = float(fragments[i+1]["end"]) * 1000
        print(f"Processing fragment: {start} to {end}")
        print(f"Processing fragment: {vi_text}")
        en_clip = full_en_audio[start:end]
        tts = gTTS(vi_text, lang="vi")
        tts_path = f"vi_temp_{i}.mp3"
        tts.save(tts_path)
        vi_audio = AudioSegment.from_mp3(tts_path)
        os.remove(tts_path)

        output += vi_audio + delay + en_clip + delay

    output.export(out_path, format="mp3")
    print("[✔] Final audio saved to", out_path)


import subprocess


def run_aeneas(audio_path="audio.mp3", text_path="temp.txt", output_json="output.json"):
    cmd = [
        "python3",
        "-m",
        "aeneas.tools.execute_task",
        audio_path,
        text_path,
        "task_language=eng|os_task_file_format=json|is_text_type=plain",
        output_json,
    ]
    subprocess.run(cmd, check=True)
    # os.remove(text_path)  # Clean up the temporary text file
    print("[✔] Aeneas alignment complete:", output_json)


if __name__ == "__main__":
    eng_lines, vn_lines = split_raw_to_english_vietnamese(final_line="number 89 what is the announcement is about?")
    audio_path = "assets/economy/book-05/test03/89-91.mp3"
    # run aeneas to get alignment
    run_aeneas(audio_path=audio_path)
    create_combined_audio(en_audio_path=audio_path, vn_texts=vn_lines, time_stop=52)
