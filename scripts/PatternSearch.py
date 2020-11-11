from scripts.commons import RELATION_TO_TYPES, PROPERTY_NAMES
import re
import json
import itertools


# todo: ? maybe add additional regex for datum


class PatternSearch:

    def __init__(self, path_to_data, path_to_patterns):
        self.path_to_data = path_to_data
        self.path_to_patterns = path_to_patterns

        self.relation_to_patterns = {}
        self.patterns_to_ids = {}
        self.ids_to_patterns = {}
        self.relation_to_types = {}

        self.pattern_counter = 0
        self.matches_counter = 0

    def read_data(self):
        with open(self.path_to_data + "/spacy_annotated_pages.json") as input_file:
            data = json.load(input_file)
        return data

    def get_relation_types_dict(self):
        for relation in PROPERTY_NAMES.keys():
            self.relation_to_types[PROPERTY_NAMES[relation]] = RELATION_TO_TYPES[relation]

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
                if line.startswith("#") or line == "\n":            # take only meaningful strings
                    continue
                relation, pattern = line.replace("\n", "").split(" ", 1)
                if relation not in RELATION_TO_TYPES.keys():              # we select only relations that dygie uses
                    continue
                relation_id = PROPERTY_NAMES[relation]
                curr_pattern_id = self.get_pattern_id(pattern)
                # add pattern to corresponding relation in relation_to_patterns dict if it is not there yet
                self.add_pattern(relation_id, curr_pattern_id)

        # patterns_to_ids = dict((patt_id, patt) for patt_id, patt in enumerate(set(patterns))) # {pattern : pattern_id}
        self.get_relation_types_dict()        # {relation : arg_types}
        self.ids_to_patterns = {patt_id: pattern for pattern, patt_id in self.patterns_to_ids.items()}

        # save patterns_to_ids to json file
        with open(self.path_to_data + "/patterns.json", "w+") as rel_p:
            json.dump(self.ids_to_patterns, rel_p)

    def preprocess_patterns(self, pattern):
        """ Turn raw patterns into good-looking regexes"""
        pattern = re.escape(pattern)
        prepr_pattern = re.sub("\\\\\\*", "[^ ]+([^ ]+){0,3}", pattern)  # * --> match 1 to 4 tokens
        # prepr_pattern = re.sub("\\$ARG", "\\\\$ARG", prepr_pattern)  # escape $ in $ARG1 and $ARG2
        # add optional articles
        # prepr_pattern = re.sub("\\\\\\$ARG", "(A)?(a)?(The)?(the)? \\$ARG", prepr_pattern)
        return prepr_pattern

    def get_types_to_entities(self, doc):
        types_to_entities = {}       # type: [ent_list]
        for ent in doc["ents"]:
            curr_label = ent["label"]
            if ent["label"] in types_to_entities.keys():
                types_to_entities[curr_label].append(ent)
            else:
                types_to_entities[curr_label] = [ent]
        return types_to_entities

    def get_abstract_for_comparing(self, doc, ent1, ent2, curr_sent, arg1, arg2):
        """ Substitute entiies with "$ARG1" and "$ARG2" and do some refactoring needed for correct search """
        to_compare = doc["text"][curr_sent["start"]:ent1["start"]] + arg1 \
                     + doc["text"][ent1["end"]:ent2["start"]] + arg2 + \
                     doc["text"][ent2["end"]:curr_sent["end"]]
        to_compare = re.sub(u'\\(', u"( ", to_compare)
        to_compare = re.sub(u'\\)', u" )", to_compare)
        to_compare = re.sub(u'\\,', ' ,', to_compare)
        to_compare = re.sub(u"\\'s", " 's", to_compare)
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

    def prepare_output_dygie(self, args_output, doc):
        matches = self.get_sentence_matches(args_output)
        doc_ent, doc_rel, doc_idx, doc_rel_ann, doc_pattern = [], [], [], [], []
        for sent in doc["sents"]:
            sent_ent, sent_rel, sent_idx, sent_rel_ann, sent_pattern = [], [], [], [], []
            for token in doc["tokens"]:
                if int(token["start"]) >= int(sent["start"]) and int(token["end"]) <= int(sent["end"]):
                    sent_ent.append(doc["text"][token["start"]:token["end"]])
                    sent_idx.append([token["start"], token["end"]])
            for match in matches:
                if match[0] >= int(sent["start"]) and match[3] <= int(sent["end"]):
                    sent_rel.append(match[:4] + [str(match[5])])
                    sent_rel_ann.append(match[5])
                    sent_pattern.append(match)
            doc_idx.append(sent_idx)
            doc_ent.append(sent_ent)
            doc_rel.append(sent_rel)
            doc_rel_ann.append(list(set(sent_rel_ann)))
            doc_pattern.append(sent_pattern)
        doc_entry = {"doc_key": doc["doc_id"], "sentences": doc_ent, "relations": doc_rel,
                     "tokensToOriginalIndices": doc_idx, "annotatedPredicates": doc_rel_ann, "patterns": doc_pattern}
        return doc_entry

    def search_by_pattern(self, curr_args_output, rel, patterns, to_compare, doc, ent1, ent2):
        """
        Look up each pattern frpm the list in string and, if there is a match, add corresponding into to
        curr_args_output dict
        """
        for pattern_id in patterns:
            pattern = self.preprocess_patterns(self.ids_to_patterns[pattern_id])        # convert pattern to regex
            match = re.search(pattern, to_compare)
            if match:
                curr_args_output[rel].append([ent1["start"], ent1["end"], ent2["start"], ent2["end"], pattern_id])
                print("New match! Relation:{}; entity1: {}; entity2: {}; pattern {}; "
                      "Sentence: {}".format(rel, doc["text"][ent1["start"]:ent1["end"]],
                                            doc["text"][ent2["start"]:ent2["end"]], pattern, doc["text"]))
                self.matches_counter += 1
        return

    def search_patterns(self):
        print("Pattern searching is starting.....")
        data = self.read_data()     # read file with sentences annotated by spacy
        self.collect_patterns()     # read patterns from the file
        all_docs = []
        for doc in data:
            types_to_entities = self.get_types_to_entities(doc)
            curr_args_output = {}
            for rel, patterns in self.relation_to_patterns.items():
                curr_args_output[rel] = []
                types = self.relation_to_types[rel]
                if not(types[0] in types_to_entities.keys() and types[1] in types_to_entities.keys()):
                    continue
                for ent1, ent2 in itertools.product(types_to_entities[types[0]], types_to_entities[types[1]]):
                    # make sure that entities are in one sentence
                    for sent in doc["sents"]:
                        if not (sent["start"] <= min(ent1["start"], ent2["start"]) <= sent["end"] and \
                                sent["start"] <= max(ent1["end"], ent2["end"]) <= sent["end"]):
                            continue
                        if ent1["start"] < ent2["start"] and ent1["label"] == types[0]:
                            # if the ent1 comes before ent2 and that is what pattern types demand
                            to_compare = self.get_abstract_for_comparing(doc, ent1, ent2, sent, "$ARG1", "$ARG2")
                            self.search_by_pattern(curr_args_output, rel, patterns, to_compare, doc, ent1, ent2)
                        elif ent1["start"] > ent2["start"] and ent2["label"] == types[0]:
                            # if the ent2 comes before ent1 and that is what pattern types demand
                            to_compare = self.get_abstract_for_comparing(doc, ent2, ent1, sent, "$ARG2", "$ARG1")
                            self.search_by_pattern(curr_args_output, rel, patterns, to_compare, doc, ent1, ent2)

            all_docs.append(self.prepare_output_dygie(curr_args_output, doc))

        print("Total match:", self.matches_counter)
        with open(self.path_to_data + "/annotated_data_with_matched_info.json", "w+") as output_json:
            json.dump(all_docs, output_json)

