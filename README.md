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
http://127.0.0.1:8080
```

__Methods__

The Nebula application provides three methods: **check** ,**status**, **rawstatus**, and **test**.

**Check Method**
The check method accepts both POST and GET requests, and requires a text input to check for accuracy. Optional language input can also be provided for the text.

For POST requests, the text [text] input and optional language input [lang] should be passed in the request body.
Below are some examples of the POST request.

```shell
curl http://nebulavm.cs.upb.de/check --header 'Content-Type: application/json' --data '{"lang": "en", "text": "Text I want to check"}'
```

Python example:
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
Python example:
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
**Required parameters**

Name   | Description
------ | ---------------------------------------------
`text` | The input text to be verified by NEBULA. <br /> **Required**: &#9745;  |             
`lang` | Language of the input text. <br />  If the language is not set to 'en' and translation is not provided, NEBULA will first translate it to english. <br /> **Required**: &#9744; <br /> **Default**: `nd`  |
`token` | The device token to notify of an available fact-checking result. <br /> **Required**: &#9744; <br /> **Default**: `None`  |
`translation` | The english translation of the input text. <br /> **Required**: &#9744; <br /> **Default**: `None`  |                       |




**Status/Rawstatus Method**
The status method also accepts both POST and GET requests, and requires an ID input to check the status of a previously submitted text input.

For POST requests, the ID input should be passed in the request body.
For GET requests, the ID input should be passed in the URL arguments.
The status method will return a JSON object containing information on the status of the checked text input. Here is an example of the JSON response:

`/status` example result:
```
{
   "request_id": "123",
   "request_status": "DONE",
   "stage_number": 8,
   "input_text": "A fake text we are checking.",
   "veracity_label": "UNRELIABLE",
   "indicator_check": {},
   "provenance": {
      "knowledge_date": "2023-05-31",
      "model_date": "2023-07-13",
      "final_model_date": "2023-12-06"
   }
}
```

`/rawstatus` example result:
```
{
   "request_id": "123",
   "request_timestamp": "2023-12-08#14:15:53.731819",
   "request_status": "DONE",
   "error": null,
   "stage_number": 8,
   "input_language": "nd",
   "input_text": "A fake text we are checking.",
   "translated_text": "A fake text we are checking.",
   "coref_text": "A fake text we are checking.",
   translation_status": "SKIPPED",
   "coref_status": "COMPLETED",
   "claim_check_status": "COMPLETED",
   "evidence_retrieval_status": "COMPLETED",
   "stance_detection_status": "COMPLETED",
   "wise_one_status": "COMPLETED",
   "wise_rnn_status": "COMPLETED",
   "indicator_check_status": "COMPLETED",
   "wise_rnn_score": "0.6114559",
   "veracity_label": "UNRELIABLE",
   "indicator_check": {},
   "sentences": [
      {
         "index": 0,
         "text":  "A fake text we are checking.",
         "score": 0.4784439666,
         "evidences": [
            {
               "evidence_text": "An evidence text",
               "url": "https://en.wikipedia.org/wiki/Evidence1",
               "elastic_score": 180.06766,
               "stance_score": "0.0643975213314539"
            },
            {
               "evidence_text": "Another evidence text",
               "url": "https://en.wikipedia.org/wiki/Evidence2",
               "elastic_score": 157.697,
               "stance_score": "0.055446140273465304"
            }
         ],
         "wise_score": 0.6114559173583984
      }
   ],
   "provenance": {
      "knowledge_date": "2023-05-31",
      "model_date": "2023-07-13",
      "final_model_date": "2023-12-06"
   }
}
```

Note that the result value may differ during development phase.

**Required parameters**

Name   | Description
------ | ---------------------------------------------
`id` | The request ID. <br /> Output ID of the `/check` endpoint. <br /> **Required**: &#9745; |    

**test or default** accept Get and if the service is running answer with this
```
{"Status":"OK"}
```

## Training WISE
WISE is the last veracity step of our pipeline.
It consists of an MLP for the single-claim score aggregation and an RNN for the the overall result.

```shell
python3 run_train.py --train-file train_file.jsonl --test-file test_file.jsonl
python3 run_train_wise.py --train-file train_file.jsonl --test-file test_file.jsonl
```

**Required parameters**

Name   | Description
------ | ---------------------------------------------
`--train-file` | Training split in jsonl format. <br /> **Required**: &#9745; | 
`--val-file` | Validation split in jsonl format. <br /> **Required**: &#9744; <br /> **Default**: None | 
`--test-file` | Testing split in jsonl format. <br /> **Required**: &#9745;  | 
`--save` | Path to save the model. <br /> **Required**: &#9744; <br /> **Default**: `resources/model.pt` | 
`--top-k` | Top k evidence to be retained. <br /> **Required**: &#9744; <br /> **Default**: `10` | 
`--dropout` | Dropout rate. <br /> **Required**: &#9744; <br /> **Default**: `0.5`| 
`--epochs` | Number of epochs. <br /> **Required**: &#9744; <br /> **Default**: `150`| 
`--batch-size` | Batch size. <br /> **Required**: &#9744; <br /> **Default**: `512`| 
`--learning-rate` | Learning rate. <br /> **Required**: &#9744; <br /> **Default**: `1e-4` | 
