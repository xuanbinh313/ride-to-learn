from pathlib import Path
from unittest import case
import requests
import json
import re
import os
from pydub import AudioSegment
import re
# The path to the audio file you want to transcribe
audio_file_path = "../assets/Actual Test 04.mp3"  # 👈 Change this to your file's path
output_file_path = "output.json"  # 👈 Change this to your desired output file path
output_folder = "output"
output_doc = "output_doc.txt"  # Folder to save individual question audio files
class Toeic:
    def __init__(self, audio_file_path: Path, output_file_path: Path):
        self.audio_file_path = audio_file_path
        self.output_file_path = output_file_path
        self.segments = []
        self.segments_docs = []
        self.delay_duration = 0  # 0 seconds in milliseconds
    def create_doc(self):
        """Create a document with all segments"""
        try:
            with open(output_doc, "w", encoding="utf-8") as doc_file:
                for segment in self.segments_docs:
                    doc_file.write(f"{segment['text'].strip()}\n")
            print(f"[✔] Document created at {output_doc}")
        except Exception as e:
            print(f"[❌] Error creating document: {e}")
    def create_audio_with_delay(self, start_time, end_time, output_path: Path):
        """Create audio segment with 5-second delay before it"""
        try:
            # Create 5-second silence
            delay = AudioSegment.silent(duration=self.delay_duration)
            
            # Load the main audio file
            audio = AudioSegment.from_mp3(self.audio_file_path)
            
            # Extract the specific segment (convert seconds to milliseconds)
            start_ms = int(start_time * 1000)
            end_ms = int(end_time * 1000)
            audio_segment = audio[start_ms:end_ms]
            
            # Combine delay + audio segment
            output_audio = delay + audio_segment
            
            # Export the result
            output_audio.export(output_path, format="mp3")
            print(f"[✔] Exported {output_path} (Duration: {len(output_audio)/1000:.2f}s)")
            
        except Exception as e:
            print(f"[❌] Error creating audio: {e}")

    def find_question_segments(self, question_num, start_index=0):
        """Find segments for a specific question number (1-40)"""
        question_segments = []
        next = start_index
        while next < len(self.segments):
            segment = self.segments[next]
            text = segment['text'].strip()
            if f"Number {question_num}" in text:
                # Find all segments until the next question or end
                i = next
                while i < len(self.segments):
                    current_text = self.segments[i]['text'].strip()
                    # Stop if we find the next question number or have Part 2, 3, or 4 in the text
                    if "Part 2" in current_text or "Part 3" in current_text or "Part 4" in current_text or \
                       current_text.startswith(f"Number {question_num + 1}"):
                        break
                    # Check if the current text is a valid answer option
                    # and the next segment is not a valid answer option
                    # This is a simple heuristic to combine question text with its answer options
                    valid_answers = {"A", "B", "C", "D", "A.", "B.", "C.", "D."}
                    is_valid_answer = current_text in valid_answers and self.segments[i + 1]['text'].strip() not in valid_answers
                    if is_valid_answer:
                        self.segments[i]['text'] = self.segments[i]['text'].strip() + " " + self.segments[i + 1]['text'].strip()
                        self.segments[i]['end'] = self.segments[i + 1]['end']
                        question_segments.append(self.segments[i])
                        i += 2
                    else:
                        question_segments.append(self.segments[i])
                        i += 1
                break
            next += 1
        if not question_segments:
            print(f"[⚠️] Question {question_num} not found in segments")
        else:
            print(f"[✔] Found {len(question_segments)} segments for Question {question_num}")
        
        return question_segments, next

    def find_question_group_segments(self, question_num, start_index=0):
        """Find segments for question groups (41-100, groups of 3)"""
        end_question = question_num + 2
        pattern = f"Questions {question_num}"

        question_segments = []
        next = start_index
        while next < len(self.segments):
            segment = self.segments[next]
            text = segment['text'].strip()
            if pattern in text:
                # Find all segments until the next question or end
                i = next
                while i < len(self.segments):
                    current_text = self.segments[i]['text'].strip()
                    next_pattern = f"Questions {end_question + 1}"
                    # Stop if we find the next question number or have Part 3, 4 in the text
                    if "Part 3" in current_text or "Part 4" in current_text or \
                       current_text.startswith(next_pattern):
                        break
                    question_segments.append(self.segments[i])
                    i += 1
                break
            next += 1
        if not question_segments:
            print(f"[⚠️] Question {question_num} not found in segments")
        else:
            print(f"[✔] Found {len(question_segments)} segments for Question {question_num}")
        
        return question_segments, next
        
    def process_individual_questions(self, allow_make_audio=True):
        """Process questions 1-40 individually"""
        print("🔄 Processing individual questions (1-40)...")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        next_segment = 0
        for question_num in range(1, 41):
            segments, next_segment = self.find_question_segments(question_num, next_segment)
            self.segments_docs.extend(segments)
            print(f"question {question_num} ---------------------")
            # for segment in segments:
            #     print(f"  - {segment['text'].strip()} (Start: {segment['start']}s, End: {segment['end']}s)")
            if not allow_make_audio:
                continue
            if segments:
                # Get start time from first segment and end time from last segment
                start_time = segments[0]['start']
                end_time = segments[-1]['end']
                
                # Create output filename
                output_path = Path(output_folder) / f"{question_num:02d}.mp3"
                
                # Create audio with delay
                self.create_audio_with_delay(start_time, end_time, output_path)
                
                print(f"   Question {question_num}: {start_time:.2f}s - {end_time:.2f}s")
            else:
                print(f"   [⚠️] Question {question_num} not found")

    def process_question_groups(self, allow_make_audio=True):
        """Process questions 41-100 in groups of 3"""
        print("🔄 Processing question groups (41-100)...")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        next_segment = 0
        for question_num in range(41, 101, 3):
            segments, next_segment = self.find_question_group_segments(question_num, next_segment)
            self.segments_docs.extend(segments)
            # print(f"Questions {question_num} ---------------------")
            # for segment in segments:
            #     print(f"  - {segment['text'].strip()} (Start: {segment['start']}s, End: {segment['end']}s)")
            if not allow_make_audio:
                continue
            if segments:
                # Get start time from first segment and end time from last segment
                start_time = segments[0]['start']
                end_time = segments[-1]['end']
                end_question = question_num + 2
                # Create output filename
                output_path = Path(output_folder) / f"{question_num:02d}-{end_question:02d}.mp3"
                # Create audio with delay
                self.create_audio_with_delay(start_time, end_time, output_path)
                print(f"   Questions {question_num}-{end_question}: {start_time:.2f}s - {end_time:.2f}s")
            else:
                print(f"   [⚠️] Questions {question_num}-{question_num+2} not found")
    
    def create_delayed_audio_for_each_sentence(self):
        """Create audio files with 5-second delays for each sentence"""
        print("🔄 Processing all segments with delays...")
        
        # Create output directory if it doesn't exist
        sentence_folder = Path(output_folder) / "sentences"
        os.makedirs(sentence_folder, exist_ok=True)
        
        for i, segment in enumerate(self.segments):
            start_time = segment['start']
            end_time = segment['end']
            text = segment['text'].strip()
            
            # Create safe filename from text (first 50 chars)
            safe_text = re.sub(r'[^\w\s-]', '', text)[:50]
            safe_text = re.sub(r'[-\s]+', '_', safe_text)
            
            output_path = sentence_folder / f"segment_{i+1:03d}_{safe_text}.mp3"
            
            # Create audio with delay
            self.create_audio_with_delay(start_time, end_time, output_path)
            
            if i < 10:  # Show first 10 for brevity
                print(f"   Segment {i+1}: {start_time:.2f}s - {end_time:.2f}s - '{text[:30]}...'")
            elif i == 10:
                print(f"   ... (processing remaining {len(self.segments)-10} segments)")
    
    def process_segments(self):
        """Main processing function"""
        try:
            # Read JSON file and load segments
            with open(self.output_file_path, "r") as json_file:
                response_data = json.load(json_file)
                self.segments = response_data.get('segments', [])
                
            print(f"📊 Loaded {len(self.segments)} segments from {self.output_file_path}")
            
            if not self.segments:
                print("❌ No segments found in the JSON file")
                return
            
            print("\nChoose processing mode:")
            print("1. Process individual questions (1-40)")
            print("2. Process question groups (41-100)")
            print("3. Process all sentences with delays")
            print("4. Process save docs all (1-40 + 41-100)")
            
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == "1":
                self.process_individual_questions()
            elif choice == "2":
                self.process_question_groups()
            elif choice == "3":
                self.create_delayed_audio_for_each_sentence()
            elif choice == "4":
                self.process_individual_questions(False)
                self.process_question_groups(False)
                self.create_doc()
            else:
                print("Invalid choice. Processing all sentences with delays...")
                self.create_delayed_audio_for_each_sentence()
                
        except FileNotFoundError:
            print(f"❌ ERROR: The file was not found at '{self.output_file_path}'")
        except json.JSONDecodeError as e:
            print(f"❌ ERROR: Invalid JSON format. Details: {e}")
        except Exception as e:
            print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    toeic = Toeic(audio_file_path, output_file_path)
    toeic.process_segments()