import sys
import os
import re
import json
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QListWidget, QListWidgetItem, QCheckBox, QLabel, QComboBox
)
from PySide6.QtCore import Qt
from gtts import gTTS
from pydub import AudioSegment

REVIEW_INTERVALS = [1, 3, 7, 30]  # days

class FlashcardItem(QWidget):
    def __init__(self, vi, en, state_data=None):
        super().__init__()
        self.vi = vi
        self.en = en
        self.status = state_data.get("status", "unseen") if state_data else "unseen"
        self.step = state_data.get("step", 0)
        self.next_review = state_data.get("next_review")

        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        self.checkbox = QCheckBox()
        self.label = QLabel(f"<b>VI:</b> {vi}<br><b>EN:</b> {en}")
        self.label.setWordWrap(True)

        self.again_button = QPushButton("Again")
        self.ok_button = QPushButton("OK")

        self.again_button.clicked.connect(self.mark_again)
        self.ok_button.clicked.connect(self.mark_ok)

        layout.addWidget(self.checkbox)
        layout.addWidget(self.label, 1)
        layout.addWidget(self.again_button)
        layout.addWidget(self.ok_button)

        self.setLayout(layout)
        self.apply_status_color()

    def apply_status_color(self):
        if self.status == "again":
            self.setStyleSheet("background-color: #ffe0e0")
        elif self.status == "ok":
            self.setStyleSheet("background-color: #e0ffe0")
        else:
            self.setStyleSheet("")

    def mark_again(self):
        self.status = "again"
        self.step = 0
        self.next_review = (datetime.now() + timedelta(days=REVIEW_INTERVALS[0])).isoformat()
        self.apply_status_color()

    def mark_ok(self):
        self.status = "ok"
        self.step = min(self.step + 1, len(REVIEW_INTERVALS) - 1)
        self.next_review = (datetime.now() + timedelta(days=REVIEW_INTERVALS[self.step])).isoformat()
        self.apply_status_color()

    def is_checked(self):
        return self.checkbox.isChecked()

class FlashcardApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("English Speaking Flashcards with SRS")
        self.resize(800, 600)
        self.state = {}
        self.layout = QVBoxLayout()

        self.filter_box = QComboBox()
        self.filter_box.addItems(["Tất cả", "Chưa học", "Again", "OK"])
        self.filter_box.currentTextChanged.connect(self.refresh_display)
        self.layout.addWidget(self.filter_box)

        self.card_list = QListWidget()
        self.layout.addWidget(self.card_list)

        button_row = QHBoxLayout()
        self.load_button = QPushButton("📂 Tải file TXT")
        self.load_button.clicked.connect(self.load_file)

        self.load_schedule_button = QPushButton("📤 Load Schedule")
        self.load_schedule_button.clicked.connect(self.load_schedule_from_file)

        self.save_schedule_button = QPushButton("💾 Save Schedule")
        self.save_schedule_button.clicked.connect(self.save_schedule_to_file)

        self.generate_button = QPushButton("🎧 Tạo file MP3")
        self.generate_button.clicked.connect(self.generate_mp3)

        button_row.addWidget(self.load_button)
        button_row.addWidget(self.load_schedule_button)
        button_row.addWidget(self.save_schedule_button)
        button_row.addWidget(self.generate_button)

        self.layout.addLayout(button_row)
        self.setLayout(self.layout)

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn file TXT", "", "Text Files (*.txt)")
        if file_path:
            self.card_list.clear()
            self.state.clear()
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    self.parse_and_add_flashcards(line.strip())
            self.refresh_display()

    def load_schedule_from_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn file JSON", "", "JSON Files (*.json)")
        if file_path:
            self.card_list.clear()
            with open(file_path, "r", encoding="utf-8") as f:
                self.state = json.load(f)
            for key, value in self.state.items():
                if "||" in key:
                    vi, en = key.split("||")
                    self.add_flashcard(vi.strip(), en.strip())
            self.refresh_display()

    def save_schedule_to_file(self):
        for i in range(self.card_list.count()):
            item = self.card_list.item(i)
            widget = self.card_list.itemWidget(item)
            key = f"{widget.vi}||{widget.en}"
            self.state[key] = {
                "status": widget.status,
                "step": widget.step,
                "next_review": widget.next_review
            }

        file_path, _ = QFileDialog.getSaveFileName(self, "Lưu lịch học", "", "JSON Files (*.json)")
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)

    def parse_and_add_flashcards(self, line):
        pattern = re.compile(r"(?:\(\w\)\s*)?(.*?)\s*\{\{c1::(.*?)\}\}")
        matches = pattern.findall(line)
        for vi, en in matches:
            vi, en = vi.strip(), en.strip()
            if vi and en:
                self.add_flashcard(vi, en)

    def add_flashcard(self, vi, en):
        key = f"{vi}||{en}"
        state_data = self.state.get(key, {"status": "unseen", "step": 0, "next_review": None})
        item_widget = FlashcardItem(vi, en, state_data)
        item = QListWidgetItem(self.card_list)
        item.setSizeHint(item_widget.sizeHint())
        self.card_list.addItem(item)
        self.card_list.setItemWidget(item, item_widget)

    def refresh_display(self):
        filter_text = self.filter_box.currentText().lower()
        for i in range(self.card_list.count()):
            item = self.card_list.item(i)
            widget = self.card_list.itemWidget(item)
            should_show = (
                filter_text == "tất cả" or
                (filter_text == "again" and widget.status == "again") or
                (filter_text == "ok" and widget.status == "ok") or
                (filter_text == "chưa học" and widget.status == "unseen")
            )
            item.setHidden(not should_show)

    def generate_mp3(self):
        silence = AudioSegment.silent(duration=5000)
        combined = AudioSegment.empty()
        os.makedirs("tmp", exist_ok=True)

        for i in range(self.card_list.count()):
            item = self.card_list.item(i)
            widget = self.card_list.itemWidget(item)
            if widget.is_checked():
                vi, en = widget.vi, widget.en
                try:
                    vi_tts = gTTS(vi, lang="vi")
                    en_tts = gTTS(en, lang="en")
                    vi_path = f"tmp/vi_{i}.mp3"
                    en_path = f"tmp/en_{i}.mp3"
                    vi_tts.save(vi_path)
                    en_tts.save(en_path)
                    vi_seg = AudioSegment.from_file(vi_path)
                    en_seg = AudioSegment.from_file(en_path)
                    combined += vi_seg + silence + en_seg + silence
                except Exception as e:
                    print(f"Lỗi xử lý câu {i}: {e}")

        if len(combined) > 0:
            now = datetime.now().strftime("%Y%m%d-%H%M%S")
            output_path = f"flashcards_output_{now}.mp3"
            combined.export(output_path, format="mp3")
            print(f"✅ File '{output_path}' đã được tạo thành công!")

        for file in os.listdir("tmp"):
            os.remove(os.path.join("tmp", file))
        os.rmdir("tmp")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FlashcardApp()
    window.show()
    sys.exit(app.exec())