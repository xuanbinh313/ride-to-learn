import json
import csv
import os

def convert_json_to_csv(json_file_path, csv_file_path=None):
    """
    Convert JSON file with fragments to CSV format with columns: id, start, end, text
    
    Args:
        json_file_path (str): Path to the input JSON file
        csv_file_path (str): Path to the output CSV file (optional)
    """
    
    # If no CSV path provided, create one based on JSON filename
    if csv_file_path is None:
        base_name = os.path.splitext(json_file_path)[0]
        csv_file_path = f"{base_name}.csv"
    
    try:
        # Read JSON file
        with open(json_file_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
        
        # Extract fragments
        fragments = data.get('fragments', [])
        
        # Write to CSV
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            
            # Write header
            writer.writerow(['id', 'start', 'end', 'text'])
            
            # Write data rows
            for fragment in fragments:
                fragment_id = fragment.get('id', '')
                start_time = fragment.get('begin', '')
                end_time = fragment.get('end', '')
                
                # Join all lines to create the text
                lines = fragment.get('lines', [])
                text = ' '.join(lines) if lines else ''
                
                writer.writerow([fragment_id, start_time, end_time, text])
        
        print(f"Successfully converted {json_file_path} to {csv_file_path}")
        print(f"Processed {len(fragments)} fragments")
        
    except FileNotFoundError:
        print(f"Error: File {json_file_path} not found")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {json_file_path}")
    except Exception as e:
        print(f"Error: {str(e)}")

def main():
    """
    Main function to handle command line usage or direct file conversion
    """
    import sys
    
    if len(sys.argv) > 1:
        # Command line usage
        json_file = sys.argv[1]
        csv_file = sys.argv[2] if len(sys.argv) > 2 else None
        convert_json_to_csv(json_file, csv_file)
    else:
        # Default conversion for the current output.json file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_file = os.path.join(current_dir, 'aeneas', 'output.json')
        
        if os.path.exists(json_file):
            convert_json_to_csv(json_file)
        else:
            print("No JSON file specified and default output.json not found")
            print("Usage: python json_to_csv_converter.py <json_file> [csv_file]")

if __name__ == "__main__":
    main()