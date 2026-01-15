import asyncio
import csv
import re
from pathlib import Path
from pydub import AudioSegment
from gtts import gTTS
from googletrans import Translator
import tempfile
import os

current_dir = Path.cwd()


class FastAudioCreator:
    def __init__(self, learning_file, audio_file, output_csv, output_folder="fast_output"):
        self.learning_file = learning_file
        self.audio_file = audio_file
        self.output_csv = output_csv
        self.output_folder = output_folder
        self.delay_duration = 2000  # 2 seconds in milliseconds
        self.translator = Translator()
        self.segments = []
        
    def load_segments(self):
        """Load segments from CSV file"""
        try:
            with open(self.output_csv, 'r', encoding='utf-8') as csvFile:
                reader = csv.DictReader(csvFile)
                for row in reader:
                    self.segments.append(row)
            print(f"📊 Loaded {len(self.segments)} segments from {self.output_csv}")
        except Exception as e:
            print(f"❌ Error loading segments: {e}")
            return False
        return True
    
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
    
    async def translate_text_sync(self, text, dest_language='vi'):
        """Translate text to destination language using Google Translate"""
        try:
            translated = await self.translator.translate(text, dest=dest_language)
            return translated.text
        except Exception as e:
            print(f"❌ Error translating text: {e}")
            return ""
    
    async def parse_learning_file(self):
        """Parse learning.txt to split by --- and translate line by line"""
        groups = []
        current_group = []
        
        try:
            with open(self.learning_file, 'r', encoding='utf-8') as f:
                raw_lines = f.readlines()

            # Clean lines
            lines = [ln.strip() for ln in raw_lines if ln.strip()]

            print(f"📝 Found {len(lines)} lines, processing...")
            
            # Process line by line
            for i, line in enumerate(lines, 1):
                # Check for group separator
                if line == "---":
                    if current_group:
                        groups.append(current_group.copy())
                        current_group = []
                    print(f"   🔸 Group separator detected at line {i}")
                    continue
                
                english_text = line
                print(f"   Translating {i}/{len(lines)}: {english_text[:50]}...")
                vietnamese_text = await self.translate_text_sync(english_text, 'vi')
                
                if vietnamese_text:
                    current_group.append({
                        'english': english_text,
                        'vietnamese': vietnamese_text
                    })
                    print(f"   ✅ Vietnamese: {vietnamese_text[:50]}...")
                else:
                    print(f"   ⚠️ Translation failed for: {english_text[:50]}...")
            
            # Add remaining pairs to last group
            if current_group:
                groups.append(current_group)

            print(f"📝 Successfully created {len(groups)} groups")
            return groups

        except Exception as e:
            print(f"❌ Error parsing learning file: {e}")
            return []
    
    def create_tts_audio(self, text, lang='vi'):
        """Create TTS audio for text using gTTS"""
        try:
            # Create gTTS object
            tts = gTTS(text=text, lang=lang, slow=False)
            
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
    
    def create_bilingual_pair_audio(self, english_text, vietnamese_text):
        """Create audio with format: English (from original audio) + delay + Vietnamese (TTS)"""
        try:
            # Find matching audio segment for English
            segment = self.find_audio_segment(english_text)
            
            if segment:
                # Extract English audio from original file using timestamps
                main_audio = AudioSegment.from_mp3(self.audio_file)
                start_ms = float(segment['start']) * 1000
                end_ms = float(segment['end']) * 1000
                english_audio = main_audio[start_ms:end_ms]
                print(f"      ✅ Using original audio: {float(segment['start']):.2f}s - {float(segment['end']):.2f}s")
            else:
                # Fallback to TTS if no segment found
                english_audio = self.create_tts_audio(english_text, 'en')
                if english_audio is None:
                    print(f"      ❌ Failed to create English audio")
                    return None
                print(f"      ⚠️ No segment found, using TTS for English")
            
            # Create Vietnamese TTS audio
            vietnamese_audio = self.create_tts_audio(vietnamese_text, 'vi')
            if vietnamese_audio is None:
                print(f"      ❌ Failed to create Vietnamese TTS audio")
                return None
            
            # Create delay
            delay = AudioSegment.silent(duration=self.delay_duration)
            
            # Combine: English + delay + Vietnamese + delay
            final_audio = english_audio + delay + vietnamese_audio + delay
            
            return final_audio
            
        except Exception as e:
            print(f"❌ Error creating bilingual pair audio: {e}")
            return None
    
    async def create_group_audio_files(self, groups):
        """Create audio files for each group with incrementing names"""
        print(f"\n🎤 Creating audio files for {len(groups)} groups...")
        
        # Create output directory
        os.makedirs(self.output_folder, exist_ok=True)
        
        file_number = 1
        total_files = 0
        
        for group_idx, group in enumerate(groups, 1):
            print(f"\n🔄 Processing Group {group_idx}...")
            
            combined_audio = AudioSegment.empty()
            
            # Process each pair in the group: English, then Vietnamese
            for pair_idx, pair in enumerate(group, 1):
                english_text = pair.get('english', '')
                vietnamese_text = pair.get('vietnamese', '')
                
                if not english_text or not vietnamese_text:
                    print(f"   ⚠️ Skipping incomplete pair {pair_idx}")
                    continue
                
                print(f"   Processing pair {pair_idx}: {english_text[:40]}...")
                
                # Create bilingual audio for this pair
                pair_audio = self.create_bilingual_pair_audio(english_text, vietnamese_text)
                
                if pair_audio:
                    combined_audio += pair_audio
                    print(f"   ✅ Added pair {pair_idx}")
                else:
                    print(f"   ⚠️ Failed to create audio for pair {pair_idx}")
            
            # Export combined audio for this group
            if len(combined_audio) > 0:
                filename = f"{file_number:02d}.mp3"
                filepath = Path(self.output_folder) / filename
                combined_audio.export(filepath, format="mp3")
                duration = len(combined_audio) / 1000
                print(f"   ✅ Created: {filename} (Duration: {duration:.2f}s, {len(group)} pairs)")
                file_number += 1
                total_files += 1
            else:
                print(f"   ⚠️ No audio created for group {group_idx}")
        
        print(f"\n🎉 Successfully created {total_files} audio files")
        print(f"📁 Output folder: {self.output_folder}")
        
        return total_files > 0
    
    async def process(self):
        """Main processing function"""
        # Load segments from CSV
        if not self.load_segments():
            print("❌ Failed to load segments")
            return
        
        # Parse learning file and translate
        groups = await self.parse_learning_file()
        
        if not groups:
            print("❌ No groups to process")
            return
        
        # Create audio files
        await self.create_group_audio_files(groups)


async def main():
    # Configuration
    learning_file = f"{current_dir}/shared-volume/learning.txt"
    output_csv = f"{current_dir}/shared-volume/raw.csv"
    input_audio_file = input("Enter the path to the main audio file (or press Enter to skip): ").strip()
    audio_file = f"{current_dir}/shared-volume/{input_audio_file}" if input_audio_file else f"{current_dir}/shared-volume/audio.mp3"
    output_folder = f"{current_dir}/shared-volume/fast_output"
    
    print("🎯 Fast Audio Creator")
    print("=" * 50)
    
    # Create processor
    processor = FastAudioCreator(learning_file, audio_file, output_csv, output_folder)
    
    # Process
    await processor.process()


if __name__ == "__main__":
    asyncio.run(main())
