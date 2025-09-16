import subprocess

input_file = "assets/Socializing and Parties.mp4"
output_file = "assets/Socializing and Parties.wav"

# Run ffmpeg command
subprocess.run([
    "ffmpeg", "-i", input_file,
    "-vn",          # remove video
    "-ab", "192k",  # bitrate
    "-ar", "44100", # sample rate
    "-y",           # overwrite output file
    output_file
])
