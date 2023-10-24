"""
Incorrect Punctuation Mark Usage
"""

# Define a RegEx pattern to match excessive punctuation (more than one consecutive punctuation mark)
excessive_punctuation_pattern = r'[?!.]{2,}'

# Find matches using the RegEx pattern
matches = re.finditer(excessive_punctuation_pattern, text)

# Initialize a list to store positions and excessive punctuation sequences
punctuation_positions = []

# Process and store matches
for match in matches:
    start_pos = match.start()
    end_pos = match.end()
    punctuation_sequence = text[start_pos:end_pos]
    punctuation_positions.extend(range(start_pos, end_pos))

punctuation_infotext = "Excessive punctuation attracts attention. This might be used for emotional manipulation."

punctuation_info = punctuation_positions, punctuation_infotext



# Print positions and excessive punctuation sequences
if punctuation_positions:
    print("Excessive punctuation attracts attention. This might be used for emotional manipulation.")
    print("The following punctuation marks are used excessively:")
    for positions in punctuation_positions:
        print(f"Excessive punctuation: '{punctuation_sequence}' (Position: {start_pos}-{end_pos})")
else:
    print("No excessive punctuation has been detected in the input text.")

