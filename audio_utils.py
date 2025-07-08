from pydub import AudioSegment
from gtts import gTTS
import os
import json

def time_to_ms(tstr: str) -> int:
    parts = tstr.split(":")
    minutes = int(parts[0])
    seconds, ms = map(float, parts[1].split("."))
    return int((minutes * 60 + seconds + ms / 1000) * 1000)

def process_audio(mp3_path: str, segments_data):
    original = AudioSegment.from_mp3(mp3_path)
    final_audio = AudioSegment.silent(duration=0)

    for parent_seg in segments_data:
        for i, seg in enumerate(parent_seg["children"]):
            start_ms = time_to_ms(seg["start"])
            end_ms = time_to_ms(seg["end"])
            clip = original[start_ms:end_ms]

            tts = gTTS(text=seg["translation"], lang="vi")
            tmp = f"tts_tmp_{i}.mp3"
            tts.save(tmp)
            tts_audio = AudioSegment.from_mp3(tmp)
            os.remove(tmp)

            silence = AudioSegment.silent(duration=seg["pause_after"]*1000)
            combined = tts_audio + silence + clip + silence
            final_audio += combined

    output_file = mp3_path.replace(".mp3", "-output.mp3")
    final_audio.export(output_file, format="mp3")
    return output_file
