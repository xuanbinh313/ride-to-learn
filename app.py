import sys, os, json, sqlite3
from pathlib import Path
from gtts import gTTS
from pydub import AudioSegment
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QListWidgetItem, QMessageBox, QListWidget
)
from PySide6.QtCore import Qt

from main import split_raw_to_english_vietnamese

DB_PATH = "db.sqlite3"

class AudioApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎧 Audio JSON Exporter")
        self.setMinimumSize(600, 500)

        self.conn = sqlite3.connect(DB_PATH)
        self.create_table()

        self.layout = QVBoxLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter a record name")
        self.layout.addWidget(QLabel("📝 Record Name:"))
        self.layout.addWidget(self.name_input)

        self.json_button = QPushButton("📂 Select JSON File")
        self.json_button.clicked.connect(self.load_json_file)
        self.layout.addWidget(self.json_button)

        self.mp3_button = QPushButton("🎵 Select MP3 File")
        self.mp3_button.clicked.connect(self.load_mp3_file)

        self.layout.addWidget(self.mp3_button)
        self.vn_button = QPushButton("📥 Select Vietnamese TXT")
        self.vn_button.clicked.connect(self.import_vn_texts)
        self.layout.addWidget(self.vn_button)

        self.save_button = QPushButton("💾 Save Record")
        self.save_button.clicked.connect(self.save_record)
        self.layout.addWidget(self.save_button)

        

        self.layout.addWidget(QLabel("✅ Select records to export:"))
        self.list_widget = QListWidget()
        self.layout.addWidget(self.list_widget)

        self.export_button = QPushButton("📤 Export Selected Records to Audio")
        self.export_button.clicked.connect(self.export_selected)
        self.layout.addWidget(self.export_button)

        self.setLayout(self.layout)

        self.current_json_path = None
        self.current_mp3_path = None
        self.current_vn_path = None
        self.vn_texts = []


        self.load_saved_records()

    def create_table(self):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                json TEXT,
                mp3_path TEXT,
                vn_texts TEXT
            )
        """)
        self.conn.commit()

    def load_json_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select JSON File", filter="*.json")
        if file_path:
            self.current_json_path = Path(file_path)
            self.json_button.setText(f"✅ {self.current_json_path.name}")

    def load_mp3_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select MP3 File", filter="*.mp3")
        if file_path:
            self.current_mp3_path = Path(file_path)
            self.mp3_button.setText(f"🎵 {Path(file_path).name}")
    def import_vn_texts(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Vietnamese TXT", filter="*.txt")
        if file_path:
            self.current_vn_path = Path(file_path)
            self.vn_button.setText(f"✅ {self.current_vn_path.name}")

        _, self.vn_texts = split_raw_to_english_vietnamese()


    def save_record(self):
        name = self.name_input.text().strip()
        if not name or not self.current_json_path or not self.current_mp3_path:
            QMessageBox.warning(self, "Missing Info", "Please enter name, select JSON and MP3.")
            return

        try:
            with open(self.current_json_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"JSON read failed: {e}")
            return

        relative_mp3 = os.path.relpath(self.current_mp3_path.resolve(), start=os.getcwd())

        cur = self.conn.cursor()
        try:
            cur.execute("INSERT INTO records (name, json, mp3_path, vn_texts) VALUES (?, ?, ?, ?)",
                        (name, json.dumps(json_data), relative_mp3, json.dumps(self.vn_texts, ensure_ascii=False)))
            self.conn.commit()
            self.load_saved_records()
            QMessageBox.information(self, "Saved", f"Saved '{name}' to database.")
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Duplicate", f"'{name}' already exists.")

    def load_saved_records(self):
        self.list_widget.clear()
        cur = self.conn.cursor()
        cur.execute("SELECT name FROM records ORDER BY id DESC")
        for (name,) in cur.fetchall():
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.list_widget.addItem(item)

    

    def export_selected(self):
        export_dir = QFileDialog.getExistingDirectory(self, "Select Export Folder")
        if not export_dir:
            return

        cur = self.conn.cursor()

        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() != Qt.Checked:
                continue

            name = item.text()
            cur.execute("SELECT json, mp3_path, vn_texts FROM records WHERE name=?", (name,))
            row = cur.fetchone()
            if not row:
                continue

            json_data, mp3_path, vn_texts_raw = row
            fragments = json.loads(json_data)["fragments"]
            mp3_path = Path(mp3_path)
            vn_texts = json.loads(vn_texts_raw)

            if not mp3_path.exists():
                QMessageBox.warning(self, "Missing MP3", f"{mp3_path} not found.")
                continue
            print(f"[✔] Exporting {name}...")
            try:
                self.create_audio(mp3_path, fragments, vn_texts, Path(export_dir) / f"{name}-output.mp3")
            except Exception as e:
                QMessageBox.warning(self, "Export Error", f"Failed to export '{name}': {e}")
                continue

        QMessageBox.information(self, "Done", "✅ Export complete.")

    def create_audio(self, mp3_path: Path, fragments, vn_texts, output_path: Path):
        delay = AudioSegment.silent(duration=5000)
        audio = AudioSegment.from_mp3(mp3_path)
        output = AudioSegment.silent(duration=0)
        for i, vi_text in enumerate(vn_texts):
            if i == 0:
                continue
            start = float(fragments[i+1]["begin"]) * 1000
            end = float(fragments[i+1]["end"]) * 1000
            en_clip = audio[start:end]

            vi_text = vn_texts[i - 1] if i - 1 < len(vn_texts) else ""
            print(f"{vi_text}")
            tts = gTTS(vi_text, lang="vi")
            tts_path = f"vi_temp_{i}.mp3"
            tts.save(tts_path)
            vi_audio = AudioSegment.from_mp3(tts_path)
            os.remove(tts_path)

            output += vi_audio + delay + en_clip + delay

        output.export(output_path, format="mp3")
        print(f"[✔] Exported {output_path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = AudioApp()
    win.show()
    sys.exit(app.exec())
