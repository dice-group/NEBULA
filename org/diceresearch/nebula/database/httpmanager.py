import logging
import requests


def send_post(url, data, headers):
    # Send the POST request using the requests library
    response = requests.post(url, headers=headers, data=data)
    # Check the response status code
    if response.ok:
        logging.debug("POST request was successful!")
        logging.debug(str(response))
        return response.text
    else:
        logging.error("POST request failed with status code: {}".format(response.status_code))
        return response.json()


def send_post_json(url, json, headers):
    # Send the POST request using the requests library
    response = requests.post(url, json=json, headers=headers)
    # Check the response status code
    if response.ok:
        logging.debug("POST request was successful!")
        return response.text
    else:
        logging.error("POST request failed with status code: {}".format(response.status_code))
        return response.json()


def send_get(url, data):
    # Send the POST request using the requests library
    response = requests.get(url + data)
    # Check the response status code
    if response.ok:
        logging.debug("Get request was successful!")
        logging.debug(str(response))
        if response.headers.get('content-type') == 'application/json':
            return response.json()
        else:
            return response.text
    else:
        logging.error("POST request failed with status code: {}".format(response.status_code))
        return response.json()
