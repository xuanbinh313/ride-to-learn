import csv
import json
import re
import asyncio
from pathlib import Path
from pydub import AudioSegment
from gtts import gTTS
from googletrans import Translator
import tempfile
import os
from pathlib import Path
current_dir = Path.cwd()
class BilingualAudioCreator:
    def __init__(self, learning_file, output_csv, audio_file, output_folder="bilingual_output"):
        self.learning_file = learning_file
        self.output_csv = output_csv
        self.audio_file = audio_file
        self.output_folder = output_folder
        self.segments = []
        self.delay_duration = 5000  # 5 seconds in milliseconds
        self.translator = Translator()
        
    def load_segments(self):
        """Load segments from output.json"""
        try:
            # with open(self.output_json, 'r', encoding='utf-8') as f:
            #     data = json.load(f)
            #     self.segments = data.get('segments', [])
            #     print(f"📊 Loaded {len(self.segments)} segments from {self.output_json}")
            with open(self.output_csv,'r', encoding='utf-8') as csvFile:
                reader = csv.DictReader(csvFile)
                for row in reader:
                    print(row)
                    self.segments.append(row)
        except Exception as e:
            print(f"❌ Error loading segments: {e}")
            return False
        return True
    
    async def translate_text(self, text, dest_language='vi'):
        """Translate text to destination language using Google Translate"""
        try:
            loop = asyncio.get_event_loop()
            translated = await loop.run_in_executor(None, self.translator.translate, text, dest_language)
            return translated.text
        except Exception as e:
            print(f"❌ Error translating text: {e}")
            return ""
    
    async def parse_learning_file(self):
        """Parse learning.txt to extract English lines and translate them to Vietnamese"""
        pairs = []
        groups = []  # Track which pairs belong to which group
        current_group = []
        
        try:
            with open(self.learning_file, 'r', encoding='utf-8') as f:
                raw_lines = f.readlines()

            # Clean lines
            lines = [ln.strip() for ln in raw_lines if ln.strip()]

            print(f"📝 Found {len(lines)} lines, processing...")
            
            # Translate each English line to Vietnamese
            pair_index = 0
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
                vietnamese_text = await self.translate_text(english_text, 'vi')
                
                if vietnamese_text:
                    pairs.append({
                        'english': english_text,
                        'vietnamese': vietnamese_text,
                        'pair_index': pair_index
                    })
                    current_group.append(pair_index)
                    pair_index += 1
                    print(f"   ✅ Vietnamese: {vietnamese_text[:50]}...")
                else:
                    print(f"   ⚠️ Translation failed for: {english_text[:50]}...")
            
            # Add remaining pairs to last group
            if current_group:
                groups.append(current_group)

            print(f"📝 Successfully created {len(pairs)} Vietnamese-English pairs in {len(groups)} groups")
            return pairs, groups

        except Exception as e:
            print(f"❌ Error parsing learning file: {e}")
            return [], []
    

    
    def create_english_only_audio(self, pair_indices, pairs, output_path):
        """Create English-only audio by concatenating segments for given pair indices"""
        try:
            main_audio = AudioSegment.from_mp3(self.audio_file)
            combined_audio = AudioSegment.empty()
            
            print(f"   🎵 Creating English-only audio for {len(pair_indices)} segments...")
            
            for idx in pair_indices:
                if idx >= len(pairs):
                    continue
                    
                pair = pairs[idx]
                english_text = pair.get('english', '')
                
                # Find matching audio segment
                segment = self.find_audio_segment(english_text)
                
                if segment:
                    start_ms = float(segment['start']) * 1000
                    end_ms = float(segment['end']) * 1000
                    english_audio = main_audio[start_ms:end_ms]
                    combined_audio += english_audio
                    print(f"      ✅ Added segment: {english_text[:40]}... ({float(segment['start']):.2f}s - {float(segment['end']):.2f}s)")
                else:
                    print(f"      ⚠️ No audio found for: {english_text[:40]}...")
            
            if len(combined_audio) > 0:
                speed = 1.2
                new_audio = combined_audio._spawn(combined_audio.raw_data, overrides={
                    "frame_rate": int(combined_audio.frame_rate * speed)
                })
                new_audio.export(output_path, format="mp3")
                duration = len(new_audio) / 1000
                print(f"   ✅ Created English-only audio: {output_path.name} (Duration: {duration:.2f}s)")
                return True
            else:
                print(f"   ⚠️ No audio segments to export")
                return False
                
        except Exception as e:
            print(f"   ❌ Error creating English-only audio: {e}")
            return False
    
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
        """Create audio with format: Vietnamese TTS + 5s delay + English audio repeated 5 times with delays"""
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
            start_ms = float(english_segment['start'] ) *1000
            end_ms = float(english_segment['end'] )* 1000
            english_audio = main_audio[start_ms:end_ms]
            
            # Combine: Vietnamese TTS + delay + English audio repeated 5 times with delays
            final_audio = vietnamese_audio + delay
            
            # Add English 5 times with delays
            for i in range(5):
                final_audio += english_audio + delay
            
            # Export
            final_audio.export(output_path, format="mp3")
            
            duration = len(final_audio) / 1000
            print(f"✅ Created: {output_path} (Duration: {duration:.2f}s)")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating bilingual audio: {e}")
            return False
    
    async def create_enhanced_progressive_audio(self, pairs, groups=None):
        """Create progressive audio files like enhanced_speak_my_self.py"""
        print(f"\n🎤 Creating enhanced progressive audio files...")
        
        # Create output directory
        os.makedirs(self.output_folder, exist_ok=True)
        # Create audio segments for each pair
        # pair_audios: for individual pair files -> Vietnamese 1 time + English repeated 5 times
        # single_pair_audios: for group/combined files -> Vietnamese 1 time + English 1 time
        pair_audios = []
        single_pair_audios = []
        success_count = 0

        for i, pair in enumerate(pairs):
            vietnamese_text = pair.get('vietnamese', '')
            english_text = pair.get('english', '')

            if not vietnamese_text or not english_text:
                print(f"⚠️ Skipping incomplete pair {i+1}")
                continue

            print(f"   Processing pair {i+1}: {vietnamese_text[:50]}... / {english_text[:50]}...")

            # Find matching audio segment for English
            segment = self.find_audio_segment(english_text)

            if segment is None:
                print(f"   ⚠️ No matching audio found, using TTS for English: {english_text[:30]}...")
                # For individual pair files: Vietnamese 1 time + English repeated 5 times
                audio = self.create_tts_bilingual_audio(vietnamese_text, english_text, repeat_times=5)
                # For group/combined files: Vietnamese 1 time + English 1 time
                single_audio = self.create_tts_bilingual_audio(vietnamese_text, english_text, repeat_times=1)
            else:
                print(f"   ✅ Found audio segment: {float(segment['start']):.2f}s - {float(segment['end']):.2f}s")
                # For individual pair files: Vietnamese 1 time + English repeated 5 times
                audio = self.create_hybrid_bilingual_audio(vietnamese_text, segment, repeat_times=5)
                # For group/combined files: Vietnamese 1 time + English 1 time
                single_audio = self.create_hybrid_bilingual_audio(vietnamese_text, segment, repeat_times=1)

            if audio:
                pair_audios.append(audio)
                success_count += 1

            # Append single-play version only if created successfully; otherwise try to create a fallback
            if single_audio:
                single_pair_audios.append(single_audio)
            else:
                # If single_audio failed but the repeated audio exists, try to derive a single-play version
                # (fallback: take the repeated audio and remove repeated English by keeping only the first Vietnamese+English block)
                try:
                    if audio:
                        seg = audio
                        # Compute approximate chunk length by dividing total by (1 + 5) if repeat_times used 5
                        approx_chunk_ms = int(len(seg) / (1 + 5))
                        fallback_single = seg[: (approx_chunk_ms * 1)]
                        single_pair_audios.append(fallback_single)
                except Exception:
                    pass

        if not pair_audios:
            print("❌ No audio segments created")
            return False

        # Generate progressive combinations with enhanced numbering
        total_files = 0
        file_number = 1
        group_number = 1

        # Work in groups based on --- separators or default 10 pairs
        remaining_audios = pair_audios.copy()
        remaining_single_audios = single_pair_audios.copy()
        processed_pairs = 0

        while remaining_audios:
            print(f"\n🔄 Processing Group {group_number}...")

            # Determine group size
            if groups and group_number - 1 < len(groups):
                group_indices = groups[group_number - 1]
                group_size = len(group_indices)
            else:
                group_size = min(10, len(remaining_audios))
                group_indices = list(range(processed_pairs, processed_pairs + group_size))

            # Take pairs for this group
            current_group = remaining_audios[:group_size]
            current_single_group = remaining_single_audios[:group_size]
            remaining_audios = remaining_audios[group_size:]
            remaining_single_audios = remaining_single_audios[group_size:]

            # Create English-only audio FIRST for this group
            if groups and group_number - 1 < len(groups):
                english_only_filename = f"{file_number:02d}.mp3"
                english_only_filepath = Path(self.output_folder) / english_only_filename
                if self.create_english_only_audio(group_indices, pairs, english_only_filepath):
                    total_files += 1
                    print(f"   ✅ Created English-only: {english_only_filename} (Group {group_number})")
                    file_number += 1

            # Create progressive files for this group
            for i in range(len(current_group)):
                # Individual pair (odd numbers after english-only)
                filename = f"{file_number:02d}.mp3"
                filepath = Path(self.output_folder) / filename
                current_group[i].export(filepath, format="mp3")
                total_files += 1
                print(f"   ✅ Created: {filename} (Pair {i+1} of Group {group_number})")
                file_number += 1

                # Progressive combination (even numbers)
                # Use single-play audios for group combinations (Vietnamese 1 time + English 1 time)
                if i > 0:  # Skip the first one as it's just a single pair
                    combined_audio = AudioSegment.empty()
                    for j in range(i + 1):
                        # If single version exists, use it; otherwise fall back to the repeated version
                        if j < len(current_single_group) and current_single_group[j] is not None:
                            combined_audio += current_single_group[j]
                        else:
                            combined_audio += current_group[j]

                    combo_filename = f"{file_number:02d}.mp3"
                    combo_filepath = Path(self.output_folder) / combo_filename
                    combined_audio.export(combo_filepath, format="mp3")
                    total_files += 1
                    print(f"   ✅ Created: {combo_filename} (Combo of Pairs 1-{i+1} of Group {group_number})")
                    file_number += 1

            # Create English-only audio AGAIN at the END of this group
            if groups and group_number - 1 < len(groups):
                english_only_end_filename = f"{file_number:02d}.mp3"
                english_only_end_filepath = Path(self.output_folder) / english_only_end_filename
                if self.create_english_only_audio(group_indices, pairs, english_only_end_filepath):
                    total_files += 1
                    print(f"   ✅ Created English-only (end): {english_only_end_filename} (Group {group_number})")
                    file_number += 1

            processed_pairs += group_size
            group_number += 1

        total_files += 1

        print(f"\n🎉 Successfully created {total_files} enhanced audio files")
        print(f"📁 Output folder: {self.output_folder}")

        return True
    
    def create_tts_bilingual_audio(self, vietnamese_text, english_text, repeat_times=5):
        """Create bilingual audio using TTS for both languages.

        repeat_times: how many times to append the English audio (default 5).
        Use repeat_times=1 in enhanced/merged outputs to avoid repeated sentences.
        """
        try:
            # Create TTS for Vietnamese
            vi_tts = gTTS(text=vietnamese_text, lang='vi', slow=False)
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as vi_temp:
                vi_temp_path = vi_temp.name
            vi_tts.save(vi_temp_path)
            vi_audio = AudioSegment.from_mp3(vi_temp_path)
            os.unlink(vi_temp_path)

            # Create TTS for English
            en_tts = gTTS(text=english_text, lang='en', slow=False)
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as en_temp:
                en_temp_path = en_temp.name
            en_tts.save(en_temp_path)
            en_audio = AudioSegment.from_mp3(en_temp_path)
            os.unlink(en_temp_path)

            # Combine: Vietnamese 1 time + delay + English repeated with delays
            delay = AudioSegment.silent(duration=self.delay_duration)
            combined = vi_audio + delay

            # Add English repeat_times with delays
            for i in range(max(1, int(repeat_times))):
                combined += en_audio + delay

            return combined

        except Exception as e:
            print(f"❌ Error creating TTS bilingual audio: {e}")
            return None
    
    def create_hybrid_bilingual_audio(self, vietnamese_text, english_segment, repeat_times=5):
        """Create bilingual audio using Vietnamese TTS + original English audio.

        repeat_times: how many times to append the English segment (default 5).
        """
        try:
            # Create Vietnamese TTS audio
            vietnamese_audio = self.create_tts_audio(vietnamese_text, None)
            if vietnamese_audio is None:
                return None

            # Extract English audio segment
            main_audio = AudioSegment.from_mp3(self.audio_file)
            start_ms = float(english_segment['start']) * 1000
            end_ms = float(english_segment['end']) * 1000
            english_audio = main_audio[start_ms:end_ms]

            # Combine: Vietnamese 1 time + delay + English repeated with delays
            delay = AudioSegment.silent(duration=self.delay_duration)
            combined = vietnamese_audio + delay

            # Add English repeat_times with delays
            for i in range(max(1, int(repeat_times))):
                combined += english_audio + delay

            return combined

        except Exception as e:
            print(f"❌ Error creating hybrid bilingual audio: {e}")
            return None

    async def process_all_pairs(self):
        """Process all Vietnamese-English pairs using enhanced mode"""
        # Load segments
        if not self.load_segments():
            return
        
        # Parse learning file and translate
        result = await self.parse_learning_file()
        if isinstance(result, tuple):
            pairs, groups = result
        else:
            pairs = result
            groups = None
            
        if not pairs:
            return
        
        # Use enhanced progressive audio generation
        return await self.create_enhanced_progressive_audio(pairs, groups)

async def main():
    # Configuration
    learning_file = f"{current_dir}/shared-volume/learning.txt"
    output_csv = f"{current_dir}/shared-volume/raw.csv"
    input_audio_file = input("Enter the path to the main audio file (default: ../shared-volume/audio.mp3): ").strip()
    audio_file = f"{current_dir}/shared-volume/{input_audio_file}" if input_audio_file else f"{current_dir}/shared-volume/audio.mp3"
    output_folder = f"{current_dir}/shared-volume/result"
    
    print("🎯 Bilingual Audio Creator - Enhanced Mode")
    print("=" * 50)
    
    # Create processor
    processor = BilingualAudioCreator(learning_file, output_csv, audio_file, output_folder)
    
    # Process all pairs
    await processor.process_all_pairs()

if __name__ == "__main__":
    asyncio.run(main())
