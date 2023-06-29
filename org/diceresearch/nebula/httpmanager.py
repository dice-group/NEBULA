import logging
import settings
import requests

logging.basicConfig(level = logging.INFO)

# Set the data to be sent in the POST request
# data = {
#    "key1": "value1",
#    "key2": "value2"
# }

def send_post(url, data, headers):
    # Send the POST request using the requests library
    response = requests.post(url, headers=headers, data=data)
    # Check the response status code
    if response.status_code == 200:
        logging.info("POST request was successful!")
        logging.info(str(response))
        # if(response.headers.get('content-type') == 'application/json'):
        #    return response.json()
        # else :
        return response.text
    else:
        logging.error("POST request failed with status code: " + str(response.status_code))
        return response.json()


def send_post_json(url, json, headers):
    # Send the POST request using the requests library
    response = requests.post(url, json=json, headers=headers)
    # Check the response status code
    if response.status_code == 200:
        logging.info("POST request was successful!")
        return response.text
    else:
        logging.error("POST request failed with status code:" + response.status_code)
        return response.json()


def send_get(url, data):
    # Send the POST request using the requests library
    response = requests.get(url + data)
    # Check the response status code
    if response.status_code == 200:
        logging.info("Get request was successful!")
        logging.info(str(response))
        if (response.headers.get('content-type') == 'application/json'):
            return response.json()
        else:
            return response.text
    else:
        logging.error("POST request failed with status code: "+ response.status_code)
        return response.json()
