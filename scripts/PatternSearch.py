import json
import sys
import re
import os
from elasticsearch import Elasticsearch

es = Elasticsearch(host="localhost", port=9200)
es = Elasticsearch()


class PatternSearch:

    def __init__(self, path_to_data, path_to_patterns):
        self.path_to_data = path_to_data
        self.path_to_patterns = path_to_patterns
        self.index = "wiki_sentences"

    def collect_patterns(self):
        """ Get patterns from file"""
        patterns = {}
        with open(self.path_to_patterns) as input:
            for line in input.readlines():
                if not line.startswith("#") and line != "\n":
                    relation, pattern = line.replace("\n", "").split(" ", 1)
                    patterns[pattern] = relation
        # todo: check arguments types
        return patterns

    def turn_pattern_to_regex(self, patterns):
        """ Turns patterns into regex expressions """
        # pattern = "( born )"  # search regex for pattern "$ARG1 ( born $ARG2 )"
        # pattern_rgx = ".*\\s*\\(\\s*.*born\\s.*\\s*\\)"
        pattern_rgx = []
        for pattern in patterns:
            pattern = re.sub("\\*", ".*", pattern)
            pattern = re.sub("\\$ARG1", ".*", pattern)
            pattern = re.sub("\\$ARG2", ".*", pattern)
            pattern = re.sub(" ", "\\\\s*", pattern)
            pattern = re.sub("\\(", "\\\\(", pattern)
            pattern = re.sub("\\)", "\\\\)", pattern)
            pattern_rgx.append(pattern)
        return pattern_rgx

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
            if re.match(pattern, sent):
                clean_hits.append(hit["_source"])
            else:
                print("The sentence is filtered since it does not perfectly match the pattern. Pattern: {}, "
                      "sentence: {}".format(pattern, sent))
        return clean_hits

    def main(self):
        with open(self.path_to_data, 'r') as input_file:
            sentences = json.loads(input_file.read())
        patterns = self.collect_patterns()
        patterns_rgx = self.turn_pattern_to_regex(list(patterns.keys()))

        # create elasticsearch index
        self.delete_index(self.index)
        self.create_index(self.index)
        self.insert_data(self.index, sentences)

        # search
        final_res = []
        for pattern, pattern_rgx in zip(patterns, patterns_rgx):
            res = self.match_query(pattern, "sentenceText")
            clean_res = self.clean_hits(res, pattern_rgx)
            if len(clean_res) > 0:
                final_res.append(clean_res)

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
    PatternSearch(sys.argv[1], sys.argv[2]).main()
