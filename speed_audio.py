import subprocess

def change_tempo_ffmpeg(input_file, output_file, tempo):
    if tempo < 0.5 or tempo > 2.0:
        raise ValueError("Tempo must be between 0.5 and 2.0 for atempo filter")

    cmd = [
        "ffmpeg",
        "-y",  # Ghi đè file output nếu có
        "-i", input_file,
        "-filter:a", f"atempo={tempo}",
        "-vn",
        output_file
    ]

    # Chạy lệnh FFmpeg
    subprocess.run(cmd, check=True)

# Ví dụ sử dụng:
change_tempo_ffmpeg("assets/56-58.mp3", "output_125.mp3", tempo=1.15)