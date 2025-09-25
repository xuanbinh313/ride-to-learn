#!/usr/bin/env python3
"""
Split audio file based on Exercise + Page patterns found in CSV file
"""

import pandas as pd
import re
import os
from pydub import AudioSegment
from typing import List, Tuple

def extract_exercise_patterns(csv_file: str) -> List[Tuple[str, float, float]]:
    """
    Extract Exercise + Page patterns with their timestamps from CSV file
    Returns list of tuples: (pattern_name, start_time, end_time)
    """
    # Read CSV file
    df = pd.read_csv(csv_file)
    
    # Pattern to match "Exercise X Page Y" (with various formats)
    pattern = re.compile(r'Exercise\s+(\d+).*?Page\s+(\d+)', re.IGNORECASE)
    
    exercises = []
    
    for _, row in df.iterrows():
        text = str(row['text'])
        match = pattern.search(text)
        
        if match:
            exercise_num = match.group(1)
            page_num = match.group(2)
            
            # Create standardized name
            exercise_name = f"Exercise_{exercise_num}_Page_{page_num}"
            start_time = float(row['start'])
            end_time = float(row['end'])
            
            exercises.append((exercise_name, start_time, end_time, text))
            print(f"Found: {exercise_name} at {start_time:.2f}-{end_time:.2f}s - '{text.strip()}'")
    
    return exercises

def split_audio_by_exercises(audio_file: str, exercises: List[Tuple[str, float, float]], 
                           output_dir: str = "exercise_chunks"):
    """
    Split audio file into chunks based on exercise patterns
    Each chunk goes from one exercise pattern until the next exercise pattern
    """
    # Load audio file
    print(f"Loading audio file: {audio_file}")
    audio = AudioSegment.from_file(audio_file)
    audio_duration = len(audio) / 1000.0  # Convert to seconds
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Sort exercises by start time
    exercises_sorted = sorted(exercises, key=lambda x: x[1])
    
    # Split and save each exercise chunk (from pattern to next pattern)
    for i, (name, start, end, text) in enumerate(exercises_sorted):
        # Start time is the beginning of current exercise
        chunk_start = start
        
        # End time is the start of next exercise, or end of audio if it's the last one
        if i < len(exercises_sorted) - 1:
            chunk_end = exercises_sorted[i + 1][1]  # Start of next exercise
        else:
            chunk_end = audio_duration  # End of audio file
        
        # Convert seconds to milliseconds for pydub
        start_ms = int(chunk_start * 1000)
        end_ms = int(chunk_end * 1000)
        
        # Extract audio chunk
        chunk = audio[start_ms:end_ms]
        
        # Create filename
        filename = f"{i+1:02d}_{name}.mp3"
        filepath = os.path.join(output_dir, filename)
        
        # Export chunk
        chunk.export(filepath, format="mp3")
        duration = chunk_end - chunk_start
        print(f"Saved: {filepath} ({duration:.2f}s)")
        
        # Also save metadata
        metadata_file = os.path.join(output_dir, f"{i+1:02d}_{name}_metadata.txt")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            f.write(f"Exercise: {name}\n")
            f.write(f"Start time: {chunk_start:.2f}s\n")
            f.write(f"End time: {chunk_end:.2f}s\n")
            f.write(f"Duration: {duration:.2f}s\n")
            f.write(f"Original pattern text: {text}\n")
            f.write(f"Note: Audio chunk from this exercise until next exercise pattern\n")

def main():
    # File paths
    csv_file = "/Users/binhcodev/Documents/Works/python/translate-audio/whisperx/output_merged.csv"
    audio_file = "/Users/binhcodev/Documents/Works/python/translate-audio/downloads/Right On.mp3"
    output_dir = "/Users/binhcodev/Documents/Works/python/translate-audio/whisperx/exercise_chunks"
    
    print("=== Extracting Exercise patterns from CSV ===")
    exercises = extract_exercise_patterns(csv_file)
    
    if not exercises:
        print("No exercise patterns found!")
        return
    
    print(f"\nFound {len(exercises)} exercise patterns:")
    
    # Calculate chunk durations (from pattern to next pattern)
    exercises_sorted = sorted(exercises, key=lambda x: x[1])
    for i, (name, start, end, text) in enumerate(exercises_sorted, 1):
        if i < len(exercises_sorted):
            next_start = exercises_sorted[i][1]  # Start of next exercise
            chunk_duration = next_start - start
        else:
            chunk_duration = "until end of audio"
        
        print(f"{i:2d}. {name} (starts at {start:.1f}s) -> chunk duration: {chunk_duration}")
    
    print(f"\n=== Splitting audio file ===")
    print("Note: Each chunk will contain audio from the exercise pattern until the next exercise pattern")
    split_audio_by_exercises(audio_file, exercises, output_dir)
    
    print(f"\nDone! Exercise chunks saved to: {output_dir}")

if __name__ == "__main__":
    main()
