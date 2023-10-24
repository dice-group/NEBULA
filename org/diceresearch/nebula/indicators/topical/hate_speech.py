"""
Hate speech

Model is specialized to detect hate speech against women and immigrants. Latest version.
https://huggingface.co/cardiffnlp/twitter-roberta-base-hate-latest
"""

model_hatev2 = tweetnlp.load_model('hate')
results_hatespeech = model_hatev2.predict(text, return_probability=True)
hatespeech_infotext = "An algorithm has classified this statement as hate speech. Hate speech is highly negative and might be used for emotional manipulation."

# Check if the predicted label is "hate_speech" before printing
if results_hatespeech["label"] == "HATE":
    hate_probability = results_hatespeech["probability"]["HATE"]
    hatespeech_info = True, hatespeech_infotext
    print("An algorithm has classified this statement as hate speech with a probability of", hate_probability,". Hate speech is highly negative and might be used for emotional manipulation.")
else:
    print("This text is not classified as hate speech.")
    hatespeech_info = False
