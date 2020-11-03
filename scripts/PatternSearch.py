import json
import sys
import re
import os
from elasticsearch import Elasticsearch

es = Elasticsearch(host="localhost", port=9200)
es = Elasticsearch()

'''
EXPECTED_TYPES_PER_PROPERTY = {
  '1':  ('ORG','ORG'),      #SUBSIDIARY_OF
  '2':  ('ORG','PERSON'),   #FOUNDED_BY
  '3':  ('PERSON','ORG'),   #EMPLOYEE_OR_MEMBER_OF
  '4':  ('ORG','PERSON'),   #CEO
  '5':  ('ORG','DATE'),     #DATE_FOUNDED
  '6':  ('ORG','GPE'),      #HEADQUARTERS
  '9':  ('PERSON','ORG'),   #EDUCATED_AT
  '10': ('PERSON','NORP'),  #NATIONALITY - NB! there is no close relation in our list
  '11': ('PERSON','GPE'),   #PLACE_OF_RESIDENCE
  '12': ('PERSON','GPE'),   #PLACE_OF_BIRTH
  '14': ('PERSON','DATE'),  #DATE_OF_DEATH
  '15': ('PERSON','DATE'),  #DATE_OF_BIRTH
  '25': ('PERSON','PERSON'),#SPOUSE
  '34': ('PERSON','PERSON'),#CHILD_OF
  '45': ('PERSON','ORG'),   #POLITICAL_AFFILIATION
}


Spacy entities:
PERSON	People, including fictional.
NORP	Nationalities or religious or political groups.
FAC	Buildings, airports, highways, bridges, etc.
ORG	Companies, agencies, institutions, etc.
GPE	Countries, cities, states.
LOC	Non-GPE locations, mountain ranges, bodies of water.
PRODUCT	Objects, vehicles, foods, etc. (Not services.)
EVENT	Named hurricanes, battles, wars, sports events, etc.
WORK_OF_ART	Titles of books, songs, etc.
LAW	Named documents made into laws.
LANGUAGE	Any named language.
DATE	Absolute or relative dates or periods.
TIME	Times smaller than a day.
PERCENT	Percentage, including ”%“.
MONEY	Monetary values, including unit.
QUANTITY	Measurements, as of weight or distance.
ORDINAL	“first”, “second”, etc.
CARDINAL	Numerals that do not fall under another type.
'''

RELATIONS = {'org:date_founded', 'per:cities_of_residence', 'org:political_religious_affiliation', 'org:website',
             'per:religion', 'per:country_of_death', 'per:title', 'per:member_of', 'per:spouse', 'per:siblings',
             'org:alternate_names', 'per:stateorprovince_of_death', 'per:charges', 'per:city_of_birth',
             'org:stateorprovince_of_headquarters', 'org:number_of_employees_members', 'per:stateorprovince_of_birth',
             'per:employee_or_member_of', 'per:employee_of', 'per:other_family', 'org:parents', 'per:origin',
             'org:subsidiaries', 'org:country_of_headquarters', 'org:member_of', 'per:stateorprovinces_of_residence',
             'per:cause_of_death', 'per:countries_of_residence', 'per:date_of_death', 'org:members',
             'per:city_of_death', 'per:alternate_names', 'org:founded_by', 'per:parents', 'org:top_members_employees',
             'per:date_of_birth', 'org:date_dissolved', 'per:country_of_birth', 'per:schools_attended',
             'org:city_of_headquarters', 'org:dissolved', 'per:age', 'per:statesorprovinces_of_residence',
             'per:children', 'org:shareholders', 'org:founded'}

