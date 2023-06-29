import requests
import settings


def coref_resolution(text):
    properties = {
        'annotators': 'coref',
        'outputFormat': 'json',
        'ner.useSUTime': 'false'
    }

    data = {
        'properties': str(properties),
        'pipelineLanguage': 'en',
        'annotator': 'coref',
        'text': text
    }

    response = requests.post(settings.crrApi, params={'properties': str(properties)}, data=data)
    response_json = response.json()

    return response_json['corefs']

def replace_coreferences(text, coreferences):
    mentions = {}
    for coref_id, mentions_list in coreferences.items():
        mention_text = mentions_list[0]['text']
        for mention in mentions_list[1:]:
            mention_text = mention_text.replace(mention['text'], mentions_list[0]['text'])
        mentions[coref_id] = mention_text

    for coref_id, mention in mentions.items():
        text = text.replace('[' + coref_id + ']', mention)

    return text