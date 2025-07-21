import csv
from pydub import AudioSegment
import os

def create_delayed_audio(audio_file_path, tsv_file_path, output_file_path, delay_seconds=5):
    """
    Create audio with delays between sentences based on TSV timestamps
    
    Args:
        audio_file_path: Path to the original audio file
        tsv_file_path: Path to the transcription TSV file
        output_file_path: Path for the output audio file
        delay_seconds: Delay in seconds between sentences (default: 5)
    """
    
    print(f"🔄 Loading audio file: {audio_file_path}")
    
    # Load the original audio
    try:
        audio = AudioSegment.from_mp3(audio_file_path)
    except Exception as e:
        print(f"❌ Error loading audio file: {e}")
        return
    
    print(f"🔄 Reading transcription file: {tsv_file_path}")
    
    # Read the TSV file to get timestamps
    segments = []
    try:
        with open(tsv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                start_ms = int(float(row['start']))
                end_ms = int(float(row['end']))
                text = row['text'].strip()
                segments.append({
                    'start': start_ms,
                    'end': end_ms,
                    'text': text
                })
    except Exception as e:
        print(f"❌ Error reading TSV file: {e}")
        return
    
    print(f"📊 Found {len(segments)} audio segments")
    
    # Create silence for delays
    delay_ms = delay_seconds * 1000  # Convert to milliseconds
    silence = AudioSegment.silent(duration=delay_ms)
    
    print(f"🔄 Creating delayed audio with {delay_seconds}s delays...")
    
    # Build the new audio with delays
    new_audio = AudioSegment.empty()
    
    for i, segment in enumerate(segments):
        # Extract the audio segment
        audio_segment = audio[segment['start']:segment['end']]
        
        # Add the audio segment
        new_audio += audio_segment
        
        # Add delay after each segment except the last one
        if i < len(segments) - 1:
            new_audio += silence
            
        print(f"✅ Processed segment {i+1}/{len(segments)}: {segment['text'][:50]}...")
    
    print(f"🔄 Saving delayed audio to: {output_file_path}")
    
    # Export the new audio
    try:
        new_audio.export(output_file_path, format="mp3")
        print(f"✅ Successfully created delayed audio!")
        print(f"📊 Original duration: {len(audio)/1000:.1f} seconds")
        print(f"📊 New duration: {len(new_audio)/1000:.1f} seconds")
        print(f"📊 Added {len(segments)-1} delays of {delay_seconds}s each")
    except Exception as e:
        print(f"❌ Error saving audio file: {e}")

if __name__ == "__main__":
    # File paths
    audio_file = "../assets/economy/book-05/test03/95-97.mp3"
    tsv_file = "transcription.tsv"
    output_file = "95-97_with_delays.mp3"
    
    # Check if files exist
    if not os.path.exists(audio_file):
        print(f"❌ Audio file not found: {audio_file}")
        exit(1)
    
    if not os.path.exists(tsv_file):
        print(f"❌ TSV file not found: {tsv_file}")
        exit(1)
    
    # Create the delayed audio
    create_delayed_audio(
        audio_file_path=audio_file,
        tsv_file_path=tsv_file,
        output_file_path=output_file,
        delay_seconds=5
    )
