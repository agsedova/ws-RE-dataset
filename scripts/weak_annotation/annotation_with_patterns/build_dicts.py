import os
from typing import Dict, Tuple
from weak_annotation.commons import RELATION_TO_TYPES, PROPERTY_NAMES
from weak_annotation.annotation_with_patterns.text_processing import convert_pattern_to_regex
from weak_annotation.annotation_with_patterns.utils import get_pattern_id

import pandas as pd


def collect_knodle_patterns(path_to_patterns: str, path_to_output: str, relation2relation_id: Dict):

    patterns = []
    relation2patterns, pattern2id, id2pattern = {}, {}, {}

    with open(path_to_patterns, encoding="UTF-8") as inp:
        for line in inp.readlines():
            if line.startswith("#") or line == "\n":  # take only meaningful strings
                continue
            relation, curr_pattern = line.replace("\n", "").split(" ", 1)

            try:
                relation_id = relation2relation_id[relation]
                if relation_id not in relation2patterns.keys():
                    relation2patterns[relation_id] = []
            except KeyError:
                continue

            if curr_pattern not in pattern2id:
                pattern_id = len(pattern2id)
                pattern2id[curr_pattern] = pattern_id
                relation2patterns[relation_id].append(pattern_id)

                patterns.append(
                    {"pattern_id": pattern_id, "pattern": curr_pattern,
                     "pattern_regex": convert_pattern_to_regex(curr_pattern),
                     "relation": {relation}, "relation_id": {relation_id}
                     })
            else:
                for pattern in patterns:
                    if pattern["pattern"] == curr_pattern:
                        pattern["relation"].add(relation)
                        pattern["relation_id"].add(relation_id)

            # curr_pattern_id, pattern_counter = get_pattern_id(pattern, pattern2id, pattern_counter)
            # add pattern to corresponding relation in rel2patterns dict if it is not there yet
            # relation2patterns = add_pattern(relation_id, curr_pattern_id, relation2patterns)
    patterns = pd.DataFrame(patterns)
    patterns.to_csv(os.path.join(os.path.split(path_to_output)[0], "patterns.csv"), index=False)

    return patterns, relation2patterns


def collect_dygie_patterns(path_to_patterns: str, path_to_output: str) -> Tuple[pd.DataFrame, Dict, Dict, Dict]:
    """ Read patterns from file and save them to a dictionary {relation : [pattern_regex]}"""

    patterns = pd.DataFrame(columns=["pattern", "pattern_id", "relation"])

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

            patterns = patterns.append(
                {"pattern": pattern, "pattern_id": curr_pattern_id, "pattern_regex": convert_pattern_to_regex(pattern),
                 "relation": relation, "relation_id": relation_id}, ignore_index=True
            )

    id2pattern_raw = {patt_id: pattern for pattern, patt_id in pattern2id.items()}
    id2pattern = {patt_id: convert_pattern_to_regex(pattern) for pattern, patt_id in pattern2id.items()}

    # save pattern2id to json file
    # with open(path_to_output + "/patterns_ids.json", "w+") as rel_p:
    #     json.dump(pattern_id2pattern, rel_p)
    patterns.to_csv(os.path.join(path_to_output, "patterns.csv"), index=False)

    return patterns, relation2patterns, id2pattern, id2pattern_raw


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
