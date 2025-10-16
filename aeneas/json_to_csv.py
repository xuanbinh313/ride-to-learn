#!/usr/bin/env python3

import json
import csv

def convert_json_to_csv(json_file, csv_file):
    """Convert raw.json to CSV format with id, start, end, text columns."""
    
    # Read the JSON file
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Create CSV file
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow(['id', 'start', 'end', 'text'])
        
        # Write data rows
        for fragment in data['fragments']:
            fragment_id = fragment['id']
            start_time = fragment['begin']
            end_time = fragment['end']
            text = ' '.join(fragment['lines']).strip()
            
            writer.writerow([fragment_id, start_time, end_time, text])
    
    print(f"Successfully converted {json_file} to {csv_file}")

if __name__ == "__main__":
    # Convert raw.json to CSV
    convert_json_to_csv('raw.json', 'raw.csv')