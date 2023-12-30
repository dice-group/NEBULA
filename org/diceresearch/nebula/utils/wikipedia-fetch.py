import pandas as pd
import json
import wikipediaapi

# Read FEVER dataset
FEVER = "./train_fever.jsonl"
df = pd.read_json(FEVER, lines=True)

# Fetch evidence from Wikipedia
wiki = wikipediaapi.Wikipedia('Test/1.0 (<My Email>) testing')
total_count = 0
to_add = []  # Buffer to store data before writing to the output file
cant = set()  # Store pages that could not be retrieved
output_file = "output_fever.jsonl"
save_frequency = 1000  # Save output every 1000 iterations

try:
    # Iterate through each row in the FEVER dataset
    for index, row in df.iterrows():
        evidence_info = row['evidence']
        # Iterate through evidence items for each row
        for ev in evidence_info[0]:
            total_count += 1
            print(f"Total {total_count}")
            # Skip evidence items with insufficient information
            if len(ev) < 4:
                continue
            page_name = ev[2]
            # Skip if the page name is None
            if page_name is None:
                continue
            try:
                # Fetch the Wikipedia page
                page = wiki.page(page_name)
                # Check if the page exists
                if page.exists():
                    # Create a new item to store the text fetched
                    new_item = {
                        "id": row['id'],
                        "verifiable": row['verifiable'],
                        "label": row['label'],
                        "claim": row['claim'],
                        "evidence": row['evidence'],
                        "text": page.text,
                    }
                    to_add.append(new_item)
                else:
                    # Add non-existing page names to the set
                    cant.add(page_name)
            except wikipediaapi.HTTPTimeoutError as e:
                print(f"Error: {e}")
            except Exception as e:
                print(f"Error: {e}")

            # Periodically save the progress
            if total_count % save_frequency == 0:
                with open(output_file, 'a') as f:
                    for item in to_add:
                        json.dump(item, f)
                        f.write('\n')
                to_add = []  # Clear the buffer after saving

except Exception as e:
    print(f"Error: {e}")

finally:
    print(f"Found {len(cant)} pages not working")

    # Save any remaining items in the buffer
    with open(output_file, 'a') as f:
        for item in to_add:
            json.dump(item, f)
            f.write('\n')
