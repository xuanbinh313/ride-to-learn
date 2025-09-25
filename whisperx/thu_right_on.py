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
    Handles cases where Exercise and Page are in consecutive rows
    """
    # Read CSV file
    df = pd.read_csv(csv_file)
    
    # Pattern to match "Exercise X Page Y" in same text
    combined_pattern = re.compile(r'Exercise\s+(\d+).*?Page\s+(\d+)', re.IGNORECASE)
    
    # Pattern to match "Exercise X" in one row
    exercise_pattern = re.compile(r'Exercise\s+(\d+)', re.IGNORECASE)
    
    # Pattern to match "Page Y" in one row
    page_pattern = re.compile(r'Page\s+(\d+)', re.IGNORECASE)
    
    exercises = []
    
    # First, look for combined patterns in single text
    for _, row in df.iterrows():
        text = str(row['text'])
        match = combined_pattern.search(text)
        
        if match:
            exercise_num = match.group(1)
            page_num = match.group(2)
            
            # Create standardized name
            exercise_name = f"Exercise_{exercise_num}_Page_{page_num}"
            start_time = float(row['start'])
            end_time = float(row['end'])
            
            exercises.append((exercise_name, start_time, end_time, text))
            print(f"Found (combined): {exercise_name} at {start_time:.2f}-{end_time:.2f}s - '{text.strip()}'")
    
    # Then, look for Exercise followed by Page in consecutive rows
    for i in range(len(df) - 1):
        current_row = df.iloc[i]
        next_row = df.iloc[i + 1]
        
        current_text = str(current_row['text'])
        next_text = str(next_row['text'])
        
        exercise_match = exercise_pattern.search(current_text)
        page_match = page_pattern.search(next_text)
        
        if exercise_match and page_match:
            exercise_num = exercise_match.group(1)
            page_num = page_match.group(1)
            
            # Create standardized name
            exercise_name = f"Exercise_{exercise_num}_Page_{page_num}"
            start_time = float(current_row['start'])  # Start from Exercise
            end_time = float(next_row['end'])         # End at Page
            
            # Check if this combination already exists (avoid duplicates)
            already_exists = any(ex[0] == exercise_name and abs(ex[1] - start_time) < 1.0 
                               for ex in exercises)
            
            if not already_exists:
                combined_text = f"{current_text.strip()} {next_text.strip()}"
                exercises.append((exercise_name, start_time, end_time, combined_text))
                print(f"Found (consecutive): {exercise_name} at {start_time:.2f}-{end_time:.2f}s - '{combined_text}'")
    
    return exercises

def parse_chunk_input(chunk_input: str) -> Tuple[int, int]:
    """
    Parse chunk input in format "exercise_num-page_num" 
    Example: "1-105" returns (1, 105) for Exercise_1_Page_105
    """
    try:
        parts = chunk_input.split('-')
        if len(parts) != 2:
            raise ValueError("Input format should be 'exercise_num-page_num'")
        
        exercise_num = int(parts[0])
        page_num = int(parts[1])
        return exercise_num, page_num
    except ValueError as e:
        raise ValueError(f"Invalid input format: {e}")

def find_specific_exercise(exercises: List[Tuple[str, float, float]], exercise_num: int, page_num: int) -> Tuple[str, float, float]:
    """
    Find a specific exercise by exercise number and page number
    """
    target_name = f"Exercise_{exercise_num}_Page_{page_num}"
    
    for exercise in exercises:
        name, start, end, text = exercise
        if name == target_name:
            return exercise
    
    raise ValueError(f"Exercise {exercise_num} Page {page_num} not found in the data")

def split_specific_exercise(audio_file: str, target_exercise: Tuple[str, float, float], 
                          all_exercises: List[Tuple[str, float, float]], 
                          output_dir: str = "exercise_chunks"):
    """
    Split audio for a specific exercise only
    """
    # Load audio file
    print(f"Loading audio file: {audio_file}")
    audio = AudioSegment.from_file(audio_file)
    audio_duration = len(audio) / 1000.0  # Convert to seconds
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Sort all exercises by start time to find the next exercise
    exercises_sorted = sorted(all_exercises, key=lambda x: x[1])
    
    # Find the target exercise in the sorted list
    target_name, target_start, target_end, target_text = target_exercise
    target_index = None
    
    for i, (name, start, end, text) in enumerate(exercises_sorted):
        if name == target_name and abs(start - target_start) < 0.1:  # Small tolerance for float comparison
            target_index = i
            break
    
    if target_index is None:
        raise ValueError(f"Could not find target exercise in sorted list")
    
    # Calculate chunk boundaries
    chunk_start = target_start
    
    # End time is the start of next exercise, or end of audio if it's the last one
    if target_index < len(exercises_sorted) - 1:
        chunk_end = exercises_sorted[target_index + 1][1]  # Start of next exercise
    else:
        chunk_end = audio_duration  # End of audio file
    
    # Convert seconds to milliseconds for pydub
    start_ms = int(chunk_start * 1000)
    end_ms = int(chunk_end * 1000)
    
    # Extract audio chunk
    chunk = audio[start_ms:end_ms]
    
    # Create filename
    filename = f"{target_index+1:02d}_{target_name}.mp3"
    filepath = os.path.join(output_dir, filename)
    
    # Export chunk
    chunk.export(filepath, format="mp3")
    duration = chunk_end - chunk_start
    print(f"Saved: {filepath} ({duration:.2f}s)")
    

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


def main():
    # File paths
    csv_file = "output_merged.csv"
    audio_file = "../downloads/Right On 7.mp3"
    output_dir = "exercise_chunks"
    
    print("=== Audio Splitter by Exercise Patterns ===")
    print("Options:")
    print("1. Enter 'all' to process all exercises")
    print("2. Enter 'exercise_num-page_num' to process specific exercise (e.g., '1-105' for Exercise 1 Page 105)")
    print("3. Press Enter to process all exercises (default)")
    
    user_input = input("\nEnter your choice: ").strip()
    
    print("\n=== Extracting Exercise patterns from CSV ===")
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
            chunk_duration = f"{next_start - start:.1f}s"
        else:
            chunk_duration = "until end of audio"
        
        print(f"{i:2d}. {name} (starts at {start:.1f}s) -> chunk duration: {chunk_duration}")
    
    # Process based on user input
    if user_input and user_input.lower() != 'all':
        try:
            # Parse specific exercise request
            exercise_num, page_num = parse_chunk_input(user_input)
            print(f"\n=== Processing specific exercise: Exercise {exercise_num} Page {page_num} ===")
            
            # Find the specific exercise
            target_exercise = find_specific_exercise(exercises, exercise_num, page_num)
            
            print(f"Found target exercise: {target_exercise[0]}")
            print("Note: Audio chunk will contain audio from this exercise pattern until the next exercise pattern")
            
            # Split only the specific exercise
            split_specific_exercise(audio_file, target_exercise, exercises, output_dir)
            
            print(f"\nDone! Specific exercise chunk saved to: {output_dir}")
            
        except ValueError as e:
            print(f"Error: {e}")
            print("Please use format 'exercise_num-page_num' (e.g., '1-105')")
            return
    else:
        # Process all exercises
        print(f"\n=== Splitting audio file for all exercises ===")
        print("Note: Each chunk will contain audio from the exercise pattern until the next exercise pattern")
        split_audio_by_exercises(audio_file, exercises, output_dir)
        
        print(f"\nDone! All exercise chunks saved to: {output_dir}")

if __name__ == "__main__":
    main()
