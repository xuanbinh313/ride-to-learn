import csv
import json
import re
from pathlib import Path
from pydub import AudioSegment
from gtts import gTTS
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
    
    def parse_learning_file(self):
        """Parse learning.txt to extract Vietnamese-English pairs"""
        pairs = []
        try:
            with open(self.learning_file, 'r', encoding='utf-8') as f:
                raw_lines = f.readlines()

            # Clean lines and skip empty lines
            lines = [ln.strip() for ln in raw_lines if ln.strip()]

            prev_line = None
            prev_lang = None

            for line in lines:
                lang = 'en' if self.is_english_line(line) else 'vi'

                if prev_line is None:
                    prev_line = line
                    prev_lang = lang
                    continue

                # We have a previous unpaired line. Pair depending on detected languages.
                if prev_lang == 'en' and lang == 'vi':
                    pairs.append({'english': prev_line, 'vietnamese': line})
                elif prev_lang == 'vi' and lang == 'en':
                    pairs.append({'english': line, 'vietnamese': prev_line})
                else:
                    # Ambiguous (both detected same language) - fallback to adjacent pairing
                    # Assume prev is english and current is vietnamese to preserve original intent
                    pairs.append({'english': prev_line, 'vietnamese': line})

                # Reset previous
                prev_line = None
                prev_lang = None

            # If there's a dangling line at the end, add it as an incomplete pair
            if prev_line is not None:
                if prev_lang == 'en':
                    pairs.append({'english': prev_line, 'vietnamese': ''})
                else:
                    pairs.append({'english': '', 'vietnamese': prev_line})

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
        
        # If 20% or more of words are common English words, consider it English
        return len(words) > 0 and (word_count / len(words)) >= 0.2
    
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
    
    def create_enhanced_progressive_audio(self, pairs):
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

        # Work in groups of 10 pairs
        remaining_audios = pair_audios.copy()
        remaining_single_audios = single_pair_audios.copy()

        while remaining_audios:
            print(f"\n🔄 Processing Group {group_number}...")

            # Take up to 10 pairs for this group
            current_group = remaining_audios[:10]
            current_single_group = remaining_single_audios[:10]
            remaining_audios = remaining_audios[10:]
            remaining_single_audios = remaining_single_audios[10:]

            # Create progressive files for this group
            for i in range(len(current_group)):
                # Individual pair (odd numbers: 01, 03, 05, ...)
                filename = f"{file_number:02d}.mp3"
                filepath = Path(self.output_folder) / filename
                current_group[i].export(filepath, format="mp3")
                total_files += 1
                print(f"   ✅ Created: {filename} (Pair {i+1} of Group {group_number})")
                file_number += 1

                # Progressive combination (even numbers: 02, 04, 06, ...)
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

            group_number += 1

        # Create final merged file with all pairs
        print(f"\n🔄 Creating final merged file...")
        final_audio = AudioSegment.empty()
        for audio in pair_audios:
            final_audio += audio

        final_filename = f"{file_number:02d}_final_all_pairs.mp3"
        final_filepath = Path(self.output_folder) / final_filename
        final_audio.export(final_filepath, format="mp3")

        total_duration = len(final_audio) / 1000
        print(f"✅ Created final merged file: {final_filename}")
        print(f"📊 Total duration: {total_duration:.2f} seconds ({total_duration/60:.2f} minutes)")

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
            merged_output_path = output_path / "77-79.mp3"
            merged_audio.export(merged_output_path, format="mp3")
            
            total_duration = len(merged_audio) / 1000
            print(f"✅ Successfully merged all files into: {merged_output_path}")
            print(f"📊 Total duration: {total_duration:.2f} seconds ({total_duration/60:.2f} minutes)")
            
            # Remove individual MP3 files~~
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

    def process_all_pairs(self, enhanced_mode=False):
        """Process all Vietnamese-English pairs"""
        # Load segments
        if not self.load_segments():
            return
        
        # Parse learning file
        pairs = self.parse_learning_file()
        if not pairs:
            return
        
        if enhanced_mode:
            # Use enhanced progressive audio generation
            return self.create_enhanced_progressive_audio(pairs)
        
        # Original mode: Create individual files and merge
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
            print(f"✅ Found audio segment: {float(segment['start']):.2f}s - {float(segment['end']):.2f}s")
            
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
    learning_file = f"{current_dir}/shared-volume/learning.txt"
    output_csv = f"{current_dir}/shared-volume/raw.csv"
    input_audio_file = input("Enter the path to the main audio file (default: ../shared-volume/audio.mp3): ").strip()
    audio_file = f"{current_dir}/shared-volume/{input_audio_file}" if input_audio_file else f"{current_dir}/shared-volume/audio.mp3"
    output_folder = f"{current_dir}/shared-volume/result"  # Changed folder name for enhanced mode
    
    print("🎯 Bilingual Audio Creator - Enhanced Mode")
    print("=" * 50)
    
    # Ask user which mode to use
    print("Choose mode:")
    print("1. Original mode (individual files + single merged file)")
    print("2. Enhanced mode (progressive combinations like enhanced_speak_my_self.py)")
    
    try:
        choice = input("Enter your choice (1 or 2): ").strip()
        enhanced_mode = choice == "2"
            
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        return
    except Exception:
        print("⚠️ Invalid input, using Enhanced mode as default")
        enhanced_mode = True
    
    # Create processor
    processor = BilingualAudioCreator(learning_file, output_csv, audio_file, output_folder)
    
    # Process all pairs
    processor.process_all_pairs(enhanced_mode=enhanced_mode)

if __name__ == "__main__":
    main()
