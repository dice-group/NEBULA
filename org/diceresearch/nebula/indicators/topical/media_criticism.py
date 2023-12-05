"""
Media criticism

Kate Starbird, Ahmer Arif, and Tom Wilson. 2019. Disinformation as Collaborative Work: Surfacing the Participatory
Nature of Strategic Information Operations. Proceedings of the ACM on Human-Computer Interaction 3, CSCW (Nov.
2019), 1–26. https://doi.org/10.1145/3359229
"""

# Dictionary Topic Media Criticism
dict_media = {
    "mainstream media": None,
    "lying media": None,
    "lying press": None,
    "fake media": None,
    "corporate media": None,
    "biased media": None,
    "propaganda machine": None,
    "controlled media": None,
    "establishment media": None,
    "presstitute": None,
    "MSM (Mainstream Media)": None,
    "agenda-driven media": None,
    "manipulative media": None,
    "media manipulation": None,
    "media bias": None,
    "media censorship": None,
    "media deception": None,
    "media distortion": None,
    "media propaganda": None,
    "media cover-up": None,
    "media control": None,
    "fake news": None,
    "alternative facts": None,
    "deep state media": None,
    "government-controlled media": None,
    "media elites": None,
    "corporate propaganda": None,
    "media spin": None,
}

# Initialize mediacriticism_count and mediacriticism_positions
mediacriticism_count = {}
mediacriticism_positions = []

# Test if terms from dict_media are in text (ignore upper/lower case)
for term in dict_media:
    pattern = re.compile(re.escape(term), re.IGNORECASE)
    matches = pattern.finditer(text)
    for match in matches:
        mediacriticism_count[term] = mediacriticism_count.get(term, 0) + 1
        # Append the positions of all matching characters to mediacriticism_positions list
        mediacriticism_positions.extend(range(match.start(), match.end()))

mediacriticism_infotext = "The topic media criticism has been identified. This topic is often associated with conspiracy theory content."

mediacriticism_info = mediacriticism_positions, mediacriticism_infotext

# Output media criticism
if mediacriticism_positions:
    print("The topic media criticism has been identified. This topic is often associated with conspiracy theory content.")
else:
    print("No terms of media criticism were identified.")