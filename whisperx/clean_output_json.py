import json
import csv
# Read from raw.json
with open("output.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Transform to simplified structure
simplified = {
    "segments": [
        {
            "id": seg["id"],
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"]
        } for seg in data["segments"]
    ]
}

# Write to result.json
with open("result.json", "w", encoding="utf-8") as f:
    json.dump(simplified, f, indent=2, ensure_ascii=False)

# Open CSV file for writing
with open("output.csv", "w", newline='', encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    
    # Write header
    writer.writerow(["id", "start", "end", "text"])
    
    # Write rows
    for seg in data["segments"]:
        writer.writerow([seg["id"], seg["start"], seg["end"], seg["text"].strip()])