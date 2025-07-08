from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QFileDialog, QLineEdit, QLabel, QHBoxLayout, QMessageBox
)
from pydub import AudioSegment
from gtts import gTTS
import sys, json, os

class ToeicEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎧 TOEIC Audio Editor")
        self.resize(800, 600)

        layout = QVBoxLayout()

        # Chọn file MP3
        mp3_layout = QHBoxLayout()
        mp3_layout.addWidget(QLabel("🎵 File MP3:"))
        self.mp3_input = QLineEdit()
        self.btn_select_mp3 = QPushButton("Chọn file")
        self.btn_select_mp3.clicked.connect(self.select_mp3)
        mp3_layout.addWidget(self.mp3_input)
        mp3_layout.addWidget(self.btn_select_mp3)
        layout.addLayout(mp3_layout)

        # Tên bài
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Tên bài (name):"))
        self.name_input = QLineEdit("toeic-audio")
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # Bảng nhập đoạn
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Start", "End", "Translation", "Pause (s)"])
        layout.addWidget(self.table)

        # Nút thêm dòng
        btn_add = QPushButton("➕ Thêm dòng")
        btn_add.clicked.connect(self.add_row)
        layout.addWidget(btn_add)

        # Nút xuất JSON và tạo audio
        btn_row = QHBoxLayout()
        btn_export = QPushButton("💾 Xuất JSON")
        btn_export.clicked.connect(self.export_json)
        btn_process = QPushButton("🎧 Tạo file audio")
        btn_process.clicked.connect(self.process_audio)
        btn_row.addWidget(btn_export)
        btn_row.addWidget(btn_process)
        layout.addLayout(btn_row)

        self.setLayout(layout)

    def add_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        for col in range(4):
            self.table.setItem(row, col, QTableWidgetItem(""))

    def select_mp3(self):
        file, _ = QFileDialog.getOpenFileName(self, "Chọn file MP3", "", "MP3 Files (*.mp3)")
        if file:
            self.mp3_input.setText(file)

    def get_segments(self):
        children = []
        for row in range(self.table.rowCount()):
            try:
                start = self.table.item(row, 0).text()
                end = self.table.item(row, 1).text()
                trans = self.table.item(row, 2).text()
                pause = float(self.table.item(row, 3).text())
                children.append({
                    "start": start,
                    "end": end,
                    "translation": trans,
                    "pause_after": pause
                })
            except:
                raise Exception(f"Dòng {row+1} có dữ liệu không hợp lệ")
        return [{
            "name": self.name_input.text(),
            "children": children
        }]

    def export_json(self):
        try:
            segments = self.get_segments()
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", str(e))
            return

        save_path, _ = QFileDialog.getSaveFileName(self, "Lưu JSON", f"{segments[0]['name']}.json", "JSON Files (*.json)")
        if save_path:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(segments, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "✅ Thành công", f"Đã lưu JSON tại:\n{save_path}")

    def time_to_ms(self, tstr):
        try:
            parts = tstr.split(":")
            minutes = int(parts[0])
            seconds, ms = map(float, parts[1].split("."))
            return int((minutes * 60 + seconds + ms / 1000) * 1000)
        except:
            raise Exception(f"Định dạng thời gian không hợp lệ: {tstr}")

    def process_audio(self):
        mp3_path = self.mp3_input.text().strip()
        if not os.path.isfile(mp3_path):
            QMessageBox.warning(self, "Lỗi", "File MP3 không tồn tại")
            return

        try:
            segments = self.get_segments()
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", str(e))
            return

        try:
            original = AudioSegment.from_mp3(mp3_path)
            final_audio = AudioSegment.silent(duration=0)

            for i, seg in enumerate(segments[0]["children"]):
                start = self.time_to_ms(seg["start"])
                end = self.time_to_ms(seg["end"])
                clip = original[start:end]

                tts = gTTS(text=seg["translation"], lang="vi")
                tts_path = f"tts_temp_{i}.mp3"
                tts.save(tts_path)
                tts_audio = AudioSegment.from_mp3(tts_path)
                os.remove(tts_path)

                silence = AudioSegment.silent(duration=seg["pause_after"] * 1000)
                final_audio += tts_audio + silence + clip + silence

            out_path = mp3_path.replace(".mp3", "-output.mp3")
            final_audio.export(out_path, format="mp3")
            QMessageBox.information(self, "🎉 Thành công", f"Đã tạo file: {out_path}")
        except Exception as e:
            QMessageBox.critical(self, "❌ Lỗi xử lý", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ToeicEditor()
    win.show()
    sys.exit(app.exec())
