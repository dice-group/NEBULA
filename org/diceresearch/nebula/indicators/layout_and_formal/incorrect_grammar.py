# Check for grammar and style errors
matches = tool.check(text)

# Initialize a list to store grammar errors and positions
grammar_positions = []

# Process the detected errors and save them in the list

for match in matches:
    error_message = match.message
    error_offset = match.offset
    for i in range(error_offset, error_offset + len(match.replacements[0])):
        grammar_positions.append(i)


grammar_infotext = ("Grammatical errors were identified. Since official news sources generally pay attention to correct "
                    "use of grammar, this might indicate unverified information.")

grammar_info = grammar_positions, grammar_infotext



# Output misspelled words (spelling errors)
if grammar_positions:
    print("Grammatical errors were identified. Since official news sources generally pay attention to correct use of "
          "grammar, this might indicate unverified information.")
    print("The following grammatical mistakes were identified:")
    for position in grammar_positions:
      print(f"Grammatical error: {error_message} (Position {error_position})")
else:
    print("No grammatical errors were identified.")

