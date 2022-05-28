# Corrector-Hackathon

This is a project of the UAB Multimedia Systems Hackathon.
The project is a website hosted in the Google Cloud that must be able to correct a text input and indicate faults.

https://corrector-sm.ew.r.appspot.com

![alt text](https://i.gyazo.com/2c2faec952fa46422f02a6f276eb7e56.gif)

### Local Installation

```bash
git clone https://github.com/ggcr/Corrector-Hackathon.git ~/.
cd ~/Corrector-Hackathon
pip3 install -r requirements.txt
python3 main.py
```

If you have successfully completed the steps at http: // localhost: 8080 you will be able to see the web UI.

To be able to run the website locally and make it functional, the project credentials in .json are required
These credentials are not in this repo.

If you do not have credentials, this message will be displayed on the console:
```
Google cloud .json credentials are missing! Unable to call Typewise API.
```
If you have credentials, you must uncomment line 73 from main.py:
```
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './corrector-sm-9ef8799680bd.json'
```

## Google Cloud
With the Google Cloud Build App, we are able to link this repository to the cloud instance. This will allow CI / CD to be made since every time a push is made to the main branch a Build Trigger will be activated in the cloud which will launch a new instance of our backend.

![alt text](https://github.com/ggcr/Corrector-Hackathon/blob/main/public/imgs/diagram.drawio.png)

### Cloud Builder: `cloudbuild.yaml` file
This trigger will deploy the app every time it detects changes to the `main` branch.
* To do this, you must give "App Engine Deployer" permissions to this cloud builder user.
```
steps:
- name: "gcr.io/cloud-builders/gcloud"
  args: ["app", "deploy"]
timeout: "1600s"
```
### App Engine: `app.yaml` file
This file will be used to deploy the app. It will be called by the cloud builder.
```
runtime: python39

handlers:
- url: /static
  static_dir: static
- url: /.*
  script: auto
```

There are two methods for correcting text:

### Local Python Lib: pyspellchecker
It is a python package that allows you to make local text corrections. It runs on the server and only on the server.

### External API: Typewise API
Using a cloud function we can call this external API and return the results.

In the 'correct' Cloud Function we have the following main.py code:
```python
def correct_sentence(request):
    import requests
    request_json = request.get_json()
    msg = ""
    if request.args and 'message' in request.args:
        msg = request.args.get('message')
    elif request_json and 'message' in request_json:
        msg = request_json['message']
    
    url = "https://typewise-ai.p.rapidapi.com/correction/whole_sentence"

    payload = {
        "text": msg,
        "keyboard": "QWERTY",
        "languages": [
            "en",
            "de",
            "es"
        ],
    }
    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Host": "typewise-ai.p.rapidapi.com",
        "X-RapidAPI-Key": "***************"
    }

    response = requests.request("POST", url, json=payload, headers=headers)
    return response.text
```

