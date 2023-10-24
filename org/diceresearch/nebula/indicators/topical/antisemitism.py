"""
Antisemitism

Sven Ove Hansson. 2017. Science Denial as a Form of Pseudoscience. Studies in History and Philosophy of Science Part
A 63 (June 2017), 39–47. https://doi.org/10.1016/j.shpsa.2017.05.002

Kate Starbird. 2017. Examining the Alternative Media Ecosystem Through the Production of Alternative Narratives of
Mass Shooting Events on Twitter. Proceedings of the International AAAI Conference on Web and Social Media 11, 1
(May 2017), 230–239. https://doi.org/10.1609/icwsm.v11i1.14878

Dictionary for antisemitic terms** by American Jewish Committee:
https://www.ajc.org/sites/default/files/pdf/2021-10/AJC_TranslateHate-Glossary-October2021.pdf
"""

dict_antisemitism = {
    "blood libel": None,
    "cosmopolitan elite": None,
    "elite cosmopolitan": None,
    "deadly exchange": None,
    "deiceide": None,
    # "(((", ")))": None, #an antisemitic symbol used to highlight the names of Jewish individuals or organizations
    # owned by Jews
    "from the river to the sea": None,
    "globalists": None,
    "the goyim know": None,
    # catchphrase used to impersonate and mock Jews and the antisemitic conspiracy theories connected to them
    "Holocough": None,  # call by the far-right to spread coronavirus to Jews to infect and kill them
    "Holohoax": None,  # Holocaust denial --> weitere Begriffe??
    "jew down": None,
    "jewish lightning": None,
    "Khazars": None,
    "Khazaria": None,
    "kosher tax": None,
    "New world order": None,
    "deepstate": None,
    "not the real Jews": None,
    "fake Jew": None,
    "poisoning the well": None,
    "poison the well": None,
    "Protocols of the Elders of Zion": None,
    "Rothschild": None,  # depends on context
    "Zionist Occupied Government": None
}

# Some terms are too broad and unspecific. Therefore, they should only be filtered if they appear in connection to
# some keywords
keywords_antisemitism = ["jew", "jewish", "zionist", "zio"]

dict_antisemitism2 = {
    "cabal": None,
    "clan": None,
    "conspiracy": None,
    "control": None,
    "cowardice": None,
    "coward": None,
    "cowardly": None,
    "dual loyalty": None,
    "greed": None,
    "capitalist": None,
    "communists": None,
    "lobby": None,
    "NWO": None,  # New world order
    "silencing": None,
    "silence": None,
    "slave owners": None,
    "ZOG": None,  # Zionist Occupied Government
}

# Initialise antisemitism_count and antisemitism_info
antisemitism_count = {}
antisemitism_info = {term: [] for term in dict_antisemitism}

# Test if terms from dict_antisemitism are in text (ignore upper/lower case)
for term in dict_antisemitism:
    pattern = re.compile(re.escape(term), re.IGNORECASE)
    matches = pattern.finditer(text)
    for match in matches:
        if term not in antisemitism_count:
            antisemitism_count[term] = 0
        antisemitism_count[term] += 1
        antisemitism_info[term].append((match.start(), match.end()))

# Check if any of the keywords is in the text
keywords_antisemitism_present = any(keyword in text for keyword in keywords_antisemitism)

if keywords_antisemitism_present:
    for term in dict_antisemitism2:
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        matches = pattern.finditer(text)
        for match in matches:
            if term not in antisemitism_count:
                antisemitism_count[term] = 0
            antisemitism_count[term] += 1
            antisemitism_count[term].append((match.start(), match.end()))

# Flag, to control output
output_flag = True

# Results
for term, count in antisemitism_count.items():
    if output_flag:
        print("Antisemitic language has been identified.")
        print("The following terms are indicators for (covert) antisemitism:")
        output_flag = False  # set to false in order to oppress output

    if antisemitism_info[term]:
        print(f"Term: {term} (Position: {antisemitism_info[term]})")
    else:
        print("There are no indicators for antisemitic language.")
