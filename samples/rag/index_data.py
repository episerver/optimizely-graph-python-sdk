import json
import simplejson as simplejson
import logging
import os
import sys
import requests as requests

SOURCE = "imdb2"
HOST = os.getenv('HOST', "https://cg.optimizely.com")
SCHEMA_SYNC_ENDPOINT = "{}/api/content/v3/types?id={}".format(HOST, SOURCE)
DATA_SYNC_ENDPOINT = "{}/api/content/v2/data?id={}".format(HOST, SOURCE)
AUTH_TOKEN = os.getenv('AUTH_TOKEN', "<TOKEN>")
HEADERS = {
    'Content-Type': 'text/plain',
    'Authorization': 'Basic ' + AUTH_TOKEN
}

SCHEMA_FILE = "models/content_types.json"
MOVIE_FILE = "data/imdb_top_100.json"

LOG_DIR = os.getenv('LOG_DIR', "./")

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# reset data
def reset_data():
    response = requests.request("DELETE", DATA_SYNC_ENDPOINT + "&languages=en", headers=HEADERS)
    logging.info(response.text)


# load schema
def load_schemas():
    with open(SCHEMA_FILE) as f:
        schema = json.dumps(json.load(f))
        response = requests.request("PUT", SCHEMA_SYNC_ENDPOINT, headers=HEADERS, data=schema)
        logging.info(response.status_code)


# load the data
def load_data(source, content_type, language):
    with open(source) as f:
        contents = json.load(f)
        bulk = ""
        for i, content in enumerate(contents):
            content["ContentType"] = ["Record", content_type]
            content["Status"] = "Published"
            content["_rbac"] = "r:Everyone:Read"
            content["__typename"] = content_type
            content["genre___searchable"] = content.pop("genre")
            content["title___searchable"] = content.pop("title")
            content["overview___searchable"] = content.pop("overview")
            content["director___searchable"] = content.pop("director")
            content["cast___searchable"] = content.pop("cast")
            content.pop('llm_text', None)
            bulk += "{\"index\": { \"_id\": \"" + source + str(i) + "\", \"language_routing\": \"" + language + "\" }}\n" + simplejson.dumps(content, ignore_nan=True)
            if i != len(contents)-1:
                bulk += "\n"
        response = requests.request("POST", DATA_SYNC_ENDPOINT, headers=HEADERS, data=bulk)
        logging.info(response.text)


reset_data()
load_schemas()
load_data(MOVIE_FILE, "Movie", "en")