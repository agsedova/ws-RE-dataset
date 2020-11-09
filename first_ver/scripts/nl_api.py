import requests
import json


def main(text):
    # Diffbot token is neccessary
    # params = {"fields": 'entities,statements', "token": "bddbe1c67b6e449d8d29c17eff80d703"}
    params = {"fields": 'entities', "token": "bddbe1c67b6e449d8d29c17eff80d703"}
    body = [{"content": text, "lang": "en"}]
    headers = {'accept': 'application/json', "Content-Type": "application/json"}

    page = requests.post(url="https://nl.diffbot.com/v1/", params=params, json=body, headers=headers)

    try:
        page.url
        # here the parsed json with annotations
        return page.json()
    except ValueError:  # includes simplejson.decoder.JSONDecodeError
        print('Decoding JSON has failed, the abstract is skipped')

    # with open('ann_test.json5', 'w') as outfile:
    #     json.dump(page.json(), outfile)

    # # single mention representation
    # page.json()[0]['entities'][0]['mentions']
