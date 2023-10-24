"""
Incorrect Spelling

Note: It is necessary to remove punctuation first because otherwise all punctuation marks are identified as spelling
mistakes because most spell checkers, including pyspellchecker, consider punctuation marks as separate words and
are typically not part of their dictionaries.
"""

# Remove punctuation from text
text_without_punctuation = text.translate(str.maketrans('', '', string.punctuation))

# Split text in words (exclude punctuation), tokenize with nltk
words_no_punct = word_tokenize(text_without_punctuation)

# SpellChecker-Object für English
spell = SpellChecker(language='en')

# Überprüfen der Rechtschreibung für jedes Wort im Text
misspelled_words = spell.unknown(words_no_punct)

# Initialize a list to store positions and words
misspelled_positions = []


for idx, word in enumerate(words_no_punct):
    if word not in spell:
        # Find the word in the original text
        word_start = text.find(word)
        if word_start != -1:
            for letter_position in range(word_start, word_start + len(word)):
                misspelled_positions.append(letter_position)


misspelled_infotext = ("Spelling errors were identified. Since official news sources generally pay attention to correct "
                       "spelling, this might indicate unverified information.")

misspelled_info = misspelled_positions, misspelled_infotext




# Output misspelled words (spelling errors)
if misspelled_positions:
    print("Spelling errors were identified. Since official news sources generally pay attention to correct spelling, "
          "this might indicate unverified information.")
    print("Misspelled letters found at the following positions in the text:")
    for position in misspelled_positions:
        print(f"Position: {position}")
else:
    print("No spelling errors were identified.")

