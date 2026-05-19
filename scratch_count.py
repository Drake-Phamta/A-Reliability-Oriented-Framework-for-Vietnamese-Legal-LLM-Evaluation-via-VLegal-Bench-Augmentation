import glob
import json
import os

print("---")
for f in glob.glob('annotations/*_annotated.jsonl'):
    total = 0
    skipped = 0
    with open(f, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                data = json.loads(line)
                if data.get('skipped', False):
                    skipped += 1
            except:
                pass
    name = os.path.basename(f)
    print(f"{name}|{total}|{skipped}")
print("---")
