import csv
from pydub import AudioSegment
import os
from pathlib import Path
current_dir = Path.cwd()
def export_audio_segment(csv_file, audio_file, output_file, start_time=None, end_time=None):
    """
    Export audio segment from start_time to end_time based on CSV timestamps.
    
    Args:
        csv_file: Path to the CSV file containing timestamps
        audio_file: Path to the original audio file
        output_file: Path for the output audio file
        start_time: Start time in seconds (optional, will use first timestamp if not provided)
        end_time: End time in seconds (optional, will use last timestamp if not provided)
    """
    
    # Check if audio file exists
    if not os.path.exists(audio_file):
        print(f"Error: Audio file not found at {audio_file}")
        return
    
    # Check if CSV file exists
    if not os.path.exists(csv_file):
        print(f"Error: CSV file not found at {csv_file}")
        return
    
    # Read CSV to get timestamps if not provided
    if start_time is None or end_time is None:
        timestamps = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    try:
                        timestamps.append(float(row[1]))
                        timestamps.append(float(row[2]))
                    except (ValueError, IndexError):
                        continue
        
        if not timestamps:
            print("Error: No valid timestamps found in CSV")
            return
        
        if start_time is None:
            start_time = min(timestamps)
        if end_time is None:
            end_time = max(timestamps)
    
    print(f"Loading audio from: {audio_file}")
    print(f"Extracting segment from {start_time}s to {end_time}s")
    
    # Load audio file
    audio = AudioSegment.from_file(audio_file)
    
    # Convert seconds to milliseconds
    start_ms = int(start_time * 1000)
    end_ms = int(end_time * 1000)
    
    # Extract segment
    segment = audio[start_ms:end_ms]
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Export segment
    file_extension = os.path.splitext(output_file)[1].lower()
    if file_extension == '.mp3':
        segment.export(output_file, format='mp3', bitrate='192k')
    elif file_extension == '.wav':
        segment.export(output_file, format='wav')
    else:
        # Default to mp3
        segment.export(output_file, format='mp3', bitrate='192k')
    
    duration = (end_time - start_time)
    print(f"Audio segment exported successfully to: {output_file}")
    print(f"Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")


def get_time_range_from_csv(csv_file):
    """
    Get start and end time from CSV file.
    Start time from the 'start' column of first data row.
    End time from the 'end' column of last data row.
    
    Args:
        csv_file: Path to the CSV file
    
    Returns:
        tuple: (start_time, end_time)
    """
    rows = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                rows.append({
                    'start': float(row['start']),
                    'end': float(row['end'])
                })
            except (ValueError, KeyError):
                continue
    
    if not rows:
        print("Error: No valid rows found in CSV")
        return None, None
    
    # Get start time from first row, end time from last row
    start_time = rows[0]['start']
    end_time = rows[-1]['end']
    
    return start_time, end_time


if __name__ == "__main__":
    # Configuration
    csv_file = f"{current_dir}/whisperx/split.csv"
    output_file = f"{current_dir}/whisperx/split.mp3"
    audio_file = f"{current_dir}/shared-volume/audio.mp3"
    
    # Get dynamic timestamps from CSV (first row start to last row end)
    start_time, end_time = get_time_range_from_csv(csv_file)
    
    if start_time is not None and end_time is not None:
        print(f"Extracted time range from CSV:")
        print(f"  Start time: {start_time}s (from first row)")
        print(f"  End time: {end_time}s (from last row)")
        print(f"  Duration: {end_time - start_time:.2f} seconds ({(end_time - start_time)/60:.2f} minutes)")
        
        # Export the audio segment
        export_audio_segment(csv_file, audio_file, output_file, start_time, end_time)
    else:
        print("Error: Could not extract time range from CSV")