TYPES_PER_RELATION = {'org:subsidiaries': ('ORG', 'ORG'),
                      'org:founded_by': ('ORG', 'PERSON'),
                      'org:founded': ('ORG', 'DATE'),
                      'org:date_founded': ('ORG', 'DATE'),
                      'org:stateorprovince_of_headquarters': ('ORG', 'GPE'),
                      'org:country_of_headquarters': ('ORG', 'GPE'),
                      'org:city_of_headquarters': ('ORG', 'GPE'),
                      'org:top_members_employees': ('ORG', 'PERSON'),
                      'org:number_of_employees_members': ('ORG', 'CARDINAL'),
                      'org:parents': ('ORG', 'ORG'),
                      'org:political_religious_affiliation': ('PERSON', 'ORG'),
                      'org:date_dissolved': ('ORG', 'DATA'),
                      'org:dissolved': ('ORG', 'DATA'),
                      'org:shareholders': ('ORG', 'PERSON'),
                      'org:alternate_names': ('ORG', 'ORG'),

                      'per:employee_or_member_of': ('PERSON', 'ORG'),
                      'per:employee_of': ('PERSON', 'ORG'),
                      'per:schools_attended': ('PERSON', 'ORG'),
                      'per:stateorprovinces_of_residence': ('PERSON', 'GPE'),
                      'per:statesorprovinces_of_residence': ('PERSON', 'GPE'),
                      'per:countries_of_residence': ('PERSON', 'GPE'),
                      'per:cities_of_residence': ('PERSON', 'GPE'),
                      'per:origin': ('PERSON', 'GPE'),
                      'per:stateorprovince_of_birth': ('PERSON', 'GPE'),
                      'per:country_of_birth': ('PERSON', 'GPE'),
                      'per:city_of_birth': ('PERSON', 'GPE'),
                      'per:stateorprovince_of_death': ('PERSON', 'GPE'),
                      'per:country_of_death': ('PERSON', 'GPE'),
                      'per:city_of_death': ('PERSON', 'GPE'),
                      'per:date_of_death': ('PERSON', 'DATE'),
                      'per:date_of_birth': ('PERSON', 'DATE'),
                      'per:spouse': ('PERSON', 'PERSON'),
                      'per:children': ('PERSON', 'PERSON'),
                      'per:parents': ('PERSON', 'PERSON'),
                      'per:siblings': ('PERSON', 'PERSON'),
                      'per:other_family': ('PERSON', 'PERSON'),
                      'per:age': ('PERSON', 'CARDINAL'),
                      'per:religion': ('PERSON', 'NORP'),
                      'per:alternate_names': ('PERSON', 'PERSON'),

                      'per:member_of': ('_', '_'),
                      'org:member_of': ('_', '_'),
                      'org:members': ('_', '_'),
                      'org:website': ('_', '_'),
                      'per:title': ('_', '_'),
                      'per:charges': ('_', '_'),
                      'per:cause_of_death': ('_', '_')}


