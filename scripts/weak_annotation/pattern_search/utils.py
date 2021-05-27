import re


def preprocess_patterns(pattern: str) -> str:
    """ Turn raw patterns into good-looking regexes"""
    pattern = re.escape(pattern)
    prepr_pattern = re.sub("\\\\ \\\\\\*", "([ ][^ ]+){0,3}", pattern)  # * --> match 1 to 4 tokens
    prepr_pattern = re.sub("\\\\\\$ARG", "(A )?(a )?(The )?(the )?\\$ARG", prepr_pattern)  # add optional articles
    if "$ARG0" in prepr_pattern:  # a reflexive relation
        prepr_pattern = re.sub(u"\\$ARG0", "$ARG1", prepr_pattern, 1)
        prepr_pattern = re.sub(u"\\$ARG0", "$ARG2", prepr_pattern)
    return prepr_pattern


def get_abstract_for_comparing(sent: str, ent1: dict, ent2: dict, arg1: str, arg2: str) -> str:
    """ Substitute entities with "$ARG1" and "$ARG2" and do some refactoring needed for correct search """
    to_compare = sent[:ent1["start_sent"]] + arg1 + sent[ent1["end_sent"]:ent2["start_sent"]] + arg2 + \
                 sent[ent2["end_sent"]:]
    to_compare = re.sub(u'\\(', u"( ", to_compare)
    to_compare = re.sub(u'\\)', u" )", to_compare)
    to_compare = re.sub(u'\\,', ' ,', to_compare)
    to_compare = re.sub(u"\\'", " '", to_compare)
    return to_compare


def calculate_ent_indices(ent: dict, sent: dict) -> dict:
    """ Calculate new entity indices in a sentence """
    ent["start_sent"] = ent["start"] - sent["start"]
    ent["end_sent"] = ent["end"] - sent["start"]
    return ent


def get_types_to_entities(doc: dict) -> dict:
    types_to_entities = {}  # type: [ent_list]
    for ent in doc["ents"]:
        for token in doc["tokens"]:
            if token["start"] == ent["start"]:
                ent["start_id"] = int(token["id"])
            if token["end"] == ent["end"]:
                ent["end_id"] = int(token["id"])
        curr_label = ent["label"]
        if ent["label"] in types_to_entities.keys():
            types_to_entities[curr_label].append(ent)
        else:
            types_to_entities[curr_label] = [ent]
    return types_to_entities
