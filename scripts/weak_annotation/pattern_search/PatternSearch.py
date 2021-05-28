import itertools
import json
import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Tuple

from scripts.weak_annotation.commons import DYGIE_RELATIONS
import sys
import scripts.utils as utils
from scripts.weak_annotation.pattern_search.build_dicts import get_types2entities, get_relation_types_dict, \
    collect_patterns
from scripts.weak_annotation.pattern_search.text_processing import get_abstract_for_comparing
from scripts.weak_annotation.pattern_search.utils import calculate_ent_indices, save_glob_stat_to_csv

logger = logging.getLogger(__name__)


class PatternSearch:
    """

    """

    def __init__(self, path_to_data: str, path_to_patterns: str, path_to_output: str):
        """

        :param path_to_data:
        :param path_to_patterns:
        :param path_to_output:
        """
        self.path_to_data = path_to_data
        self.path_patterns = path_to_patterns
        self.path_out = path_to_output
        Path(self.path_out).mkdir(parents=True, exist_ok=True)

        self.matches_counter = 0

        self.id2relation = DYGIE_RELATIONS
        self.rel2types = get_relation_types_dict()        # build self.rel2types dict {relation : arg_types}
        self.stat_rel_matches = dict.fromkeys(self.rel2types.keys(), 0)        # intialize statistics
        self.rel2patterns, self.id2pattern = collect_patterns(self.path_patterns, self.path_out)

    def retrieve_patterns(self):
        Path(self.path_out).mkdir(parents=True, exist_ok=True)
        sys.stdout = open(os.path.join(self.path_out, "console"), 'w')

        if os.path.isdir(self.path_to_data):  # if we retrieve patterns in multiple files (input is a directory)
            self._search_patterns_multiple_files()
        elif os.path.isfile(self.path_to_data):  # if we retrieve patterns in a single file
            self._search_patterns_in_file(inp=self.path_to_data, out=self.path_out)
        else:
            logger.info("Check your input! It's neither directory nor file")

        save_glob_stat_to_csv(self.stat_rel_matches, os.path.join(self.path_out, '_stat.csv'))
        sys.stdout.close()

    def _search_patterns_multiple_files(self):
        """ The function performs search for patterns in samples that are stored in different files """
        for curr_dir, _, files in os.walk(self.path_to_data):
            current_out_dir = os.path.join(self.path_out, "retrieved", curr_dir[-2:])
            Path(current_out_dir).mkdir(parents=True, exist_ok=True)
            for file in files:
                self._search_patterns_in_file(
                    inp=os.path.join(curr_dir, file), out=os.path.join(current_out_dir, file[:-11])
                )

    def _search_patterns_in_file(self, inp: str, out: str):
        """ The function performs search for patterns in samples from one files """
        Path(out).mkdir(parents=True, exist_ok=True)
        self.matches_counter = 0

        # load list of dictionaries containing with wiki articles
        with open(inp) as input_file:
            if input_file != '.DS_Store':
                try:
                    data = json.load(input_file)
                except json.decoder.JSONDecodeError:
                    return

        # perform search in each wiki article
        stat_rel = {key: 0 for key in self.stat_rel_matches.keys()}
        all_docs = [self.find_pattern_matches(doc, stat_rel) for doc in data]
        all_docs = list(filter(lambda x: x is not None, all_docs))

        with open(out + "_dygie.json", "w+") as out_j:
            json.dump(all_docs, out_j)
        utils.save_loc_stat_to_csv(out + "_stat.csv", stat_rel, self.id2relation)

        logger.info(f'Pattern search in {inp}. Total match: {self.matches_counter}')

    def find_pattern_matches(self, wiki_page: Dict, stat_rel: Dict) -> Tuple[Dict, None]:
        """
        :param wiki_page: dictionary that contains the information about a wiki article
        ("doc_id", "text", "ents", "sents", "tokens").
        :param stat_rel:
        """

        types2entities = get_types2entities(wiki_page)        # dict {entity_type : [entities]}
        rel2retrieved_args = {}

        for rel_id, pattern_ids in self.rel2patterns.items():
            rel2retrieved_args[rel_id] = []
            types = self.rel2types[rel_id]          # entity types that are acceptable for this relation

            # if there are no entities of these types, skip the sentence
            if not (types[0] in types2entities.keys() and types[1] in types2entities.keys()):
                continue

            for ent1, ent2 in itertools.product(types2entities[types[0]], types2entities[types[1]]):
                for sent in wiki_page["sents"]:       # for each sentence in a document
                    # make sure that entities are in one sentence
                    if not (sent["start"] <= min(ent1["start"], ent2["start"]) <= sent["end"] and
                            sent["start"] <= max(ent1["end"], ent2["end"]) <= sent["end"]):
                        continue

                    # calculate entities' indices according to the sentence
                    ent1 = calculate_ent_indices(ent1, sent)
                    ent2 = calculate_ent_indices(ent2, sent)

                    # extract the sentence we are working now with
                    sent_text = wiki_page["text"][sent["start"]:sent["end"]]
                    # look for patterns in this sentence
                    self.perform_search_in_sentence(
                        sent_text, ent1, ent2, types, rel_id, pattern_ids, rel2retrieved_args, stat_rel
                    )

        if any(rel2retrieved_args.values()):  # check if there were any matches in doc
            matches = self._get_sentence_matches(rel2retrieved_args)
            args_output = utils.prepare_output_dygie(matches, wiki_page)
            return args_output
        else:
            return None

    def _get_sentence_matches(self, args_output: dict) -> list:
        matches = []
        for rel, match in args_output.items():
            if len(match) > 0:
                for m in match:
                    m.append(self.id2relation[rel])
                    matches.append(m)
        return matches

    def search_by_pattern(
            self, curr_args_output: dict, rel: str, patterns: set, to_compare: str, ent1: dict, ent2: dict,
            stat_rel: dict
    ) -> None:
        """
        Look up each pattern from the list in string and, if there is a match, add corresponding info to
        curr_args_output dict
        """
        for pattern_id in patterns:
            pattern_regex = self.id2pattern[pattern_id] # take pattern regex
            match = re.search(pattern_regex, to_compare)
            if match:
                curr_args_output[rel].append([ent1, ent2, pattern_id])
                # print_match_info(self, sent, rel, pattern, ent1, ent2)
                self.stat_rel_matches[rel] += 1  # increment whole statistics
                stat_rel[rel] += 1  # increment local sentence statistics
                self.matches_counter += 1

    def perform_search_in_sentence(
            self, sent: str, ent1: dict, ent2: dict, types: tuple, rel: str, patterns: set, curr_args_output: dict,
            stat_rel: dict
    ) -> None:
        """
         Look for pattern matches in a sentence "
        """
        if ent1["start_sent"] < ent2["start_sent"] and ent1["label"] == types[0]:
            # $ARG1 studied at $ARG2, types = ("PERSON", "ORG"), ent1 = Bill ("PERSON"), ent2 = Stanford ("ORG")
            to_compare = get_abstract_for_comparing(sent, ent1, ent2, "$ARG1", "$ARG2")
            self.search_by_pattern(curr_args_output, rel, patterns, to_compare, ent1, ent2, stat_rel)
        elif ent1["start_sent"] < ent2["start_sent"] and ent1["label"] == types[1]:
            # $ARG2 alumnus $ARG1, types = ("PERSON", "ORG"), ent1 = Stanford ("ORG"), ent2 = Bill ("PERSON")
            to_compare = get_abstract_for_comparing(sent, ent1, ent2, "$ARG2", "$ARG1")
            self.search_by_pattern(curr_args_output, rel, patterns, to_compare, ent1, ent2, stat_rel)
        elif ent1["start_sent"] > ent2["start_sent"] and ent1["label"] == types[0]:
            # $ARG2 alumnus $ARG1, types = ("PERSON", "ORG"), ent1 = Bill ("PERSON"), ent2 = Stanford ("ORG")
            to_compare = get_abstract_for_comparing(sent, ent2, ent1, "$ARG2", "$ARG1")
            self.search_by_pattern(curr_args_output, rel, patterns, to_compare, ent1, ent2, stat_rel)
        elif ent1["start_sent"] > ent2["start_sent"] and ent1["label"] == types[1]:
            # $ARG1 studied at $ARG2, types = ("PERSON", "ORG"), ent1 = Stanford ("ORG"), ent2 = Bill ("PERSON")
            to_compare = get_abstract_for_comparing(sent, ent2, ent1, "$ARG1", "$ARG2")
            self.search_by_pattern(curr_args_output, rel, patterns, to_compare, ent1, ent2, stat_rel)

        return curr_args_output  # for testing purposes


    # def _get_pattern_id(self, pattern: str) -> int:
    #     """ Returns a pattern id from pattern2id dict or creates a new pattern : pattern_id pair """
    #     if pattern not in self.pattern2id.keys():
    #         pattern_id = self.pattern_counter
    #         self.pattern2id[pattern] = pattern_id
    #         self.pattern_counter += 1
    #     else:
    #         pattern_id = self.pattern2id[pattern]
    #     return pattern_id

    # def _collect_patterns(self) -> None:
    #     """ Read patterns from file and save them to a dictionary {relation : [patterns]}"""
    #     with open(self.path_patterns, encoding="UTF-8") as inp:
    #         for line in inp.readlines():
    #             if line.startswith("#") or line == "\n":  # take only meaningful strings
    #                 continue
    #             relation, pattern = line.replace("\n", "").split(" ", 1)
    #             if relation not in RELATION_TO_TYPES.keys():  # we select only relations that dygie uses
    #                 continue
    #             relation_id = PROPERTY_NAMES[relation]
    #             curr_pattern_id = self._get_pattern_id(pattern)
    #             # add pattern to corresponding relation in rel2patterns dict if it is not there yet
    #             self.rel2patterns = add_pattern(relation_id, curr_pattern_id)
    #
    #     self.id2pattern = {patt_id: pattern for pattern, patt_id in self.pattern2id.items()}
    #
    #     # save pattern2id to json file
    #     with open(self.path_out + "/patterns_ids.json", "w+") as rel_p:
    #         json.dump(self.id2pattern, rel_p)


    # def _search_patterns_one_file(self):
    #     current_out_dir = self.path_out
    #     Path(current_out_dir).mkdir(parents=True, exist_ok=True)
    #     self.matches_counter = 0
    #
    #     with open(self.path_to_data) as input_file:  # load data
    #         data = json.load(input_file)
    #
    #     self.find_pattern_matches(data, current_out_dir)
    #     self.save_glob_stat_to_csv(os.path.join(current_out_dir, "_stat.csv"))
    #     sys.stdout.close()

    # def _search_patterns_multiple_files(self):
    #     for curr_dir, _, files in os.walk(self.path_to_data):
    #         current_out_dir = os.path.join(self.path_out, "retrieved", curr_dir[-2:])
    #         Path(current_out_dir).mkdir(parents=True, exist_ok=True)
    #         for file in files:
    #             current_out_path = os.path.join(current_out_dir, file[:-11])
    #             logger.info("Pattern search in file {}...".format(curr_dir + "/" + file))
    #             self.matches_counter = 0
    #
    #             with open(os.path.join(curr_dir, file)) as input_file:
    #                 data = json.load(input_file)
    #
    #             self.find_pattern_matches(data, current_out_path)
    #
    #     self.save_glob_stat_to_csv(os.path.join(self.path_out, "retrieved", "_stat.csv"))
    #     sys.stdout.close()


# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(prog=os.path.basename(sys.argv[0]))
#     parser.add_argument("--path_patterns", help="")
#     parser.add_argument("--path_to_output_files", help="")
#     parser.add_argument("--path_to_retrieved_sentences", help="")
#     args = parser.parse_args()
#     PatternSearch(
#         args.path_to_output_files, args.path_patterns, args.path_to_retrieved_sentences
#     ).retrieve_patterns()
