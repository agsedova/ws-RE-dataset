"""
extract abstracts_AA from wiki pages; save it to json with "id", "url", "title", "text" fields
"""

import sys
import os
import json
import utils
from parse_abstract import AbstractParser


def process_wikidump_pages(path_to_input_file):
    all_abstracts, all_sentences = {}, {}
    with open(path_to_input_file, 'r') as input_file:
        file_length = sum(1 for _ in open(path_to_input_file))
        for num, line in enumerate(input_file, 1):
            wiki_input = json.loads(line)
            if "may refer to" not in wiki_input["text"]:
                wiki_input["text"] = extract_abstract(wiki_input["text"])   # extract abstracts_test only
                ann = AbstractParser(wiki_input).parse()  # get parced abstracts_test
                if ann is not None:
                    print("Page {}/{} is annotated".format(num, file_length))
                    all_abstracts = {**all_abstracts, **abstracts_to_json_format(ann, wiki_input)}
                    all_sentences = {**all_sentences, **sentences_to_json_format(ann)}
            else:
                print("Page {}/{} is skipped because it is a 'may refer to' page".format(num, file_length))
    return all_abstracts, all_sentences


def extract_abstract(page):
    """ takes an entire Wiki pages as input and returns its abstract"""
    return page[utils.find_nth(page, "\n\n", 1)+2:utils.find_nth(page, "\n\n", 2)+2]


def sentences_to_json_format(annotation):
    """ Prepare annotated sentences to save them in .json format"""
    all_sentences = {}
    for sent in annotation:
        all_sentences = {**all_sentences, **{sent.sentenceId: sent.as_dict()}}
    return all_sentences


def abstracts_to_json_format(annotation, wiki_input):
    """ Prepare annotated abstracts_test to save them in .json format"""
    return {wiki_input["id"]: {"url": wiki_input["url"], "title": wiki_input["title"], "text": wiki_input["text"],
                               "sentences": [sent.as_dict() for sent in annotation]}}


def main(root_dir):
    for dir, _, files in os.walk(root_dir):
        for file in files:
            path_to_input_file = os.path.join(dir, file)
            print("Processing of file", path_to_input_file)
            if "wiki" in path_to_input_file:
                abstracts, sentences = process_wikidump_pages(path_to_input_file)
                if abstracts is not None and sentences is not None:
                    utils.save_to_json(root_dir, "/abstracts.json", abstracts)
                    utils.save_to_json(root_dir, "/sentences.json", sentences)
                    print("================================================")


if __name__ == '__main__':
    main(sys.argv[1])