import logging
import random
from typing import Dict, List, Tuple
import numpy as np

logger = logging.getLogger(__name__)


def log_section(text: str, logger: logging) -> None:
    """
    Prints a section.
    :param text:  text to print
    :param logger: logger object
    """
    logger.info("==============================================================")
    logger.info(text)
    logger.info("==============================================================")


def get_sentence_matches(args_output: Dict, id2relation: Dict) -> List:
    """
    The function gets from the dict {rel: sample, where relation matched} only the samples that match some
    relation, adds relation name to it and return as a list of matches.
    """
    matches = []
    for rel, match in args_output.items():
        if len(match) > 0:
            for m in match:
                m.append({"rel_id": rel})
                m.append({"rel": id2relation[rel]})
                matches.append(m)
    return matches


def prepare_output_dygie(matches: List, doc: Dict) -> Dict:
    doc_ent, doc_rel, doc_idx, doc_rel_ann, doc_pattern = [], [], [], [], []
    for sent in doc["sents"]:
        sent_ent, sent_rel, sent_idx, sent_rel_ann, sent_pattern = [], [], [], [], []
        for token in doc["tokens"]:
            if int(token["start"]) >= int(sent["start"]) and int(token["end"]) <= int(sent["end"]):
                sent_ent.append(doc["text"][token["start"]:token["end"]])
                sent_idx.append([token["start"], token["end"]])
        for match in matches:
            ent1, ent2, pattern, relation = match[0], match[1], match[2]["pattern_id"], match[4]["rel"]
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


def prepare_output_knodle(matches: List, doc: Dict, num_patterns: int) -> Tuple[List, List, np.ndarray, List, List]:
    """
    The function gets list of matches and a document where these matches were found and transform them to Knodle
    specific format.
    """
    processed_entity_pairs = {}
    samples_cut, samples_full, arg1_poses, arg2_poses = [], [], [], []
    rule_matches_z = np.zeros((0, num_patterns))

    for match in matches:
        pattern_id = match[2]["pattern_id"]
        arg1_pos = (match[0]["start"], match[0]["end"])
        arg2_pos = (match[1]["start"], match[1]["end"])
        entities_start = min(arg1_pos[0], arg2_pos[0])
        entities_end = max(arg1_pos[1], arg2_pos[1])

        if (entities_start, entities_end) in processed_entity_pairs.items():
            rule_matches_z[processed_entity_pairs[(entities_start, entities_end)]][pattern_id] = 1
        else:
            arg1_poses.append(arg1_pos)
            arg2_poses.append(arg2_pos)

            for sent in doc["sents"]:
                if entities_start >= sent["start"] and entities_end <= sent["end"]:
                    sample_full = doc["text"][sent["start"]:sent["end"]]
                    samples_cut.append(doc["text"][entities_start:entities_end])
                    samples_full.append(sample_full)

                    z_row = np.zeros(num_patterns)
                    z_row[pattern_id] = 1
                    rule_matches_z = np.vstack((rule_matches_z, z_row))

                    samples_cut_neg, z_row_neg, arg1_pos_neg, arg2_pos_neg = create_negative_entry(
                            doc, sent, entities_start, entities_end, num_patterns
                    )

                    samples_cut.append(samples_cut_neg)
                    samples_full.append(sample_full)
                    rule_matches_z = np.vstack((rule_matches_z, z_row_neg))
                    arg1_poses.append(arg1_pos_neg)
                    arg2_poses.append(arg2_pos_neg)

            # save information about the matched entity pair and corresponding row in z matrix (last added positive row)
            processed_entity_pairs[(entities_start, entities_end)] = rule_matches_z.shape[0] - 2

    return samples_cut, samples_full, rule_matches_z, arg1_poses, arg2_poses


def create_negative_entry(
        doc: Dict, sent: Dict, forbidden_entities_start: int, forbidden_entities_end: int, z_matrix_2nd_dim: int
) -> Tuple[str, np.ndarray, Tuple, Tuple]:

    # take random tokens to make a negative sample
    negative_entities = random.sample(
        [t for t in doc["tokens"] if t["start"] >= sent["start"] and t["end"] <= sent["end"] and
         t["start"] != forbidden_entities_start and t["end"] != forbidden_entities_end
         and t["start"] != t["end"]], 2
    )

    arg1_pos_neg = (negative_entities[0]["start"], negative_entities[0]["end"])
    arg2_pos_neg = (negative_entities[1]["start"], negative_entities[1]["end"])

    neg_entities_start = min(negative_entities[0]["start"], negative_entities[1]["start"])
    neg_entities_end = max(negative_entities[0]["end"], negative_entities[1]["end"])

    samples_cut_negative = doc["text"][neg_entities_start:neg_entities_end]
    z_row = np.zeros((1, z_matrix_2nd_dim))

    return samples_cut_negative, z_row, arg1_pos_neg, arg2_pos_neg


def create_negative_entry_without_z_row(
        doc: Dict, sent: Dict, forbidden_entities_start: int, forbidden_entities_end: int
) -> Tuple[str, Tuple, Tuple]:

    # take random tokens to make a negative sample
    negative_entities = random.sample(
        [t for t in doc["tokens"] if t["start"] >= sent["start"] and t["end"] <= sent["end"] and
         t["start"] != forbidden_entities_start and t["end"] != forbidden_entities_end
         and t["start"] != t["end"]], 2
    )

    arg1_pos_neg = (negative_entities[0]["start"], negative_entities[0]["end"])
    arg2_pos_neg = (negative_entities[1]["start"], negative_entities[1]["end"])

    neg_entities_start = min(negative_entities[0]["start"], negative_entities[1]["start"])
    neg_entities_end = max(negative_entities[0]["end"], negative_entities[1]["end"])

    samples_cut_negative = doc["text"][neg_entities_start:neg_entities_end]

    return samples_cut_negative, arg1_pos_neg, arg2_pos_neg


def save_loc_stat_to_csv(out_file: str, stat: dict, id2relation: dict) -> None:
    with open(out_file, 'w') as csvfile:
        for key in stat.keys():
            csvfile.write("%s\t%s\n" % (id2relation[key], stat[key]))


def abstracts_to_json_format(annotation, wiki_input):
    """ Prepare annotated abstracts_test to save them in .json format"""
    return {wiki_input["id"]: {"url": wiki_input["url"], "title": wiki_input["title"], "text": wiki_input["text"],
                               "sentences": [sent.as_dict() for sent in annotation]}}


def print_match_info(sent, rel, pattern, ent1, ent2):
    logger.info("New match! Relation:{}; entity1: {}; entity2: {}; pattern {}; Sentence: {}".format(
        rel, sent[ent1["start_sent"]:ent1["end_sent"]], sent[ent2["start_sent"]:ent2["end_sent"]], pattern, sent))


def return_entity_pair(sent: str, ent1: Dict, ent2: Dict) -> str:
    ent1_text = sent[ent1["start_sent"]:ent1["end_sent"]].replace(" ", "_")
    ent2_text = sent[ent2["start_sent"]:ent2["end_sent"]].replace(" ", "_")
    return "$".join([ent1_text, ent2_text])
