import json
import sys
import re

from EntityExtractor import Entity
from AbstractParser import Sentence
from elasticsearch import Elasticsearch
from elasticsearch import helpers

es = Elasticsearch(host="localhost", port=9200)
es = Elasticsearch()

# PUT localhost:9200/test-index
# Content-Type: application/json
#
# {
#   "mappings": {
#     "properties": {
#       "entities": {
#         "type": "nested"
#       }
#     }
#   }
# }


class PatternSearch:

    def __init__(self, path_to_data, path_to_patterns):
        self.path_to_data = path_to_data
        self.path_to_patterns = path_to_patterns
        self.index = "test-index"

    def create_index(self, index):
        body = '{"mappings":{"properties":{"entities":{"type":"nested"},"sentenceText":{"type":"text",' \
               '"analyzer":"whitespace","search_analyzer":"simple"}}}}'
        es.indices.create(index=index, body=body, ignore=400)

    def delete_index(self, index):
        es.indices.delete(index=index)

    def insert_one_data(self, _index, data):
        # index and doc_type you can customize by yourself
        res = es.index(index=_index, doc_type='sentences', id=5, body=data)
        # index will return insert info: like as created is True or False
        return res

    def insert_data(self, _index, data):
        # index and doc_type you can customize by yourself
        i = 0
        for _, sent in data.items():
            res = es.index(index=_index, body=sent)
            i += 1
            if i % 100 == 0:
                print(i)
            # print(res)

    # def insert_data_by_bulk(self, data):
    #     res = helpers.bulk(es, data)
    #     print(res)

    def regex_search(self, pat, index, field):
        return es.search(
            index=index,
            body={
                "query": {
                    "regexp": {
                        field: pat
                    }
                }
            }
        )

    def match_query(self, pat, field):
        return es.search(
            index=self.index,
            body={
                "query": {
                    "match_phrase": {
                        field: {
                            "query": pat,
                            # "analyzer": "whitespace",
                            # "operator": "and"
                        }
                    }
                }
            })["hits"]["hits"]

    def clean_hits(self, hits, pattern):
        clean_hits = []
        for hit in hits:
            sent = hit["_source"]["sentenceText"]
            if re.match(pattern, sent):
                clean_hits.append(hit["_source"])
            else:
                print("ooops!", sent)
        return clean_hits

    def retrieve_patterns(self):
        sentences = self.read_input_data()
        patterns = self.collect_patterns()

        self.delete_index(self.index)
        self.create_index(self.index)
        self.insert_data(self.index, sentences)

        # search
        pattern = "( born )"  # search regex for pattern "$ARG1 ( born $ARG2 )"
        pattern_rgx = ".*\\s*\\(\\s*.*born\\s.*\\s*\\)"
        res = self.match_query(pattern, "sentenceText")
        clean_hits = self.clean_hits(res, pattern_rgx)

        with open('retrieved.json', 'w') as outfile:
            json.dump(clean_hits, outfile)

        return

    def read_input_data(self):
        sentences = {}
        with open(self.path_to_data, 'r') as input_file:
            sent_json = json.loads(input_file.read())
            # for _, sent in sent_json.items():
                # sent_obj = Sentence(**sent)
                # sent_obj.entities = [Entity(**ent) for ent in sent_obj.entities]
                # sentences[sent_obj.sentenceId] = sent_obj
            return sent_json

    def collect_patterns(self):
        """ Get patterns from file"""
        patterns = {}
        with open(self.path_to_patterns) as input:
            for line in input.readlines():
                if not line.startswith("#") and line != "\n":
                    relation, pattern = line.replace("\n", "").split(" ", 1)
                    # pattern = pattern.replace("\n", "").split(" ", 1)
                    # pattern = (pattern[0], pattern[1].rsplit(" ", 1)[0], pattern[1].rsplit(" ", 1)[1])
                    patterns[pattern] = relation
        return patterns

    def check_pattern(self, sentences, patterns):
        # for pattern in patterns:
        #     print(patt)
        #     patt = re.sub(patt, "$ARG1", "")
        #     match = re.search(r"")


        return ""


if __name__ == "__main__":
    PatternSearch(sys.argv[1], sys.argv[2]).retrieve_patterns()

