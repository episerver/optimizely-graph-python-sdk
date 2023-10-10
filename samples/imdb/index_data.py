#!/usr/bin/env python

import csv
import json
import collections
import logging
import os
import sys

import requests as requests

# aliases
OrderedDict = collections.OrderedDict

SOURCE = "imdb"
HOST = os.getenv('HOST', "http://localhost:4000")
SCHEMA_SYNC_ENDPOINT = "{}/api/content/v3/types?id={}".format(HOST, SOURCE)
DATA_SYNC_ENDPOINT = "{}/api/content/v2/data?id={}".format(HOST, SOURCE)
AUTH_TOKEN = os.getenv('AUTH_TOKEN', "<TOKEN>")
HEADERS = {
    'Content-Type': 'text/plain',
    'Authorization': 'Basic ' + AUTH_TOKEN
}

SCHEMA_FILE = "models/content_types.json"
NAME_BASICS_FILE = 'data/name.basics.small.tsv'
TITLE_BASICS_FILE = 'data/title.basics.small.tsv'
TITLE_RATINGS_FILE = 'data/title.ratings.small.tsv'

STRING_ARRAY_FIELDS = ["ContentType", "knownForTitles", "primaryProfession___searchable", "genres___searchable"]
INT_FIELDS = ["birthYear", "deathYear", "startYear", "endYear", "runtimeMinutes", "numVotes"]
FLOAT_FIELDS = ["averageRating"]
BOOLEAN_FIELDS = ["isAdult"]

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
def load_data(source, content_type):
    data = []
    with open(source, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t', quotechar='"')
        header = next(reader)
        header.append("ContentType")
        header.append("Status")
        header.append("_rbac")
        header.append("__typename")
        count = 0
        idx = 0
        for (is_last_check, row) in is_last(reader):
            for i, value in enumerate(row):
                if header[i] in STRING_ARRAY_FIELDS:
                    row[i] = value.split(",") if "," in value else [value]
                elif header[i] in INT_FIELDS:
                    row[i] = int(value) if value != "\\N" else None
                elif header[i] in FLOAT_FIELDS:
                    row[i] = float(value) if value != "\\N" else None
                elif header[i] in BOOLEAN_FIELDS:
                    row[i] = value.lower() in ["1"]
            row.append(["Record", content_type])
            row.append("Published")
            row.append("r:Everyone:Read")
            row.append(content_type)
            data.append(OrderedDict(zip(header, row)))

            count += 1
            idx += 1
            if count == 100 or is_last_check:
                count = 0
                bulk = '\n'.join(
                    "{\"index\": { \"_id\": \"" + source + str(
                        idx + i) + "\", \"language_routing\": \"en\" }}\n" + json.dumps(v) for (i, v) in
                    enumerate(data))
                response = requests.request("POST", DATA_SYNC_ENDPOINT, headers=HEADERS, data=bulk)
                logging.info(response.text)
                data = []


def is_last(itr):
    old = next(itr)
    for new in itr:
        yield False, old
        old = new
    yield True, old


# reset_data()
load_schemas()
load_data(NAME_BASICS_FILE, "Actor")
load_data(TITLE_BASICS_FILE, "Title")
load_data(TITLE_RATINGS_FILE, "Rating")
