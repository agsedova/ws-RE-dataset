"""
extract abstracts_AA from wiki pages; save it to json with "id", "url", "title", "text" fields
"""
import sys
import os
import json
import utils
from AbstractParser import AbstractParser


class WikiDumpProcesser:

    def __init__(self, root_dir):
        self.root_dir = root_dir

    def abstracts_to_json_format(self, annotation, wiki_input):
        """ Prepare annotated abstracts_test to save them in .json format"""
        return {wiki_input["id"]: {"url": wiki_input["url"], "title": wiki_input["title"], "text": wiki_input["text"],
                                   "sentences": [sent.as_dict() for sent in annotation]}}

    def sentences_to_json_format(self, annotation):
        """ Prepare annotated sentences to save them in .json format"""
        all_sentences = {}
        for sent in annotation:
            all_sentences = {**all_sentences, **{sent.sentenceId: sent.as_dict()}}
        return all_sentences

    def process_wikidump_file(self, path_to_input_file):
        all_abstracts, all_sentences = {}, {}
        with open(path_to_input_file, 'r') as input_file:
            file_length = sum(1 for _ in open(path_to_input_file))
            for num, line in enumerate(input_file, 1):
                wiki_input = json.loads(line)
                if "may refer to" not in wiki_input["text"]:
                    wiki_input["text"] = utils.extract_abstract(wiki_input["text"])   # extract abstracts_test only
                    ann = AbstractParser(wiki_input).parse()  # get parsed abstracts_test
                    if ann is not None:
                        print("Page {}/{} is annotated".format(num, file_length))
                        all_abstracts = {**all_abstracts, **self.abstracts_to_json_format(ann, wiki_input)}
                        all_sentences = {**all_sentences, **self.sentences_to_json_format(ann)}
                else:
                    print("Page {}/{} is skipped because it is a 'may refer to' page".format(num, file_length))
        return all_abstracts, all_sentences

    def main(self):
        for dir, _, files in os.walk(self.root_dir):
            for file in files:
                path_to_input_file = os.path.join(dir, file)
                print("Processing of file", path_to_input_file)
                if "wiki" in path_to_input_file:
                    all_abstracts, all_sentences = self.process_wikidump_file(path_to_input_file)
                    if all_abstracts is not None and all_sentences is not None:
                        utils.save_to_json(self.root_dir, "/abstracts.json", all_abstracts)
                        utils.save_to_json(self.root_dir, "/sentences.json", all_sentences)
                    print("================================================")


if __name__ == '__main__':
    WikiDumpProcesser(sys.argv[1]).main()

