import re
from typing import Dict, Union


def convert_pattern_to_regex(pattern: str) -> str:
    """ Turn raw patterns into good-looking regexes"""
    pattern = re.escape(pattern)
    prepr_pattern = re.sub("\\\\ \\\\\\*", "([ ][^ ]+){0,3}", pattern)  # * --> match 1 to 4 tokens
    prepr_pattern = re.sub("\\\\\\$ARG", "(A )?(a )?(The )?(the )?\\$ARG", prepr_pattern)  # add optional articles
    if "$ARG0" in prepr_pattern:  # a reflexive relation
        prepr_pattern = re.sub(u"\\$ARG0", "$ARG1", prepr_pattern, 1)
        prepr_pattern = re.sub(u"\\$ARG0", "$ARG2", prepr_pattern)
    return prepr_pattern


def get_sent_for_comparing(ent1, ent2, types, sent) -> Union[str, None]:
    if ent1["start_sent"] < ent2["start_sent"] and ent1["label"] == types[0]:
        # $ARG1 studied at $ARG2, types = ("PERSON", "ORG"), ent1 = Bill ("PERSON"), ent2 = Stanford ("ORG")
        return process_sent(sent, ent1, ent2, "$ARG1", "$ARG2")

    elif ent1["start_sent"] < ent2["start_sent"] and ent1["label"] == types[1]:
        # $ARG2 alumnus $ARG1, types = ("PERSON", "ORG"), ent1 = Stanford ("ORG"), ent2 = Bill ("PERSON")
        return process_sent(sent, ent1, ent2, "$ARG2", "$ARG1")

    elif ent1["start_sent"] > ent2["start_sent"] and ent1["label"] == types[0]:
        # $ARG2 alumnus $ARG1, types = ("PERSON", "ORG"), ent1 = Bill ("PERSON"), ent2 = Stanford ("ORG")
        return process_sent(sent, ent2, ent1, "$ARG2", "$ARG1")

    elif ent1["start_sent"] > ent2["start_sent"] and ent1["label"] == types[1]:
        # $ARG1 studied at $ARG2, types = ("PERSON", "ORG"), ent1 = Stanford ("ORG"), ent2 = Bill ("PERSON")
        return process_sent(sent, ent2, ent1, "$ARG1", "$ARG2")

    else:
        return None


def process_sent(sent: str, ent1: Dict, ent2: Dict, arg1: str, arg2: str) -> str:
    """ Substitute entities with "$ARG1" and "$ARG2" and do some refactoring needed for correct search """
    to_compare = sent[:ent1["start_sent"]] + arg1 + sent[ent1["end_sent"]:ent2["start_sent"]] + arg2 + \
                 sent[ent2["end_sent"]:]
    to_compare = re.sub(u'\\(', u"( ", to_compare)
    to_compare = re.sub(u'\\)', u" )", to_compare)
    to_compare = re.sub(u'\\,', ' ,', to_compare)
    to_compare = re.sub(u"\\'", " '", to_compare)
    return to_compare
