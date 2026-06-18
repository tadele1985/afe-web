from pathlib import Path

file_path = Path("femis_data.json")

# read with BOM-safe encoding
data = file_path.read_text(encoding="utf-8-sig")

# rewrite clean UTF-8 file
file_path.write_text(data, encoding="utf-8")

print("Fixed JSON encoding successfully")