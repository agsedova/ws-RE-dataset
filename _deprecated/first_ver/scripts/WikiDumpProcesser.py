"""
extract abstracts_AA from wiki pages; save it to json with "id", "url", "title", "text" fields
"""
import sys
import os
import json
from scripts.WikiDumpParser import AbstractParser
import re


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
                    # extract abstracts only
                    wiki_input["text"] = self.clear_punctuation(self.extract_abstract(wiki_input["text"]))
                    ann = AbstractParser(wiki_input).parse()  # get parsed abstracts_test
                    if ann is not None:
                        print("Page {}/{} is annotated".format(num, file_length))
                        all_abstracts = {**all_abstracts, **self.abstracts_to_json_format(ann, wiki_input)}
                        all_sentences = {**all_sentences, **self.sentences_to_json_format(ann)}
                else:
                    print("Page {}/{} is skipped because it is a 'may refer to' page".format(num, file_length))
        return all_abstracts, all_sentences

    def clear_punctuation(self, text):
        """ Add additional whitespaces after the punctuation symbols; needed for correct pattern search """
        text = re.sub("\\(", "\\( ", text)
        text = re.sub("\\)", "\\) ", text)
        text = re.sub(",", ", ", text)
        text = re.sub("\\.", "\\. ", text)
        return text

    def extract_abstract(self, page):
        """ takes an entire Wiki pages as input and returns its abstract"""
        return page[self.find_nth(page, "\n\n", 1) + 2:self.find_nth(page, "\n\n", 2) + 2]

    def find_nth(self, string, substring, n):
        """ Find index of the nth element in the string"""
        return string.find(substring) if n == 1 else string.find(substring, self.find_nth(string, substring, n - 1) + 1)

    def save_to_json(self, filename, new_entry):
        """ Create a json file and save data in it or add new entries to already existing json file"""
        path_to_output_file = self.root_dir + filename
        if os.path.isfile(path_to_output_file):
            with open(path_to_output_file, 'r+', encoding="UTF-8") as output_file:
                data = json.load(output_file)
                updated_data = {**data, **new_entry}
                output_file.seek(0)
                json.dump(updated_data, output_file)
                # json.dumps(updated_data, output_file)
                output_file.truncate()
                print("New entries are added to the existing {} file".format(filename))
        else:
            with open(path_to_output_file, 'w+', encoding="UTF-8") as output_file:
                json.dump(new_entry, output_file)
                print("New entries are saved to the newly created {} file".format(filename))
        # with open(path_to_output_file, 'w+', encoding="UTF-8") as output_file:
        #     json.dump(new_abstract, output_file)
        #     print("New .json file is created, abstracts_test are saved")

    def main(self):
        for dir, _, files in os.walk(self.root_dir):
            for file in files:
                path_to_input_file = os.path.join(dir, file)
                print("Processing of file", path_to_input_file)
                if "wiki" in path_to_input_file:
                    all_abstracts, all_sentences = self.process_wikidump_file(path_to_input_file)
                    if all_abstracts is not None and all_sentences is not None:
                        self.save_to_json("/abstracts.json", all_abstracts)
                        self.save_to_json("/sentences.json", all_sentences)
                    print("================================================")


if __name__ == '__main__':
    WikiDumpProcesser(sys.argv[1]).main()

