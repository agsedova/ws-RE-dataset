import itertools
import json
import os
import re
import logging
from pathlib import Path
from scripts.commons import RELATION_TO_TYPES, PROPERTY_NAMES, DYGIE_RELATIONS
import sys
import argparse
import scripts.utils as utils

logger = logging.getLogger(__name__)


class PatternSearch:

    def __init__(self, path_to_data: str, path_to_patterns: str, path_to_output: str):
        self.path_to_data = path_to_data
        self.path_to_patterns = path_to_patterns
        self.path_to_output = path_to_output

        self.pattern_counter, self.matches_counter = 0, 0
        self.patterns_to_ids = {}
        self.relation_to_patterns = {}
        self.relation_to_types = {}
        self.ids_to_relations = DYGIE_RELATIONS
        self.stat_rel_matches = {}
        self.ids_to_patterns = {}

    def retrieve_patterns(self):
        Path(self.path_to_output).mkdir(parents=True, exist_ok=True)
        sys.stdout = open(os.path.join(self.path_to_output, "console"), 'w')

        self._get_relation_types_dict()
        self._collect_patterns()  # read patterns from the file
        self.ids_to_patterns = {patt_id: pattern for pattern, patt_id in self.patterns_to_ids.items()}

        if os.path.isdir(self.path_to_data):  # if we retrieve patterns in multiple files (input is a directory)
            self._search_patterns_multiple_files()
        elif os.path.isfile(self.path_to_data):  # if we retrieve patterns in a single file
            self._search_patterns_one_file()
        else:
            logger.info("Check your input! Now it's neither directory nor file")

    def _search_patterns_one_file(self):
        current_out_dir = self.path_to_output
        Path(current_out_dir).mkdir(parents=True, exist_ok=True)
        self.matches_counter = 0

        with open(self.path_to_data) as input_file:  # load data
            data = json.load(input_file)

        self.find_pattern_matches(data, current_out_dir)
        self.save_glob_stat_to_csv(os.path.join(current_out_dir, "_stat.csv"))
        sys.stdout.close()

    def _search_patterns_multiple_files(self):
        for curr_dir, _, files in os.walk(self.path_to_data):
            current_out_dir = os.path.join(self.path_to_output, "retrieved", curr_dir[-2:])
            Path(current_out_dir).mkdir(parents=True, exist_ok=True)
            for file in files:
                logger.info("Pattern search in file {}...".format(curr_dir + "/" + file))
                current_out_path = os.path.join(current_out_dir, file[:-11])
                self.matches_counter = 0

                with open(os.path.join(curr_dir, file)) as input_file:
                    data = json.load(input_file)

                self.find_pattern_matches(data, current_out_path)

        self.save_glob_stat_to_csv(os.path.join(self.path_to_output, "retrieved", "_stat.csv"))
        sys.stdout.close()

    def _get_pattern_id(self, pattern: str) -> int:
        """ Returns a pattern id from patterns_to_ids dict or creates a new pattern : pattern_id pair """
        if pattern not in self.patterns_to_ids.keys():
            pattern_id = self.pattern_counter
            self.patterns_to_ids[pattern] = pattern_id
            self.pattern_counter += 1
        else:
            pattern_id = self.patterns_to_ids[pattern]
        return pattern_id

    def add_pattern(self, relation_id: str, curr_pattern_id: int) -> None:
        if relation_id in self.relation_to_patterns.keys():
            self.relation_to_patterns[relation_id].update([curr_pattern_id])
        else:
            self.relation_to_patterns[relation_id] = set([curr_pattern_id])

    def _collect_patterns(self) -> None:
        """ Read patterns from file and save them to a dictionary {relation : [patterns]}"""
        with open(self.path_to_patterns, encoding="UTF-8") as inp:
            for line in inp.readlines():
                if line.startswith("#") or line == "\n":  # take only meaningful strings
                    continue
                relation, pattern = line.replace("\n", "").split(" ", 1)
                if relation not in RELATION_TO_TYPES.keys():  # we select only relations that dygie uses
                    continue
                relation_id = PROPERTY_NAMES[relation]
                curr_pattern_id = self._get_pattern_id(pattern)
                # add pattern to corresponding relation in relation_to_patterns dict if it is not there yet
                self.add_pattern(relation_id, curr_pattern_id)

        self._get_relation_types_dict()  # {relation : arg_types}
        self.ids_to_patterns = {patt_id: pattern for pattern, patt_id in self.patterns_to_ids.items()}

        # save patterns_to_ids to json file
        with open(self.path_to_output + "/patterns_ids.json", "w+") as rel_p:
            json.dump(self.ids_to_patterns, rel_p)

    def _get_relation_types_dict(self):
        for relation, relation_id in PROPERTY_NAMES.items():
            self.stat_rel_matches[relation_id] = 0
            self.relation_to_types[relation_id] = RELATION_TO_TYPES[relation]

    def preprocess_patterns(self, pattern: str) -> str:
        """ Turn raw patterns into good-looking regexes"""
        pattern = re.escape(pattern)
        prepr_pattern = re.sub("\\\\ \\\\\\*", "([ ][^ ]+){0,3}", pattern)  # * --> match 1 to 4 tokens
        prepr_pattern = re.sub("\\\\\\$ARG", "(A )?(a )?(The )?(the )?\\$ARG", prepr_pattern)  # add optional articles
        if "$ARG0" in prepr_pattern:  # a reflexive relation
            prepr_pattern = re.sub(u"\\$ARG0", "$ARG1", prepr_pattern, 1)
            prepr_pattern = re.sub(u"\\$ARG0", "$ARG2", prepr_pattern)
        return prepr_pattern

    def get_types_to_entities(self, doc: dict) -> dict:
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

    def get_abstract_for_comparing(self, sent: str, ent1: dict, ent2: dict, arg1: str, arg2: str) -> str:
        """ Substitute entities with "$ARG1" and "$ARG2" and do some refactoring needed for correct search """
        to_compare = sent[:ent1["start_sent"]] + arg1 + sent[ent1["end_sent"]:ent2["start_sent"]] + arg2 + \
                     sent[ent2["end_sent"]:]
        to_compare = re.sub(u'\\(', u"( ", to_compare)
        to_compare = re.sub(u'\\)', u" )", to_compare)
        to_compare = re.sub(u'\\,', ' ,', to_compare)
        to_compare = re.sub(u"\\'", " '", to_compare)
        return to_compare

    def _get_sentence_matches(self, args_output: dict) -> list:
        matches = []
        for rel, match in args_output.items():
            if len(match) > 0:
                for m in match:
                    m.append(self.ids_to_relations[rel])
                    matches.append(m)
        return matches

    def search_by_pattern(
            self, curr_args_output: dict, rel: str, patterns: set, to_compare: str, ent1: dict, ent2: dict,
            stat_rel: dict) -> None:
        """
        Look up each pattern from the list in string and, if there is a match, add corresponding info to
        curr_args_output dict
        """
        for pattern_id in patterns:
            pattern = self.preprocess_patterns(self.ids_to_patterns[pattern_id])  # convert pattern to regex
            match = re.search(pattern, to_compare)
            if match:
                curr_args_output[rel].append([ent1, ent2, pattern_id])
                # print_match_info(self, sent, rel, pattern, ent1, ent2)
                self.stat_rel_matches[rel] += 1  # increment whole statistics
                stat_rel[rel] += 1  # increment local sentence statistics
                self.matches_counter += 1

    def perform_search_in_sentence(
            self, sent: str, ent1: dict, ent2: dict, types: tuple, rel: str, patterns: set, curr_args_output: dict,
            stat_rel: dict):
        """ Look for pattern matches in a sentence """
        if ent1["start_sent"] < ent2["start_sent"] and ent1["label"] == types[0]:
            # $ARG1 studied at $ARG2, types = ("PERSON", "ORG"), ent1 = Bill ("PERSON"), ent2 = Stanford ("ORG")
            to_compare = self.get_abstract_for_comparing(sent, ent1, ent2, "$ARG1", "$ARG2")
            self.search_by_pattern(curr_args_output, rel, patterns, to_compare, ent1, ent2, stat_rel)
        elif ent1["start_sent"] < ent2["start_sent"] and ent1["label"] == types[1]:
            # $ARG2 alumnus $ARG1, types = ("PERSON", "ORG"), ent1 = Stanford ("ORG"), ent2 = Bill ("PERSON")
            to_compare = self.get_abstract_for_comparing(sent, ent1, ent2, "$ARG2", "$ARG1")
            self.search_by_pattern(curr_args_output, rel, patterns, to_compare, ent1, ent2, stat_rel)
        elif ent1["start_sent"] > ent2["start_sent"] and ent1["label"] == types[0]:
            # $ARG2 alumnus $ARG1, types = ("PERSON", "ORG"), ent1 = Bill ("PERSON"), ent2 = Stanford ("ORG")
            to_compare = self.get_abstract_for_comparing(sent, ent2, ent1, "$ARG2", "$ARG1")
            self.search_by_pattern(curr_args_output, rel, patterns, to_compare, ent1, ent2, stat_rel)
        elif ent1["start_sent"] > ent2["start_sent"] and ent1["label"] == types[1]:
            # $ARG1 studied at $ARG2, types = ("PERSON", "ORG"), ent1 = Stanford ("ORG"), ent2 = Bill ("PERSON")
            to_compare = self.get_abstract_for_comparing(sent, ent2, ent1, "$ARG1", "$ARG2")
            self.search_by_pattern(curr_args_output, rel, patterns, to_compare, ent1, ent2, stat_rel)

    def calculate_ent_indices(self, ent: dict, sent: dict) -> dict:
        """ Calculate new entity indices in a sentence """
        ent["start_sent"] = ent["start"] - sent["start"]
        ent["end_sent"] = ent["end"] - sent["start"]
        return ent

    def find_pattern_matches(self, data: list, output_path: str) -> None:
        # data = self.read_data()  # read file with sentences annotated by spacy
        all_docs = []
        stat_rel = {key: 0 for key in self.stat_rel_matches.keys()}
        for doc in data:
            types_to_entities = self.get_types_to_entities(doc)
            curr_args_output = {}
            for rel, patterns in self.relation_to_patterns.items():
                curr_args_output[rel] = []
                types = self.relation_to_types[rel]
                if not (types[0] in types_to_entities.keys() and types[1] in types_to_entities.keys()):
                    continue
                for ent1, ent2 in itertools.product(types_to_entities[types[0]], types_to_entities[types[1]]):
                    for sent in doc["sents"]:
                        # make sure that entities are in one sentence
                        if not (sent["start"] <= min(ent1["start"], ent2["start"]) <= sent["end"] and
                                sent["start"] <= max(ent1["end"], ent2["end"]) <= sent["end"]):
                            continue
                        # calculate entities indices according to the sentence
                        ent1 = self.calculate_ent_indices(ent1, sent)
                        ent2 = self.calculate_ent_indices(ent2, sent)

                        # extract the sentence we are working now with
                        sent_text = doc["text"][sent["start"]:sent["end"]]
                        self.perform_search_in_sentence(sent_text, ent1, ent2, types, rel, patterns, curr_args_output,
                                                        stat_rel)
            if any(curr_args_output.values()):  # check if there were any matches in doc
                matches = self._get_sentence_matches(curr_args_output)
                doc_dygie = utils.prepare_output_dygie(matches, doc)
                all_docs.append(doc_dygie)

        logger.info("Total match: {}".format(self.matches_counter))

        with open(output_path + "_dygie.json", "w+") as output_json:
            json.dump(all_docs, output_json)
        utils.save_loc_stat_to_csv(output_path + "_stat.csv", stat_rel, self.ids_to_relations)

        # return curr_args_output_dygie  # for testing purposes

    def save_glob_stat_to_csv(self, out_file: str) -> None:
        with open(out_file, 'w') as csvfile:
            for key in self.stat_rel_matches.keys():
                csvfile.write("%s\t%s\n" % (self.ids_to_relations[key], self.stat_rel_matches[key]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog=os.path.basename(sys.argv[0]))
    parser.add_argument("--path_to_patterns", help="")
    parser.add_argument("--path_to_output_files", help="")
    parser.add_argument("--path_to_retrieved_sentences", help="")
    args = parser.parse_args()
    PatternSearch(
        args.path_to_output_files, args.path_to_patterns, args.path_to_retrieved_sentences
    ).retrieve_patterns()
