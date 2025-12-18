import csv
import os
from pathlib import Path

current_dir = Path.cwd()
def extract_text_from_csv(csv_file, output_file):
    """
    Read CSV file and extract all text from the 'text' column,
    join them together, and split by sentence delimiters (. or ?)
    """
    try:
        text_content = []
        
        # Read the CSV file
        with open(csv_file, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            print(f"📖 Reading CSV file: {csv_file}")
            print(f"📝 Columns found: {csv_reader.fieldnames}")
            
            # Extract text from each row
            for row_num, row in enumerate(csv_reader, 1):
                if 'text' in row:
                    text = row['text'].strip()
                    if text:  # Only add non-empty text
                        text_content.append(text)
                        print(f"   Row {row_num}: {text[:50]}...")
                else:
                    print(f"⚠️ No 'text' column found in row {row_num}")
        
        # Join all text with space
        joined_text = ' '.join(text_content)
        print(f"\n🔗 Joined {len(text_content)} text entries into one string")
        
        # Split by sentence delimiters (. or ?)
        import re
        # Split by . or ? but keep the delimiter
        pattern = r'(?<!\bMr)(?<!\bMs)(?<!\bmr)(?<!\bms)(?<!\bp)(?<!\ba)([.?!])'
        sentences = re.split(pattern, joined_text)
        
        # Recombine sentences with their delimiters
        final_sentences = []
        i = 0
        while i < len(sentences):
            if i + 1 < len(sentences) and sentences[i + 1] in ['.', '?']:
                # Combine sentence with its delimiter
                sentence = (sentences[i] + sentences[i + 1]).strip()
                if sentence:
                    final_sentences.append(sentence)
                i += 2
            else:
                # No delimiter found, add as is
                sentence = sentences[i].strip()
                if sentence:
                    final_sentences.append(sentence)
                i += 1
        
        print(f"✂️  Split into {len(final_sentences)} sentences")
        
        # Write all sentences to output file, one per line
        with open(output_file, 'w', encoding='utf-8') as file:
            for sentence in final_sentences:
                file.write(sentence + '\n')
        
        print(f"\n✅ Successfully extracted and split {len(final_sentences)} sentences")
        print(f"📄 Output saved to: {output_file}")
        
        # Show file size
        file_size = os.path.getsize(output_file)
        print(f"📊 File size: {file_size} bytes ({file_size/1024:.2f} KB)")
        
        return True
        
    except FileNotFoundError:
        print(f"❌ Error: CSV file '{csv_file}' not found")
        return False
    except Exception as e:
        print(f"❌ Error processing CSV: {e}")
        return False

def main():
    """Main function to extract text from raw.csv to raw.txt"""
    csv_file = f"{current_dir}/whisperx/raw.csv"
    output_file = f"{current_dir}/shared-volume/raw.txt"
    
    print("🔄 CSV Text Extractor")
    print("=" * 30)
    
    # Check if CSV file exists
    if not os.path.exists(csv_file):
        print(f"❌ CSV file '{csv_file}' not found in current directory")
        return
    
    # Extract text
    success = extract_text_from_csv(csv_file, output_file)
    
    if success:
        print(f"\n🎉 Text extraction completed!")
        print(f"📁 Check '{output_file}' for the extracted text")
    else:
        print(f"\n❌ Text extraction failed!")

if __name__ == "__main__":
    main()
