import json
import sys

from extract_entities import Entity
from parse_abstract import Sentence
from elasticsearch import Elasticsearch


class PatternSearch:

    def __init__(self, path_to_data, path_to_patterns):
        self.path_to_data = path_to_data
        self.path_to_patterns = path_to_patterns

    def retrieve_patterns(self):
        sentences = self.read_input_data()
        patterns = self.collect_patterns()
        self.check_pattern(sentences, patterns)


        print("ok")
        return

    def read_input_data(self):
        sentences = {}
        with open(self.path_to_data, 'r') as input_file:
            sent_json = json.loads(input_file.read())
            for _, sent in sent_json.items():
                sent_obj = Sentence(**sent)
                sent_obj.entities = [Entity(**ent) for ent in sent_obj.entities]
                sentences[sent_obj.sentenceText] = sent_obj
            return sentences

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
        es = Elasticsearch()
        for pattern in patterns:
            print(patt)
            patt = re.sub(patt, "$ARG1", "")
            match = re.search(r"")

        return ""


if __name__ == "__main__":
    PatternSearch(sys.argv[1], sys.argv[2]).retrieve_patterns()

