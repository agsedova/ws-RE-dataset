import re


def convert_pattern_to_regex(pattern: str) -> str:
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
