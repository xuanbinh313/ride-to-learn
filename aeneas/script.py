import subprocess
fileName = input("Enter the file name (with extension) located in shared-volume folder (default is audio.mp3): ")
cmd = [
    "python3",
    "-m",
    "aeneas.tools.execute_task",
    f"./assets/{fileName}" or "./assets/audio.mp3",
    f"./assets/raw.txt",
    "task_language=eng|os_task_file_format=json|is_text_type=plain",
    "raw.json",
]

# In log trực tiếp ra terminal khi chạy
subprocess.run(cmd)
