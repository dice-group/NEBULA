# Nebula Application
Code repository of the [NEBULA](https://nebula.peasec.de/) project.

## Environment
You can use a venv or a conda environment:
```
python -m venv nebula
source nebula/bin/activate
pip install -r requirements.txt
```
```
conda create -n nebula python=3.8.10
conda activate nebula
pip install -r requirements.txt
```

## Running the Application
To run the application, simply execute the main.py file using the command:
```
python main.py
```

The application will provide an API endpoint at:

```
http://127.0.0.1:5000
```

__Methods__

The Nebula application provides three methods: **check** ,**status**, **test or default**.

**Check Method**
The check method accepts both POST and GET requests, and requires a text input to check for accuracy. Optional language input can also be provided for the text.

For POST requests, the text [text] input and optional language input [lang] should be passed in the request body.
Below are some examples of the POST request.

```shell
curl http://nebulavm.cs.upb.de/check --header 'Content-Type: application/json' --data '{"lang": "en", "text": "Text I want to check"}'
```

```python
import requests

CHECK_URL = "http://nebulavm.cs.upb.de/check"
input = {
    'lang': 'en',
    'text': 'Text we want to check'
}
req = requests.post(CHECK_URL, json=input)
```


For GET requests, the  text [text] input should be passed in the URL arguments along with the optional language input [lang]. 
Below are some examples of the GET request.
```shell
curl --location 'http://nebulavm.cs.upb.de/check?lang=en&text=Text%20you%20want%20to%20check'
```
```python
import requests

CHECK_URL = "http://nebulavm.cs.upb.de/check?lang=en&text=Text%20we%20want%20to%20check"
req = requests.get(CHECK_URL)
```

Language specifications:
```
    - English : en
    - German : de
```
The check method will return a JSON object containing an ID for the text input. Here is an example of the JSON response:

```
{
    "id": "123"
}
```

**Status Method**
The status method also accepts both POST and GET requests, and requires an ID input to check the status of a previously submitted text input.

For POST requests, the ID input should be passed in the request body.
For GET requests, the ID input should be passed in the URL arguments.
The status method will return a JSON object containing information on the status of the checked text input. Here is an example of the JSON response:

```
{
    "id": "http://nebula.cs.uni-paderborn.de/id/123",
    "status": "Done",
    "text": "Text that has been checked",
    "lang": "Given language or detected language",
    "result": "The check result (WP5.1, either true / false or a numerical value)",
    "explanation": "Explanation generated by the explanation component (WP5.2)",
    "provenance": {
        "check-timestamp": "time at which the check has been started",
        "knowledge-date": "date of the latest news article known to the system",
        "model-date": "date of the model that has been used for classification"
    }
}
Note that the result value may differ during development phase.
```

**test or default**
accept Get and if the service is running answer with this
```
{
  "test": "ok"
}
```
