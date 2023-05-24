import requests

# Set the data to be sent in the POST request
#data = {
#    "key1": "value1",
#    "key2": "value2"
#}

def sendpost(url,data,headers):
    # Send the POST request using the requests library
    response = requests.post(url,headers=headers, data=data)
    # Check the response status code
    if response.status_code == 200:
        print("POST request was successful!")
        print(str(response))
        if(response.headers.get('content-type') == 'application/json'):
            return response.json()
        else :
            return response.text
    else:
        print("POST request failed with status code:", response.status_code)
        return response.json()

def sendpostjson(url,json,headers):
    # Send the POST request using the requests library
    response = requests.post(url,json=json,headers=headers)
    # Check the response status code
    if response.status_code == 200:
        print("POST request was successful!")
        return response.json()
    else:
        print("POST request failed with status code:", response.status_code)
        return response.json()

def sendget(url,data):
    # Send the POST request using the requests library
    response = requests.get(url+data)
    # Check the response status code
    if response.status_code == 200:
        print("Get request was successful!")
        print(str(response))
        if(response.headers.get('content-type') == 'application/json'):
            return response.json()
        else :
            return response.text
    else:
        print("POST request failed with status code:", response.status_code)
        return response.json()



