import yt_dlp

url = "https://www.youtube.com/watch?v=AiAYhUAkHpg"

ydl_opts = {
    "format": "m4a/bestaudio/best",  # try m4a first, fallback to bestaudio
    "outtmpl": "assets/%(title)s.%(ext)s",
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }
    ],
    "compat_opts": ["no-keep-sig"],  # ignore nsig extraction
    "ignoreerrors": True,            # skip if some formats fail
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([url])
