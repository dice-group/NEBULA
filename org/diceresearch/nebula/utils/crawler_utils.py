import json
import ssl
import urllib
from collections import Counter

from newsplease import NewsPlease
from tqdm import tqdm


def update_bar(q, total):
    pbar = tqdm(total=total, position=0, leave=True)
    while True:
        x = q.get()
        pbar.update(x)


headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
    'Accept-Encoding': 'none',
    'Accept-Language': 'en-US,en;q=0.8',
    'Connection': 'keep-alive'}
context = ssl.SSLContext()


def crawl_file(file, save, bar_queue):
    """
    Loops through news articles in a json array. For each news article, it downloads the html again and adds the new
    article text to the same json object
    :param bar_queue: tqdm to update simultaneously
    :param save: Filepath where to save the new articles
    :param file: JSON file to read from
    :return:
    """
    fail_counter = Counter()

    with open(file) as fin:
        data = json.load(fin)

    for item in data:
        bar_queue.put_nowait(1)
        # get url
        article_url = item['url']
        if article_url is None:
            continue

        # get html
        try:
            request = urllib.request.Request(article_url, None, headers)
            response = urllib.request.urlopen(request, context=context, timeout=10)
            article_data = response.read()
            article_html = article_data.decode("utf8")
        except Exception as e:
            fail_counter.update([str(e)])
            continue

        # get article from html
        if article_html is not None:
            article = NewsPlease.from_html(article_html, url=None)
            if article is None:
                fail_counter.update(["Empty article"])
                continue
        else:
            fail_counter.update(["Article html is empty"])
            continue

        # check if new text is empty or None
        article_ob = article.get_serializable_dict()
        article_newtext = article_ob['maintext']
        if not bool(article_newtext):
            fail_counter.update(["New article text is empty"])
            continue

        # append to jsonl
        with open(save, 'a+', encoding='utf8') as f:
            item['new_content'] = article_newtext
            f.write('{0}\n'.format(json.dumps(item)))

    return fail_counter