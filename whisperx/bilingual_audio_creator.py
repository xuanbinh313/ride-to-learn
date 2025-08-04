import csv
import json
import re
from pathlib import Path
from pydub import AudioSegment
from gtts import gTTS
import tempfile
import os

class BilingualAudioCreator:
    def __init__(self, learning_file, output_json, audio_file, output_folder="bilingual_output"):
        self.learning_file = learning_file
        self.output_json = output_json
        self.audio_file = audio_file
        self.output_folder = output_folder
        self.segments = []
        self.delay_duration = 5000  # 5 seconds in milliseconds
        
    def load_segments(self):
        """Load segments from output.json"""
        try:
            # with open(self.output_json, 'r', encoding='utf-8') as f:
            #     data = json.load(f)
            #     self.segments = data.get('segments', [])
            #     print(f"📊 Loaded {len(self.segments)} segments from {self.output_json}")
            with open(self.output_json,'r', encoding='utf-8') as csvFile:
                reader = csv.DictReader(csvFile)
                for row in reader:
                    self.segments.append(row)
        except Exception as e:
            print(f"❌ Error loading segments: {e}")
            return False
        return True
    
    def parse_learning_file(self):
        """Parse learning.txt to extract Vietnamese-English pairs"""
        pairs = []
        try:
            with open(self.learning_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            current_pair = {}
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check if this line contains English text (has English characters and common English words)
                if self.is_english_line(line):
                    if 'vietnamese' in current_pair:
                        current_pair['english'] = line
                        pairs.append(current_pair.copy())
                        current_pair = {}
                    else:
                        current_pair['english'] = line
                else:
                    # Assume it's Vietnamese
                    current_pair['vietnamese'] = line
            
            print(f"📝 Found {len(pairs)} Vietnamese-English pairs")
            return pairs
            
        except Exception as e:
            print(f"❌ Error parsing learning file: {e}")
            return []
    
    def is_english_line(self, line):
        """Check if a line is likely English text"""
        # Simple heuristic: check for common English words and patterns
        english_indicators = ['the', 'and', 'to', 'of', 'a', 'in', 'is', 'you', 'that', 'it', 'he', 'was', 'for', 'on', 'are', 'as', 'with', 'his', 'they', 'i', 'at', 'be', 'this', 'have', 'from', 'or', 'one', 'had', 'by', 'word', 'but', 'not', 'what', 'all', 'were', 'we', 'when', 'your', 'can', 'said', 'there', 'each', 'which', 'she', 'do', 'how', 'their', 'if', 'will', 'up', 'other', 'about', 'out', 'many', 'then', 'them', 'these', 'so', 'some', 'her', 'would', 'make', 'like', 'into', 'him', 'has', 'two', 'more', 'go', 'no', 'way', 'could', 'my', 'than', 'first', 'been', 'call', 'who', 'its', 'now', 'find', 'long', 'down', 'day', 'did', 'get', 'come', 'made', 'may', 'part']
        
        line_lower = line.lower()
        word_count = 0
        words = re.findall(r'\b\w+\b', line_lower)
        
        for word in words:
            if word in english_indicators:
                word_count += 1
        
        # If more than 20% of words are common English words, consider it English
        return len(words) > 0 and (word_count / len(words)) > 0.2
    
    def find_audio_segment(self, english_text):
        """Find matching audio segment for English text"""
        # Clean the text for better matching
        clean_text = re.sub(r'[^\w\s]', '', english_text.lower())
        words = clean_text.split()
        
        best_match = None
        best_score = 0
        
        for segment in self.segments:
            segment_text = re.sub(r'[^\w\s]', '', segment['text'].lower())
            
            # Calculate overlap score
            segment_words = set(segment_text.split())
            text_words = set(words)
            
            if len(text_words) == 0:
                continue
                
            overlap = len(segment_words.intersection(text_words))
            score = overlap / len(text_words)
            
            # Also check if the segment contains most of the target text
            if score > best_score and score > 0.6:  # At least 60% word overlap
                best_match = segment
                best_score = score
        
        return best_match
    
    def create_tts_audio(self, text, output_path):
        """Create TTS audio for Vietnamese text using gTTS"""
        try:
            # Create gTTS object for Vietnamese
            tts = gTTS(text=text, lang='vi', slow=False)
            
            # Use temporary file for TTS output
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Save TTS audio to temporary file
            tts.save(temp_path)
            
            # Load as AudioSegment
            tts_audio = AudioSegment.from_mp3(temp_path)
            
            # Clean up temp file
            os.unlink(temp_path)
            
            return tts_audio
            
        except Exception as e:
            print(f"❌ Error creating TTS audio: {e}")
            return None
    
    def create_bilingual_audio(self, vietnamese_text, english_segment, output_path):
        """Create audio with format: Vietnamese TTS + 5s delay + English audio + 5s delay"""
        try:
            # Create delays
            delay = AudioSegment.silent(duration=self.delay_duration)
            
            # Create Vietnamese TTS audio
            print(f"🔊 Generating TTS for: {vietnamese_text[:50]}...")
            vietnamese_audio = self.create_tts_audio(vietnamese_text, None)
            
            if vietnamese_audio is None:
                print("❌ Failed to create Vietnamese TTS audio")
                return False
            
            # Extract English audio segment
            main_audio = AudioSegment.from_mp3(self.audio_file)
            start_ms = int(english_segment['start'] * 1000)
            end_ms = int(english_segment['end'] * 1000)
            english_audio = main_audio[start_ms:end_ms]
            
            # Combine: Vietnamese TTS + 5s delay + English audio + 5s delay
            final_audio = vietnamese_audio + delay + english_audio + delay
            
            # Export
            final_audio.export(output_path, format="mp3")
            
            duration = len(final_audio) / 1000
            print(f"✅ Created: {output_path} (Duration: {duration:.2f}s)")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating bilingual audio: {e}")
            return False
    
    def merge_all_audio_files(self):
        """Merge all created MP3 files into one single file and remove individual files"""
        try:
            # Get all MP3 files from output folder
            output_path = Path(self.output_folder)
            mp3_files = sorted(list(output_path.glob("pair_*.mp3")))
            
            if not mp3_files:
                print("❌ No MP3 files found to merge")
                return False
            
            print(f"🔄 Merging {len(mp3_files)} audio files...")
            
            # Start with empty audio
            merged_audio = AudioSegment.empty()
            
            # Add each file to the merged audio
            for i, mp3_file in enumerate(mp3_files, 1):
                print(f"   Adding file {i}/{len(mp3_files)}: {mp3_file.name}")
                audio_segment = AudioSegment.from_mp3(mp3_file)
                merged_audio += audio_segment
            
            # Export merged file
            merged_output_path = output_path / "62-64.mp3"
            merged_audio.export(merged_output_path, format="mp3")
            
            total_duration = len(merged_audio) / 1000
            print(f"✅ Successfully merged all files into: {merged_output_path}")
            print(f"📊 Total duration: {total_duration:.2f} seconds ({total_duration/60:.2f} minutes)")
            
            # Remove individual MP3 files
            print(f"🗑️  Cleaning up individual files...")
            for mp3_file in mp3_files:
                try:
                    mp3_file.unlink()
                    print(f"   Deleted: {mp3_file.name}")
                except Exception as e:
                    print(f"   ⚠️ Could not delete {mp3_file.name}: {e}")
            
            print(f"✅ Cleanup complete. Only merged file remains.")
            
            return True
            
        except Exception as e:
            print(f"❌ Error merging audio files: {e}")
            return False

    def process_all_pairs(self):
        """Process all Vietnamese-English pairs"""
        # Load segments
        if not self.load_segments():
            return
        
        # Parse learning file
        pairs = self.parse_learning_file()
        if not pairs:
            return
        
        # Create output directory
        os.makedirs(self.output_folder, exist_ok=True)
        
        success_count = 0
        
        for i, pair in enumerate(pairs, 1):
            vietnamese_text = pair.get('vietnamese', '')
            english_text = pair.get('english', '')
            
            if not vietnamese_text or not english_text:
                print(f"⚠️ Skipping incomplete pair {i}")
                continue
            
            print(f"\n🔄 Processing pair {i}/{len(pairs)}")
            print(f"   Vietnamese: {vietnamese_text[:50]}...")
            print(f"   English: {english_text[:50]}...")
            
            # Find matching audio segment
            segment = self.find_audio_segment(english_text)
            
            if segment is None:
                print(f"   ❌ No matching audio found for: {english_text[:30]}...")
                continue
            
            print(f"   ✅ Found audio segment: {segment['start']:.2f}s - {segment['end']:.2f}s")
            
            # Create output filename
            safe_name = re.sub(r'[^\w\s-]', '', english_text[:30])
            safe_name = re.sub(r'[-\s]+', '_', safe_name)
            output_path = Path(self.output_folder) / f"pair_{i:03d}_{safe_name}.mp3"
            
            # Create bilingual audio
            if self.create_bilingual_audio(vietnamese_text, segment, output_path):
                success_count += 1
        
        print(f"\n🎉 Successfully created {success_count}/{len(pairs)} bilingual audio files")
        print(f"📁 Output folder: {self.output_folder}")
        
        # Merge all audio files into one
        if success_count > 0:
            print(f"\n🔄 Merging all audio files...")
            self.merge_all_audio_files()

def main():
    # Configuration
    learning_file = "learning.txt"
    output_json = "output.json"
    audio_file = "../assets/Actual Test 04.mp3"
    output_folder = "output"
    
    # Create processor
    processor = BilingualAudioCreator(learning_file, output_json, audio_file, output_folder)
    
    # Process all pairs
    processor.process_all_pairs()

if __name__ == "__main__":
    main()
