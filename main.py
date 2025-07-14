import re

VIETNAMESE_CHARS = "àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ"


def is_vietnamese_line(line):
    return any(char in VIETNAMESE_CHARS for char in line.lower())


def is_question_number_or_title(line):
    stripped = line.strip()
    return (
        re.match(r"^\*{0,2}\d+([–-]\d+)?(.*?)\*{0,2}$", stripped) or stripped.isdigit()
    )


def split_raw_to_english_vietnamese(input_path="raw.txt", en_path="temp.txt"):
    with open(input_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    en_lines = []
    vn_lines = []

    for line in lines:
        if re.match(r"^\d{2,3}-\d{2,3}", line):
            raw_title = line.replace("-", " to ")
            en_lines.append(f"questions {raw_title}")
        elif is_vietnamese_line(line):
            vn_lines.append(line)
        else:
            en_lines.append(line)

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
        
    for i, fragment in enumerate(data["fragments"]):
        if i == 0:
            continue  # Skip the first fragment if it's not needed
        start = float(fragment["begin"]) * 1000
        end = float(fragment["end"]) * 1000
        print(f"Processing fragment: {start} to {end}")
        en_clip = full_en_audio[start:end]
        vi_text = vn_texts[i - 1]
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
        "python",
        "-m",
        "aeneas.tools.execute_task",
        audio_path,
        text_path,
        "task_language=eng|os_task_file_format=json|is_text_type=plain",
        output_json,
    ]
    subprocess.run(cmd, check=True)
    os.remove(text_path)  # Clean up the temporary text file
    print("[✔] Aeneas alignment complete:", output_json)


if __name__ == "__main__":
    eng_lines, vn_lines = split_raw_to_english_vietnamese()

    # run aeneas to get alignment
    run_aeneas(audio_path="89-91.mp3")
    create_combined_audio(en_audio_path="89-91.mp3", vn_texts=vn_lines,time_stop=52)
