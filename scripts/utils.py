import logging

logger = logging.getLogger(__name__)

def prepare_output_dygie(matches, doc):
    """

    """
    doc_ent, doc_rel, doc_idx, doc_rel_ann, doc_pattern = [], [], [], [], []
    for sent in doc["sents"]:
        sent_ent, sent_rel, sent_idx, sent_rel_ann, sent_pattern = [], [], [], [], []
        for token in doc["tokens"]:
            if int(token["start"]) >= int(sent["start"]) and int(token["end"]) <= int(sent["end"]):
                sent_ent.append(doc["text"][token["start"]:token["end"]])
                sent_idx.append([token["start"], token["end"]])
        for match in matches:
            ent1, ent2, pattern, relation = match[0], match[1], match[2], match[3]
            if min(ent1["start"], ent2["start"]) >= int(sent["start"]) and \
                    max(ent1["end"], ent2["end"]) <= int(sent["end"]):
                sent_rel.append(sorted([ent1["start_id"], ent2["start_id"], ent1["end_id"], ent2["end_id"]]) +
                                [relation])
                sent_rel_ann.append(relation)
                sent_pattern.append(sorted([ent1["start_id"], ent2["start_id"], ent1["end_id"], ent2["end_id"]]) +
                                    [pattern] + [relation])
        doc_idx.append(sent_idx)
        doc_ent.append(sent_ent)
        doc_rel.append(sent_rel)
        doc_rel_ann.append(list(dict.fromkeys(sent_rel_ann)))
        doc_pattern.append(sent_pattern)
    doc_entry = {"doc_key": doc["doc_id"], "sentences": doc_ent, "relations": doc_rel,
                 "tokensToOriginalIndices": doc_idx, "annotatedPredicates": doc_rel_ann, "patterns": doc_pattern}
    return doc_entry


def save_loc_stat_to_csv(out_file: str, stat: dict, ids_to_relations: dict) -> None:
    with open(out_file, 'w') as csvfile:
        for key in stat.keys():
            csvfile.write("%s\t%s\n" % (ids_to_relations[key], stat[key]))


def abstracts_to_json_format(annotation, wiki_input):
    """ Prepare annotated abstracts_test to save them in .json format"""
    return {wiki_input["id"]: {"url": wiki_input["url"], "title": wiki_input["title"], "text": wiki_input["text"],
                               "sentences": [sent.as_dict() for sent in annotation]}}


def find_nth(string: str, substring: str, n: int) -> int:
    """ Find index of the nth element in the string"""
    return string.find(substring) if n == 1 else string.find(substring, find_nth(string, substring, n - 1) + 1)


def print_match_info(sent, rel, pattern, ent1, ent2):
    logger.info("New match! Relation:{}; entity1: {}; entity2: {}; pattern {}; Sentence: {}".format(
        rel, sent[ent1["start_sent"]:ent1["end_sent"]], sent[ent2["start_sent"]:ent2["end_sent"]], pattern, sent))

def log_section(text: str, logger: logging) -> None:
    """
    Prints a section.
    :param text:  text to print
    :param logger: logger object
    """
    logger.info("==============================================================")
    logger.info(text)
    logger.info("==============================================================")
