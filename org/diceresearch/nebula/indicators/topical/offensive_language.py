"""
Offensive language

https://github.com/cardiffnlp/tweetnlp
"""
lp.load_model('offensive')  # Or `model = tweetnlp.Offensive()`
results_offensive = model_offensive.predict(text, return_probability=True)
offensivelanguage_infotext = "An algorithm has identified offensive language in this statement. Offensive language is highly negative and might be used for emotional manipulation."

# Check if the predicted label is "hate_speech" before printing
if results_offensive ["label"] == "offensive":
    offensive_probability = results_offensive["probability"]["offensive"]
    offensivelanguage_info = True, offensivelanguage_infotext
    print("An algorithm has identified offensive language in this text with a probability of", offensive_probability,". Offensive language might be used for emotional manipulation.")
else:
    print("This text is not classified as hate speech.")
    offensivelanguage_info = False
model_offensive = tweetn

