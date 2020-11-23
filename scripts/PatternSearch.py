import itertools
import json
import os
import re
from pathlib import Path
from scripts.commons import RELATION_TO_TYPES, PROPERTY_NAMES, DYGIE_RELATIONS
import sys


# todo: ? maybe add additional regex for datum


class PatternSearch:

    def __init__(self, path_to_data, path_to_patterns, path_to_output):
        self.path_to_data = path_to_data
        self.path_to_patterns = path_to_patterns
        self.path_to_output = path_to_output

        self.pattern_counter, self.matches_counter = 0, 0
        self.patterns_to_ids = {}
        self.relation_to_patterns = {}
        self.relation_to_types = {}
        self.stat_rel_matches = {}

        self.get_relation_types_dict()
        self.collect_patterns()
        self.ids_to_patterns = {patt_id: pattern for pattern, patt_id in self.patterns_to_ids.items()}

    def read_data(self, path):
        with open(path) as input_file:
            data = json.load(input_file)
        return data

    def get_relation_types_dict(self):
        for relation, relation_id in PROPERTY_NAMES.items():
            self.stat_rel_matches[relation_id] = 0
            self.relation_to_types[relation_id] = RELATION_TO_TYPES[relation]

    def get_pattern_id(self, pattern):
        """ Returns a pattern id from patterns_to_ids dict or creates a new pattern : pattern_id pair """
        if pattern not in self.patterns_to_ids.keys():
            pattern_id = self.pattern_counter
            self.patterns_to_ids[pattern] = pattern_id
            self.pattern_counter += 1
        else:
            pattern_id = self.patterns_to_ids[pattern]
        return pattern_id

    def add_pattern(self, relation_id, curr_pattern_id):
        if relation_id in self.relation_to_patterns.keys():
            self.relation_to_patterns[relation_id].update([curr_pattern_id])
        else:
            self.relation_to_patterns[relation_id] = set([curr_pattern_id])

    def collect_patterns(self):
        """ Read patterns from file and save them to a dictionary {relation : [patterns]}"""
        # {relation : [patterns]}, {pattern : pattern_id}
        with open(self.path_to_patterns, encoding="UTF-8") as inp:
            for line in inp.readlines():
                if line.startswith("#") or line == "\n":  # take only meaningful strings
                    continue
                relation, pattern = line.replace("\n", "").split(" ", 1)
                if relation not in RELATION_TO_TYPES.keys():  # we select only relations that dygie uses
                    continue
                relation_id = PROPERTY_NAMES[relation]
                curr_pattern_id = self.get_pattern_id(pattern)
                # add pattern to corresponding relation in relation_to_patterns dict if it is not there yet
                self.add_pattern(relation_id, curr_pattern_id)

        # patterns_to_ids = dict((patt_id, patt) for patt_id, patt in enumerate(set(patterns))) # {pattern : pattern_id}
        self.get_relation_types_dict()  # {relation : arg_types}
        self.ids_to_patterns = {patt_id: pattern for pattern, patt_id in self.patterns_to_ids.items()}

        # save patterns_to_ids to json file
        with open(self.path_to_output + "/patterns_ids.json", "w+") as rel_p:
            json.dump(self.ids_to_patterns, rel_p)

    def preprocess_patterns(self, pattern):
        """ Turn raw patterns into good-looking regexes"""
        # todo: add optional articles - check if there isn't any yet!
        pattern = re.escape(pattern)
        prepr_pattern = re.sub("\\\\ \\\\\\*", "([ ][^ ]+){0,3}", pattern)  # * --> match 1 to 4 tokens
        # prepr_pattern = re.sub("\\$ARG", "\\\\$ARG", prepr_pattern)  # escape $ in $ARG1 and $ARG2
        # add optional articles
        # prepr_pattern = re.sub("\\\\\\$ARG", "(A)?(a)?(The)?(the)? \\$ARG", prepr_pattern)
        # if there is reflexive relation
        if "$ARG0" in prepr_pattern:
            prepr_pattern = re.sub(u"\\$ARG0", "$ARG1", prepr_pattern, 1)
            prepr_pattern = re.sub(u"\\$ARG0", "$ARG2", prepr_pattern)
        return prepr_pattern

    def get_types_to_entities(self, doc):
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

    def get_abstract_for_comparing(self, sent, ent1, ent2, arg1, arg2):
        """ Substitute entiies with "$ARG1" and "$ARG2" and do some refactoring needed for correct search """
        to_compare = sent[:ent1["start_sent"]] + arg1 + sent[ent1["end_sent"]:ent2["start_sent"]] + arg2 + \
                     sent[ent2["end_sent"]:]
        to_compare = re.sub(u'\\(', u"( ", to_compare)
        to_compare = re.sub(u'\\)', u" )", to_compare)
        to_compare = re.sub(u'\\,', ' ,', to_compare)
        to_compare = re.sub(u"\\'", " '", to_compare)
        return to_compare

    def get_sentence_matches(self, args_output):
        matches = []
        for rel, match in args_output.items():
            if len(match) > 0:
                for m in match:
                    m.append(rel)
                    matches.append(m)
        return matches

    def print_match_info(self, sent, rel, pattern, ent1, ent2):
        print("New match! Relation:{}; entity1: {}; entity2: {}; pattern {}; Sentence: {}".format(
            rel, sent[ent1["start_sent"]:ent1["end_sent"]], sent[ent2["start_sent"]:ent2["end_sent"]], pattern, sent))

    def search_by_pattern(self, curr_args_output, rel, patterns, to_compare, ent1, ent2, stat_rel):
        """
        Look up each pattern from the list in string and, if there is a match, add corresponding info to
        curr_args_output dict
        """
        for pattern_id in patterns:
            pattern = self.preprocess_patterns(self.ids_to_patterns[pattern_id])  # convert pattern to regex
            match = re.search(pattern, to_compare)
            if match:
                # curr_args_output[rel].append([min(ent1["start"], ent2["start"]), min(ent1["end"], ent2["end"]),
                #                               max(ent1["start"], ent2["start"]), max(ent1["end"], ent2["end"]),
                #                               pattern_id])
                curr_args_output[rel].append([ent1, ent2, pattern_id])
                # print_match_info(self, sent, rel, pattern, ent1, ent2)

                self.stat_rel_matches[rel] += 1  # increment whole statistics
                stat_rel[rel] += 1  # increment local sentence statistics
                self.matches_counter += 1

    # todo: shouldn't be return curr_args_output?

    def perform_search_in_sentence(self, sent, ent1, ent2, types, rel, patterns, curr_args_output, stat_rel):
        """ Look for pattern matches in a sentence """
        # if not (sent["start"] <= min(ent1["start"], ent2["start"]) <= sent["end"] and
        #         sent["start"] <= max(ent1["end"], ent2["end"]) <= sent["end"]):
        #     return
        if ent1["start_sent"] < ent2["start_sent"] and ent1["label"] == types[0]:
            # usual case
            # $ARG1 studied at $ARG2, types = ("PERSON", "ORG")
            # e.g. "Bill studied at Stanford", ent1 = Bill ("PERSON"), ent2 = Stanford ("ORG")
            to_compare = self.get_abstract_for_comparing(sent, ent1, ent2, "$ARG1", "$ARG2")
            self.search_by_pattern(curr_args_output, rel, patterns, to_compare, ent1, ent2, stat_rel)
        elif ent1["start_sent"] < ent2["start_sent"] and ent1["label"] == types[1]:
            # $ARG2 alumnus $ARG1, types = ("PERSON", "ORG"), ent1 = Stanford ("ORG"), ent2 = Bill ("PERSON")
            # e.g. "Stanford alumnus Bill"
            to_compare = self.get_abstract_for_comparing(sent, ent1, ent2, "$ARG2", "$ARG1")
            self.search_by_pattern(curr_args_output, rel, patterns, to_compare, ent1, ent2, stat_rel)
        elif ent1["start_sent"] > ent2["start_sent"] and ent1["label"] == types[0]:
            # $ARG2 alumnus $ARG1, types = ("PERSON", "ORG"), ent1 = Bill ("PERSON"), ent2 = Stanford ("ORG")
            # e.g. "Stanford alumnus Bill"
            to_compare = self.get_abstract_for_comparing(sent, ent2, ent1, "$ARG2", "$ARG1")
            self.search_by_pattern(curr_args_output, rel, patterns, to_compare, ent1, ent2, stat_rel)
        elif ent1["start_sent"] > ent2["start_sent"] and ent1["label"] == types[1]:
            # $ARG1 studied at $ARG2, types = ("PERSON", "ORG")
            # e.g. "Bill studied at Stanford", ent1 = Stanford ("ORG"), ent2 = Bill ("PERSON")
            to_compare = self.get_abstract_for_comparing(sent, ent2, ent1, "$ARG1", "$ARG2")
            self.search_by_pattern(curr_args_output, rel, patterns, to_compare, ent1, ent2, stat_rel)
        return curr_args_output

    # todo: shouldn't be return curr_args_output?

    def calculate_ent_indices(self, ent, sent):
        """ Calculate new entity indices in a sentence """
        ent["start_sent"] = ent["start"] - sent["start"]
        ent["end_sent"] = ent["end"] - sent["start"]
        return ent
    #
    # def get_ent_id(self, doc, ent):
    #     ent[""] = doc.ents.
    #     return

    def search_patterns(self, data, output_path):
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
                        curr_args_output = self.perform_search_in_sentence(sent_text, ent1, ent2, types, rel, patterns,
                                                                           curr_args_output, stat_rel)
            if any(curr_args_output.values()):  # check if there were any matches in doc
                curr_args_output_dygie = self.prepare_output_dygie(curr_args_output, doc)
                all_docs.append(curr_args_output_dygie)

        print("Total match:", self.matches_counter)

        with open(output_path + "_dygie.json", "w+") as output_json:
            json.dump(all_docs, output_json)
        self.save_loc_stat_to_csv(output_path + "_stat.csv", stat_rel)

        return curr_args_output_dygie      # for testing purposes

    def start_somewhat_function(self):
        sys.stdout = open('data/output/console', 'w')
        self.collect_patterns()  # read patterns from the file
        for dir, _, files in os.walk(self.path_to_data):
            current_out_dir = os.path.join(self.path_to_output, "retrieved", dir[-2:])
            Path(current_out_dir).mkdir(parents=True, exist_ok=True)
            for file in files:
                print("Pattern search in file {}...".format(dir + "/" + file))
                current_out_path = os.path.join(current_out_dir, file[:-11])
                self.matches_counter = 0
                data = self.read_data(os.path.join(dir, file))  # load data
                _ = self.search_patterns(data, current_out_path)  # launch pattern search
                print(self.stat_rel_matches)
        # save overall statistics
        self.save_glob_stat_to_csv(os.path.join(self.path_to_output, "retrieved", "_stat.csv"))
        sys.stdout.close()

    def prepare_output_dygie(self, args_output, doc):
        """

        """
        matches = self.get_sentence_matches(args_output)
        doc_ent, doc_rel, doc_idx, doc_rel_ann, doc_pattern = [], [], [], [], []
        for sent in doc["sents"]:
            sent_ent, sent_rel, sent_idx, sent_rel_ann, sent_pattern = [], [], [], [], []
            for token in doc["tokens"]:
                if int(token["start"]) >= int(sent["start"]) and int(token["end"]) <= int(sent["end"]):
                    sent_ent.append(doc["text"][token["start"]:token["end"]])
                    sent_idx.append([token["start"], token["end"]])
            for match in matches:
                ent1 = match[0]
                ent2 = match[1]
                if min(ent1["start"], ent2["start"]) >= int(sent["start"]) and max(ent1["end"], ent2["end"]) <= int(sent["end"]):
                    # if match[0] >= int(sent["start"]) and match[3] <= int(sent["end"]):
                    # sent_rel.append(match[:4] + [str(match[5])])
                    sent_rel.append(sorted([ent1["start_id"], ent2["start_id"], ent1["end_id"], ent2["end_id"]]) + [str(match[3])])
                    sent_rel_ann.append(match[3])
                    sent_pattern.append(sorted([ent1["start_id"], ent2["start_id"], ent1["end_id"], ent2["end_id"]]) + [match[2]] + [match[3]])
            doc_idx.append(sent_idx)
            doc_ent.append(sent_ent)
            doc_rel.append(sent_rel)
            doc_rel_ann.append(list(set(sent_rel_ann)))
            doc_pattern.append(sent_pattern)
        doc_entry = {"doc_key": doc["doc_id"], "sentences": doc_ent, "relations": doc_rel,
                     "tokensToOriginalIndices": doc_idx, "annotatedPredicates": doc_rel_ann, "patterns": doc_pattern}
        return doc_entry

    def save_loc_stat_to_csv(self, out_file, stat):
        with open(out_file, 'w') as csvfile:
            for key in stat.keys():
                csvfile.write("%s\t%s\n" % (DYGIE_RELATIONS[key], stat[key]))

    def save_glob_stat_to_csv(self, out_file):
        with open(out_file, 'w') as csvfile:
            for key in self.stat_rel_matches.keys():
                csvfile.write("%s\t%s\n" % (DYGIE_RELATIONS[key], self.stat_rel_matches[key]))


""" 
After the whole run:
    {'per:nationality': 280550, 'org:city_of_headquarters': 14098, 'per:date_of_birth': 488102, 
    'org:top_members_employees': 1983, 'per:city_of_birth': 25308, 'per:countries_of_residence': 9134, 
    'org:founded_by': 1492, 'org:subsidiaries': 3000, 'per:employee_of': 3649, 'per:children': 1069, 
    'per:date_of_death': 10739, 'org:founded': 191, 'per:schools_attended': 2459, 
    'per:political_religious_affiliation': 233}
"""
