from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil, os, json
from audio_utils import process_audio

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload")
async def upload(mp3: UploadFile = File(...), json_str: str = Form(...)):
    mp3_path = os.path.join(UPLOAD_DIR, mp3.filename)
    with open(mp3_path, "wb") as f:
        shutil.copyfileobj(mp3.file, f)

    segments = json.loads(json_str)
    output = process_audio(mp3_path, segments)
    return FileResponse(output, media_type="audio/mp3", filename=os.path.basename(output))
