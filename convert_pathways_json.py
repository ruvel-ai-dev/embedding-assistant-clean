import json

with open("pathways.json", "r") as f:
    data = json.load(f)

output_lines = []
for entry in data:
    output_lines.append(f"Title: {entry['title']}")
    output_lines.append(f"Description: {entry['description']}")
    output_lines.append(f"Keywords: {', '.join(entry['keywords'])}")
    output_lines.append(f"URL: {entry['url']}")
    output_lines.append("-" * 40)

with open("pathways.txt", "w") as f:
    f.write("\n".join(output_lines))

print("✅ pathways.txt generated from pathways.json")
