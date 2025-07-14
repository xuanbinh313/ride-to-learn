import re
import os
import json
import subprocess
from gtts import gTTS
from pydub import AudioSegment

VIETNAMESE_CHARS = "àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ"

def is_vietnamese_line(line):
    return any(char in VIETNAMESE_CHARS for char in line.lower())

def is_title_line(line):
    return re.match(r"^\d{2,3}([–-]\d{2,3})?(\.| refer)", line.strip()) is not None

def normalize_title(line):
    if re.match(r"^\d{2,3}-\d{2,3}", line):
        a, b = line.split("-")
        return f"{a}-{b}", f"questions {a} to {b} refer to the following advertisement"
    number = re.match(r"^(\d{2,3})", line.strip())
    return number.group(1), None

def split_into_sections(raw_path="raw.txt"):
    with open(raw_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    sections = []
    current_section = {"id": None, "en": [], "vn": []}

    for line in lines:
        if is_title_line(line):
            if current_section["id"]:
                sections.append(current_section)
            sid, en_title = normalize_title(line)
            current_section = {"id": sid, "en": [], "vn": []}
            if en_title:
                current_section["en"].append(en_title)
        elif is_vietnamese_line(line):
            current_section["vn"].append(line)
        else:
            current_section["en"].append(line)

    if current_section["id"]:
        sections.append(current_section)
    print(f"[✔] Found {len(sections)} sections in {raw_path}")
    return sections


def run_aeneas(audio_path, text_path, output_json):
    cmd = [
        "python", "-m", "aeneas.tools.execute_task",
        audio_path,
        text_path,
        "task_language=eng|os_task_file_format=json|is_text_type=plain",
        output_json,
    ]
    subprocess.run(cmd, check=True)
    os.remove(text_path)
    print(f"[✔] Aeneas alignment complete: {output_json}")


def create_combined_audio(vn_texts, en_audio_path, json_path, out_path, time_stop=0):
    delay = AudioSegment.silent(duration=5000)
    output = AudioSegment.empty()

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    full_en_audio = AudioSegment.from_mp3(en_audio_path)
    if time_stop > 0:
        data["fragments"][-1]["end"] = str(time_stop)

    for i, fragment in enumerate(data["fragments"]):
        if i == 0:
            continue  # skip possible empty fragment
        start = float(fragment["begin"]) * 1000
        end = float(fragment["end"]) * 1000
        print(f"🎧 Fragment {i}: {start}–{end}ms")

        en_clip = full_en_audio[start:end]
        vi_text = vn_texts[i - 1] if i - 1 < len(vn_texts) else "[MISSING VI]"

        tts = gTTS(vi_text, lang="vi")
        tts_path = f"vi_temp_{i}.mp3"
        tts.save(tts_path)
        vi_audio = AudioSegment.from_mp3(tts_path)
        os.remove(tts_path)

        output += vi_audio + delay + en_clip + delay

    output.export(out_path, format="mp3")
    print(f"[✔] Final output: {out_path}")


if __name__ == "__main__":
    sections = split_into_sections("raw.txt")

    for section in sections:
        sid = section["id"]
        en_lines = section["en"]
        vn_lines = section["vn"]

        print(f"\n🔹 Processing section: {sid} ({len(en_lines)} EN, {len(vn_lines)} VI)")

        audio_file = f"{sid}.mp3"
        if not os.path.exists(audio_file):
            print(f"⚠️ Audio file missing: {audio_file} — skipping")
            continue

        temp_txt = f"{sid}_temp.txt"
        output_json = f"{sid}_output.json"
        output_mp3 = f"{sid}_output.mp3"

        with open(temp_txt, "w", encoding="utf-8") as f:
            f.write("\n".join(en_lines))

        run_aeneas(audio_path=audio_file, text_path=temp_txt, output_json=output_json)
        create_combined_audio(vn_texts=vn_lines, en_audio_path=audio_file, json_path=output_json, out_path=output_mp3)
