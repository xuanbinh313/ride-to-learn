from gtts import gTTS
from pydub import AudioSegment
import os
from pathlib import Path

def text_to_audio(vi_line, en_line, index):
    """Create audio for a Vietnamese-English pair"""
    vi_tts = gTTS(vi_line, lang='vi')
    en_tts = gTTS(en_line, lang='en')

    vi_path = f"temp_vi_{index}.mp3"
    en_path = f"temp_en_{index}.mp3"

    vi_tts.save(vi_path)
    en_tts.save(en_path)

    vi_audio = AudioSegment.from_file(vi_path)
    en_audio = AudioSegment.from_file(en_path)
    silence = AudioSegment.silent(duration=5000)  # 5 seconds silence

    combined = vi_audio + silence + en_audio + silence

    # Clean up temp files
    os.remove(vi_path)
    os.remove(en_path)

    return combined

def create_progressive_audio_files(lines, output_folder="enhanced_output"):
    """Create progressive audio files with combinations"""
    # Create output directory
    os.makedirs(output_folder, exist_ok=True)
    
    # Check valid format
    if len(lines) % 2 != 0:
        raise ValueError("⚠️ File input.txt must contain even number of lines (each 2 lines is 1 bilingual pair).")
    
    # Convert lines to pairs
    pairs = []
    for i in range(0, len(lines), 2):
        vi = lines[i]
        en = lines[i+1]
        pairs.append((vi, en))
    
    print(f"📝 Found {len(pairs)} Vietnamese-English pairs")
    
    # Create audio segments for each pair
    print("🎤 Creating audio segments for each pair...")
    pair_audios = []
    for i, (vi, en) in enumerate(pairs):
        print(f"   Processing pair {i+1}: {vi[:50]}... / {en[:50]}...")
        audio = text_to_audio(vi, en, i)
        pair_audios.append(audio)
    
    # Generate progressive combinations with sequential numbering
    total_files = 0
    file_number = 1
    group_number = 1
    
    while len(pair_audios) > 0:
        print(f"\n🔄 Processing Group {group_number}...")
        
        # Take up to 10 pairs for this group
        current_group = pair_audios[:10]
        pair_audios = pair_audios[10:]  # Remove processed pairs
        
        # Create progressive files for this group with sequential numbering
        for i in range(len(current_group)):
            # Individual pair (odd numbers: 01, 03, 05, 07, 09, 11, 13, 15, 17, 19)
            filename = f"{file_number:02d}.mp3"
            filepath = Path(output_folder) / filename
            current_group[i].export(filepath, format="mp3")
            total_files += 1
            print(f"   ✅ Created: {filename} (Pair {i+1} of Group {group_number})")
            file_number += 1
            
            # Progressive combination (even numbers: 02, 04, 06, 08, 10, 12, 14, 16, 18, 20)
            if i > 0:  # Skip the first one as it's just a single pair
                combined_audio = AudioSegment.empty()
                for j in range(i + 1):
                    combined_audio += current_group[j]
                
                combo_filename = f"{file_number:02d}.mp3"
                combo_filepath = Path(output_folder) / combo_filename
                combined_audio.export(combo_filepath, format="mp3")
                total_files += 1
                print(f"   ✅ Created: {combo_filename} (Combo of Pairs 1-{i+1} of Group {group_number})")
                file_number += 1
        
        group_number += 1
    
    print(f"\n🎉 Successfully created {total_files} audio files")
    print(f"📁 Output folder: {output_folder}")
    
    return total_files, file_number

def create_final_merged_file(lines, output_folder="enhanced_output", final_number=999):
    """Create one final file with all pairs"""
    print("\n🔄 Creating final merged file...")
    
    final_audio = AudioSegment.empty()
    
    for i in range(0, len(lines), 2):
        vi = lines[i]
        en = lines[i+1]
        print(f"🎤 Adding pair {i//2 + 1}: {vi[:30]}... / {en[:30]}...")
        pair_audio = text_to_audio(vi, en, f"final_{i//2}")
        final_audio += pair_audio
    
    # Export final merged file with sequential number
    final_path = Path(output_folder) / f"{final_number:02d}_final_all_pairs.mp3"
    final_audio.export(final_path, format="mp3")
    
    duration = len(final_audio) / 1000
    print(f"✅ Created final merged file: {final_path}")
    print(f"📊 Total duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")

def main():
    # Configuration
    input_file = "input-02.txt"
    output_folder = "enhanced_output"
    
    print(f"📖 Reading {input_file}...")
    
    # Read input file
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"❌ Error: File '{input_file}' not found!")
        return
    
    if not lines:
        print("❌ Error: Input file is empty!")
        return
    
    print(f"📝 Loaded {len(lines)} lines from {input_file}")
    
    # Create progressive audio files
    total_files, next_file_number = create_progressive_audio_files(lines, output_folder)
    
    # Create final merged file
    create_final_merged_file(lines, output_folder, next_file_number)
    
    print(f"\n🎉 All done! Created {total_files + 1} files in '{output_folder}' folder")

if __name__ == "__main__":
    main()
