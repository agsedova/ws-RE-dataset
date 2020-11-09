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

    def get_relation_types_dict(self, relation_to_ids):
        relation_to_types = {}
        for relation in relation_to_ids.keys():
            relation_to_types[relation_to_ids[relation]] = RELATION_TO_TYPES[relation]
        return relation_to_types

    def get_patterns(self):
        """ Read patterns from file and save them to a dictionary {relation : [patterns]}"""
        # {relation : [patterns]}, {pattern : pattern_id}
        relation_to_patterns, patterns_to_ids, relation_to_ids = {}, {}, {}
        pattern_id, relation_id = 0, 0
        with open(self.path_to_patterns, encoding="UTF-8") as input:
            for line in input.readlines():
                if not line.startswith("#") and line != "\n":
                    relation, pattern = line.replace("\n", "").split(" ", 1)
                    # we take only relations that dygie uses
                    if relation in RELATION_TO_TYPES.keys():
                        # assign an id to pattern and add to patterns_to_ids dict
                        if pattern not in patterns_to_ids.keys():
                            patterns_to_ids[pattern] = pattern_id
                            pattern_id += 1
                        # assign an id to relation and add to relation_to_ids dict
                        if relation not in relation_to_ids.keys():
                            relation_to_ids[relation] = relation_id
                            relation_id += 1
                        # add relation - pattern pair to relation_to_patterns dict
                        if relation_to_ids[relation] in relation_to_patterns.keys():
                            relation_to_patterns[relation_to_ids[relation]].append(pattern)
                        else:
                            relation_to_patterns[relation_to_ids[relation]] = [pattern]
        relation_to_types = self.get_relation_types_dict(relation_to_ids)
        # save relation_to_ids to json file
        with open(self.path_to_data + "/relations.json", "w+") as rel_f:
            json.dump(relation_to_ids, rel_f)
        # save patterns_to_ids to json file
        with open(self.path_to_data + "/patterns.json", "w+") as rel_p:
            json.dump(patterns_to_ids, rel_p)
        return relation_to_patterns, patterns_to_ids, relation_to_types

    def preprocess_patterns(self, pattern):
        """ Turn raw patterns into good-looking regexes"""
        pattern = re.escape(pattern)
        prepr_pattern = re.sub("\\\\\\*", "[^ ]+([^ ]+){0,3}", pattern)  # * --> match 1 to 4 tokens
        # prepr_pattern = re.sub("\\$ARG", "\\\\$ARG", prepr_pattern)  # escape $ in $ARG1 and $ARG2
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
                    sent_rel.append(match[:4] + [match[5]])
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

    def search_patterns(self):
        data = self.read_data()
        relation_to_patterns, patterns_to_ids, relation_to_types = self.get_patterns()
        all_docs = []
        i = 0
        for doc in data:
            types_to_entities = self.get_types_to_entities(doc)
            curr_args_output = {}
            for rel, patterns in relation_to_patterns.items():
                curr_args_output[rel] = []
                types = relation_to_types[rel]
                if types[0] in types_to_entities.keys() and types[1] in types_to_entities.keys():
                    for ent1, ent2 in itertools.product(types_to_entities[types[0]], types_to_entities[types[1]]):
                        if ent1["start"] < ent2["start"]:
                            # todo more checks about argument order!
                            to_compare = self.get_abstract_for_comparing(doc, ent1, ent2)
                            for raw_pattern in patterns:
                                # convert pattern to regex
                                pattern = self.preprocess_patterns(raw_pattern)
                                match = re.search(pattern, to_compare)
                                if match:
                                    curr_args_output[rel].append([ent1["start"], ent1["end"], ent2["start"],
                                                                  ent2["end"], patterns_to_ids[raw_pattern]])
                                    print("New match! Relation:{}; entity1: {}; entity2: {}; pattern {}; "
                                          "Sentence: {}".format(rel, doc["text"][ent1["start"]:ent1["end"]],
                                                    doc["text"][ent2["start"]:ent2["end"]], pattern, doc["text"]))
                                    i += 1
                        elif ent1["start"] > ent2["start"]:
                            # todo more checks about argument order!
                            pass
            all_docs.append(self.prepare_output_dygie(curr_args_output, doc))
        print("Total match:", i)
        with open(self.path_to_data + "/annotated_data_with_matched_info.json", "w+") as output_json:
            json.dump(all_docs, output_json)


"""


Еще заметила, что в списке AnnotatedPredicates первого документа (id 161013) для 9 предложения предикат повторяется, а должен появиться только один раз, так как здесь не учитывается конкретное количество примеров этого предиката в предложении, а только факт его наличия.

"""