from typing import Dict, Union
import ast
import pandas as pd


def get_token_text(doc, token):
    return doc["text"][token["start"]:token["end"]]


def ents_in_sent(doc, ent1, ent2) -> Union[Dict, None]:
    # check if both entities are in one sentence
    for sent in doc["sents"]:
        if ent1["start"] >= sent["start"] and ent2["start"] >= sent["start"] and ent1["end"] <= sent["end"] and \
                ent2["end"] <= sent["end"]:
            return sent
    return None

