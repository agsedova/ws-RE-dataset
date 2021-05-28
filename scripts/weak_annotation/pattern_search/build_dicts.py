import json
from typing import Dict, Tuple
from scripts.weak_annotation.commons import RELATION_TO_TYPES, PROPERTY_NAMES
from scripts.weak_annotation.pattern_search.text_processing import convert_pattern_to_regex
from scripts.weak_annotation.pattern_search.utils import get_pattern_id


def collect_patterns(path_to_patterns: str, path_to_output: str) -> Tuple[Dict, Dict]:
    """ Read patterns from file and save them to a dictionary {relation : [pattern_regex]}"""

    pattern_counter = 0
    relation2patterns, pattern2id, id2pattern = {}, {}, {}

    with open(path_to_patterns, encoding="UTF-8") as inp:
        for line in inp.readlines():
            if line.startswith("#") or line == "\n":  # take only meaningful strings
                continue
            relation, pattern = line.replace("\n", "").split(" ", 1)
            if relation not in RELATION_TO_TYPES.keys():  # we select only relations that dygie uses
                continue
            relation_id = PROPERTY_NAMES[relation]
            curr_pattern_id, pattern_counter = get_pattern_id(pattern, pattern2id, pattern_counter)

            # add pattern to corresponding relation in rel2patterns dict if it is not there yet
            relation2patterns = add_pattern(relation_id, curr_pattern_id, relation2patterns)

    id2pattern = {patt_id: convert_pattern_to_regex(pattern) for pattern, patt_id in pattern2id.items()}

    # save pattern2id to json file
    with open(path_to_output + "/patterns_ids.json", "w+") as rel_p:
        json.dump(id2pattern, rel_p)

    return relation2patterns, id2pattern


def get_types2entities(doc: Dict) -> Dict:
    """
        Returns a dictionary of all entities that doc contains: {entity_type : [entities]}
    :param doc: SpaCy annotated text saved as a dictionary (fields: "doc_id", "text", "ents", "sents", "tokens")
    """
    types2entities = {}  # {type:[ent_list]}
    for ent in doc["ents"]:
        for token in doc["tokens"]:
            if token["start"] == ent["start"]:
                ent["start_id"] = int(token["id"])
            if token["end"] == ent["end"]:
                ent["end_id"] = int(token["id"])
        curr_label = ent["label"]
        if ent["label"] in types2entities.keys():
            types2entities[curr_label].append(ent)
        else:
            types2entities[curr_label] = [ent]
    return types2entities


def add_pattern(relation_id: str, curr_pattern_id: int, relation2patterns: Dict) -> Dict:
    if relation_id in relation2patterns.keys():
        relation2patterns[relation_id].update([curr_pattern_id])
    else:
        relation2patterns[relation_id] = set([curr_pattern_id])
    return relation2patterns


def get_relation_types_dict() -> Dict:
    relation2types = {}
    for relation, relation_id in PROPERTY_NAMES.items():
        relation2types[relation_id] = RELATION_TO_TYPES[relation]
    return relation2types
