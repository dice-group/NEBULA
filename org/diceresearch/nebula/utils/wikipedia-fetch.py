import json
import pandas as pd

import wikipediaapi

# read FEVER
FEVER = "train_fever.jsonl"
df = pd.read_json(FEVER, lines=True)


# fetch evidence from wikipedia
wiki = wikipediaapi.Wikipedia('Test/1.0 (<My Email>) testing')
total_count = 0
to_add = set()
cant = set()
for index, row in df.iterrows():
    evidence_info = row['evidence']
    for ev in evidence_info[0]:
        total_count += 1
        print(f"Total {total_count}")
        if len(ev) < 4:
            continue
        page_name = ev[2]
        if page_name is None:
            continue
        page = wiki.page(page_name)
        if page.exists():
            new_item = list()
            new_item.append(page.text)
            new_item.append(row['claim'])
            new_item.append(row['label'])
            to_add.add(new_item)
        else:
            cant.add(page_name)
print(f"Found {len(cant)} pages not working")


# save file as jsonl
