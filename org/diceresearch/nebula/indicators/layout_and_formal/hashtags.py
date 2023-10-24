'''
Parameters to be modified accordingly

HASHTAG_COUNT_THRESHOLD: The minimum number of hashtags to be considered before designation as an indicator.
'''
HASHTAG_COUNT_THRESHOLD = 5

def detect_excessive_hashtag_usage(input_text):
  def extract_hash_tags_unique(input_text):
    return list(set(part[1:] for part in input_text.split() if part.startswith('#')))

  hashtag_list = extract_hash_tags_unique(input_text)
  hashtag_count = len(hashtag_list)
  if hashtag_list and hashtag_count >= HASHTAG_COUNT_THRESHOLD:
      print("The excessive use of hashtags can be used by fake news outlets and sources to manipulate search results "
            "and trending topics by connecting a topic to unrelated, possibly more popular, topics.")
      print("Serious outlets are not known to use them and thus you should exercise caution by checking against "
            "reputable and trustworthy sources.")
      print("Total number of detected hashtags (without duplicates): {}".format(hashtag_count))
  else:
    print("No excessive use of hashtags beyond set thresholds.")

# Testing / Sanity check
input_text = "Hello #World!"
detect_excessive_hashtag_usage