class PatternSearch:

    def __init__(self, path_to_data, path_to_patterns, path_to_entity_types):
        self.path_to_data = path_to_data
        self.path_to_patterns = path_to_patterns
        self.path_to_entity_types = path_to_entity_types
        self.index = "wiki_sentences"

    def collect_patterns(self):
        """ Get patterns from file"""
        patterns = []  # {(pattern, pattern_as_regex, argument_order) : relation}
        with open(self.path_to_patterns) as input:
            for line in input.readlines():
                if not line.startswith("#") and line != "\n":
                    relation, pattern = line.replace("\n", "").split(" ", 1)
                    pattern_rgx, arg_ord = self.turn_pattern_to_regex(pattern)
                    pattern = re.sub("\\$ARG1", "(.*)", pattern)
                    pattern = re.sub("\\$ARG2", "(.*)", pattern)
                    patterns.append({"text": pattern, "pattern_rgx": pattern_rgx, "argument_order": arg_ord,
                                     "relation": relation})
        return patterns

    def turn_pattern_to_regex(self, pattern):
        """ Turns patterns into regex expressions """
        # pattern = "( born )"  # search regex for pattern "$ARG1 ( born $ARG2 )"
        # pattern_rgx = ".*\\s*\\(\\s*.*born\\s.*\\s*\\)"
        if "$ARG0" in pattern:
            arg_order = "12"
        elif int(pattern.find("$ARG1")) < int(pattern.find("$ARG2")):
            arg_order = "12"
        elif int(pattern.find("$ARG1")) > int(pattern.find("$ARG2")):
            arg_order = "21"
        else:
            print("Error! Pattern doesn't contain arguments")
        pattern = re.sub("\\*", ".*", pattern)
        pattern = re.sub(" ", "\\\\s*", pattern)
        pattern = re.sub("\\(", "\\\\(", pattern)
        pattern = re.sub("\\)", "\\\\)", pattern)
        pattern = re.sub("\\$ARG1", "([\\\\S]+)", pattern)
        pattern = re.sub("\\$ARG2", "([\\\\S]+)", pattern)
        return pattern, arg_order

    def create_index(self, index):
        """ Creates elasticsearch index"""
        body = '{"mappings":{"properties":{"entities":{"type":"nested"},"sentenceText":{"type":"text",' \
               '"analyzer":"whitespace","search_analyzer":"simple"}}}}'
        es.indices.create(index=index, body=body, ignore=400)

    def delete_index(self, index):
        """ Delete elasticsearch index"""
        es.indices.delete(index=index)

    def insert_one_data(self, _index, data):
        """ Add one data sample to index. Index will return insert info: like as created is True or False """
        return es.index(index=_index, doc_type='sentences', id=5, body=data)

    def insert_data(self, _index, data):
        """ Add data to index. """
        print("Start indexing data...")
        for _, sent in data.items():
            es.index(index=_index, body=sent)
        print("Indexing is finished")

    # def insert_data_by_bulk(self, data):
    #     res = helpers.bulk(es, data)
    #     print(res)

    # def regex_search(self, pat, index, field):
    #     """ Search regex pattern in a field of all instances in index """
    #     return es.search(index=index, body={"query": {"regexp": {field: pat}}})

    def match_query(self, pat, field):
        """ Search a pattern in a field of all instances in index """
        return es.search(index=self.index, body={"query": {"match_phrase": {field: {"query": pat}}}})["hits"]["hits"]

    def clean_hits(self, hits, pattern):
        """ Filter out the instances that exactly match the pattern """
        clean_hits = []
        for hit in hits:
            sent = hit["_source"]["sentenceText"]
            m = re.match(pattern["pattern_rgx"], sent)
            if m:
                if pattern["argument_order"] == "12":
                    clean_hits.append({"sentence": hit["_source"], "$ARG1": m[1], "$ARG2": m[2],
                                       "relation": pattern["relation"], "pattern": pattern["text"]})
                else:
                    clean_hits.append({"sentence": hit["_source"], "$ARG1": m[2], "$ARG2": m[1],
                                       "relation": pattern["relation"], "pattern": pattern["text"]})
            else:
                print("The sentence was excluded since it does not perfectly match the pattern. Pattern: {}, "
                      "sentence: {}".format(pattern["pattern_rgx"], sent))
        return clean_hits

    def check_types(self, sentences):
        proper_sentences = []
        for sentence in sentences:
            sentence["$ARG1_type"], sentence["$ARG2_type"] = '', ''
            expected_types = TYPES_PER_RELATION[sentence["relation"]]
            # matched_arg1_entity = filter(lambda ent: ent['entityInSentence'] == sentence["$ARG1"],
            #               sentence["sentence"]["entities"])
            # matched_arg2_entity = filter(lambda ent: ent['entityInSentence'] == sentence["$ARG2"],
            #                              sentence["sentence"]["entities"])
            for entity in sentence["sentence"]["entities"]:
                if entity["entityInSentence"] == sentence["$ARG1"]:
                    sentence["$ARG1_type"] = entity["entityType"]
                    if sentence["$ARG1_type"] != expected_types[0]:
                        break
                elif entity["entityInSentence"] == sentence["$ARG2"]:
                    sentence["$ARG2_type"] = entity["entityType"]
                    if sentence["$ARG2_type"] != expected_types[1]:
                        break
            if sentence["$ARG1_type"] == expected_types[0] and sentence["$ARG2_type"] == expected_types[1]:
                proper_sentences.append(sentence)
        return proper_sentences

    def main(self):
        with open(self.path_to_data, 'r') as input_file:
            sentences = json.loads(input_file.read())
        patterns = self.collect_patterns()

        # create elasticsearch index
        self.delete_index(self.index)
        self.create_index(self.index)
        self.insert_data(self.index, sentences)

        # search
        final_res = []
        for pattern in patterns:
            hits = self.match_query(pattern["text"], "sentenceText")
            clean_hits = self.clean_hits(hits, pattern)
            proper_sentences = self.check_types(clean_hits)
            if len(proper_sentences) > 0:
                final_res += proper_sentences

        with open('retrieved.json', 'w') as outfile:
            json.dump(final_res, outfile)

    # def read_input_data(self):
    #     sentences = {}
    #     with open(self.path_to_data, 'r') as input_file:
    #         sent_json = json.loads(input_file.read())
    #         # for _, sent in sent_json.items():
    #             # sent_obj = Sentence(**sent)
    #             # sent_obj.entities = [Entity(**ent) for ent in sent_obj.entities]
    #             # sentences[sent_obj.sentenceId] = sent_obj
    #         return sent_json


if __name__ == "__main__":
    PatternSearch(sys.argv[1], sys.argv[2], sys.argx[3]).main()
