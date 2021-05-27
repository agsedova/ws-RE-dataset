import itertools
import json
from pathlib import Path
import sys
import os
import scripts.utils as utils
from scripts.commons import DYGIE_RELATIONS


class EntityPairsSearch:

    def __init__(self, path_to_spacy_data, path_to_entity_pair_ids, path_to_entity_pair_to_rel, path_to_output):
        self.path_to_spacy_data = path_to_spacy_data
        self.path_to_entity_pair_ids = path_to_entity_pair_ids
        self.path_to_entity_pair_to_rel = path_to_entity_pair_to_rel
        self.path_to_output = path_to_output

        self.entity_pair_ids = {}
        self.entity_pair_to_rel = {}
        self.spacy_data = {}
        self.stat_rel_matches = {}

        self.matches_counter = 0

    def add_stat_defaults(self):
        for relation in DYGIE_RELATIONS.values():
            self.stat_rel_matches[relation] = 0

    def load_dicts(self):
        with open(self.path_to_entity_pair_ids) as f:  # load data
            self.entity_pair_ids = json.load(f)
        with open(self.path_to_entity_pair_to_rel) as f:  # load data
            self.entity_pair_to_rel = json.load(f)
        # todo: fix this WA
        for entpair, relation in self.entity_pair_to_rel.items():
            self.entity_pair_to_rel[entpair] = list(set(relation))

        self.add_stat_defaults()

    def get_token_text(self, doc, token):
        return doc["text"][token["start"]:token["end"]]

    def add_ent_info(self, doc):
        for ent in doc["ents"]:
            ent["text"] = ""
            for token in doc["tokens"]:
                if token["start"] == ent["start"]:
                    ent["text"] += self.get_token_text(doc, token)
                    ent["start_id"] = int(token["id"])
                if token["end"] == ent["end"]:
                    token_text = self.get_token_text(doc, token)
                    if token_text not in ent["text"]:
                        ent["text"] += ("_" + token_text)
                    ent["end_id"] = int(token["id"])
                if token["start"] > ent["start"] and token["end"] < ent["end"]:
                    token_text = self.get_token_text(doc, token)
                    ent["text"] += ("_" + token_text)

    def is_ents_in_sent(self, doc, ent1, ent2):
        # check if both entities are in one sentence
        for sent in doc["sents"]:
            if ent1["start"] >= sent["start"] and ent2["start"] >= sent["start"] and ent1["end"] <= sent["end"] and \
                    ent2["end"] <= sent["end"]:
                return True
        return False

    def find_entity_pairs_match(self, data, output_path):
        all_docs = []
        stat_rel = {key: 0 for key in self.stat_rel_matches.keys()}
        for doc in data:
            matches = []
            self.add_ent_info(doc)
            for ent1, ent2 in itertools.permutations(doc["ents"], 2):
                if self.is_ents_in_sent(doc, ent1, ent2):
                    if ent1["start"] > ent2["start"]:
                        continue
                    entity_pair_text = ent1["text"] + ", " + ent2["text"]
                    if entity_pair_text not in self.entity_pair_ids:
                        continue
                    entity_pair_id = self.entity_pair_ids[entity_pair_text]
                    if str(entity_pair_id) not in self.entity_pair_to_rel:
                        continue
                    entity_pair_rel = self.entity_pair_to_rel[str(entity_pair_id)]
                    for rel in entity_pair_rel:
                        matches.append([ent1, ent2, entity_pair_id, rel])
                        self.matches_counter += 1
                        self.stat_rel_matches[rel] += 1
                        stat_rel[rel] += 1
            if len(matches) == 0:
                continue
            doc_dygie = utils.prepare_output_dygie(matches, doc)
            if any(doc_dygie["annotatedPredicates"]):
                all_docs.append(doc_dygie)

        print("Total match:", self.matches_counter)

        with open(output_path + "_dygie.json", "w+") as output_json:
            json.dump(all_docs, output_json)
        self.save_loc_stat_to_csv(output_path + "_stat.csv", stat_rel)

    def save_loc_stat_to_csv(self, out_file, stat):
        with open(out_file, 'w') as csvfile:
            for key in stat.keys():
                csvfile.write("%s\t%s\n" % (key, stat[key]))

    def save_glob_stat_to_csv(self, out_file):
        with open(out_file, 'w') as csvfile:
            for relation in self.stat_rel_matches.keys():
                csvfile.write("%s\t%s\n" % (relation, self.stat_rel_matches[relation]))

    def search_entpairs_multiple_files(self):
        for dir, _, files in os.walk(self.path_to_spacy_data):
            current_out_dir = os.path.join(self.path_to_output, "retrieved", dir[-2:])
            Path(current_out_dir).mkdir(parents=True, exist_ok=True)
            for file in files:
                print("Pattern search in file {}...".format(dir + "/" + file))
                current_out_path = os.path.join(current_out_dir, file[:-11])
                self.matches_counter = 0

                with open(os.path.join(dir, file)) as input_file:  # load data
                    data = json.load(input_file)

                self.find_entity_pairs_match(data, current_out_path)  # launch pattern search
                print(self.stat_rel_matches)

        # save overall statistics
        self.save_glob_stat_to_csv(os.path.join(self.path_to_output, "retrieved", "_stat.csv"))
        sys.stdout.close()

    def search_entpairs_one_file(self):
        Path(self.path_to_output).mkdir(parents=True, exist_ok=True)
        self.matches_counter = 0

        with open(self.path_to_spacy_data) as input_file:  # load data
            data = json.load(input_file)

        self.find_entity_pairs_match(data, self.path_to_output)  # launch pattern search

        print(self.stat_rel_matches)
        # save overall statistics
        self.save_glob_stat_to_csv(os.path.join(self.path_to_output, "_stat.csv"))
        sys.stdout.close()

    def retrieve_entity_pairs(self):
        self.load_dicts()

        Path(self.path_to_output).mkdir(parents=True, exist_ok=True)
        sys.stdout = open(os.path.join(self.path_to_output, "console"), 'w')

        if os.path.isdir(self.path_to_spacy_data):  # if we retrieve patterns in multiple files (input is a directory)
            self.search_entpairs_multiple_files()

        elif os.path.isfile(self.path_to_spacy_data):  # if we retrieve patterns in a single file
            self.search_entpairs_one_file()


if __name__ == "__main__":
    EntityPairsSearch("../data/output/knwldgn/retrieved_knwldgn_train/knwldgn_train_spacy.json",
                      "../data/output/wikidump/retrieved_4th_ver/_ent_pairs/entity_pair_ids.json",
                      "../data/output/wikidump/retrieved_4th_ver/_ent_pairs/entity_pair_to_rel.json",
                      "../data/output/knwldgn/retrieved_knwldgn_train_ent_pairs/")\
        .retrieve_entity_pairs()

