from scripts.commons import RELATION_TO_TYPES
import re
import json
import itertools


class PatternSearch:
    def __init__(self, path_to_data, path_to_patterns):
        self.path_to_data = path_to_data
        self.path_to_patterns = path_to_patterns

    def read_data(self):
        with open(self.path_to_data + "/annotated_pages.json") as input_file:
            data = json.load(input_file)
        return data

    # prepare patterns
    def get_patterns(self):
        """ Read patterns from file and save them to a dictionary {relation : [patterns]}"""
        relation_to_patterns = {}  # {relation : [patterns]}
        with open(self.path_to_patterns, encoding="UTF-8") as input:
            for line in input.readlines():
                if not line.startswith("#") and line != "\n":
                    relation, raw_pattern = line.replace("\n", "").split(" ", 1)
                    pattern = self.preprocess_patterns(raw_pattern)
                    if relation in relation_to_patterns.keys():
                        relation_to_patterns[relation].append(pattern)
                    else:
                        relation_to_patterns[relation] = [pattern]
        return relation_to_patterns

    def preprocess_patterns(self, pattern):
        """ Turn raw patterns into good-looking regexes"""
        pattern = re.escape(pattern)
        prepr_pattern = re.sub("\\\\\\*", "[^ ]+([^ ]+){0,3}", pattern)  # * --> match 1 to 4 tokens
        # prepr_pattern = re.sub("\\$ARG", "\\\\$ARG", prepr_pattern)  # escape $ in $ARG1 and $ARG2
        return prepr_pattern

    def get_types_to_entities(self, doc):
        types_to_entities = {}       # type: [ent_list]
        for ent in doc["ents"]:
            # curr_ent = doc["text"][ent["start"]:ent["end"]]
            curr_label = ent["label"]
            if ent["label"] in types_to_entities.keys():
                types_to_entities[curr_label].append(ent)
            else:
                types_to_entities[curr_label] = [ent]
        return types_to_entities

    def get_abstract_for_comparing(self, doc, ent1, ent2):
        """ Substitute entiies with "$ARG1" and "$ARG2" and do some refactoring needed for correct search """
        to_compare = doc["text"][:ent1["start"]] + "$ARG1" + doc["text"][ent1["end"]:ent2["start"]] + "$ARG2" + \
                     doc["text"][ent2["end"]:]
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
                    sent_rel.append(match)
                    sent_rel_ann.append(match[5])
                    sent_pattern.append(match[4])
            doc_idx.append(sent_idx)
            doc_ent.append(sent_ent)
            doc_rel.append(sent_rel)
            doc_rel_ann.append(sent_rel_ann)
            doc_pattern.append(sent_pattern)
        doc_entry = {"doc_key": doc["doc_id"], "tokenisedSentences": doc_ent, "relations": doc_rel,
                     "tokensToOriginalIndices": doc_idx, "annotatedPredicates": doc_rel_ann,
                     "patterns": doc_pattern}
        return doc_entry

    def search_patterns(self):
        data = self.read_data()
        relation_to_patterns = self.get_patterns()
        all_docs = []
        i = 0
        for doc in data:
            types_to_entities = self.get_types_to_entities(doc)
            curr_args_output = {}
            for rel, patterns in relation_to_patterns.items():
                if rel in RELATION_TO_TYPES.keys():
                    curr_args_output[rel] = []
                    types = RELATION_TO_TYPES[rel]
                    if types[0] in types_to_entities.keys() and types[1] in types_to_entities.keys():
                        for ent1, ent2 in itertools.product(types_to_entities[types[0]], types_to_entities[types[1]]):
                            if ent1["start"] < ent2["start"]:
                                # todo more checks about argument order!
                                to_compare = self.get_abstract_for_comparing(doc, ent1, ent2)
                                for pattern in patterns:
                                    match = re.search(pattern, to_compare)
                                    if match:
                                        curr_args_output[rel].append([ent1["start"], ent1["end"], ent2["start"],
                                                                      ent2["end"], pattern])
                                        # print("New match! Relation:{}; entity1: {}; entity2: {}; pattern {}; "
                                        #       "Sentence: {}".format(rel, doc["text"][ent1["start"]:ent1["end"]],
                                        #                 doc["text"][ent2["start"]:ent2["end"]], pattern, doc["text"]))
                                        i += 1
                            elif ent1["start"] > ent2["start"]:
                                # todo more checks about argument order!
                                pass
            all_docs.append(self.prepare_output_dygie(curr_args_output, doc))
        print("Total match:", i)
        with open(self.path_to_data + "/annotated_data_with_matched_info.json", "w+") as output_json:
            json.dump(all_docs, output_json)
