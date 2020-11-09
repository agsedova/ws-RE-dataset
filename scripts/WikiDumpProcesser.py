import json
import spacy
import os


nlp = spacy.load("en_core_web_sm")


class WikiDumpProcesser:

    def __init__(self, root_dir):
        self.root_dir = root_dir

    def abstracts_to_json_format(self, annotation, wiki_input):
        """ Prepare annotated abstracts_test to save them in .json format"""
        return {wiki_input["id"]: {"url": wiki_input["url"], "title": wiki_input["title"], "text": wiki_input["text"],
                                   "sentences": [sent.as_dict() for sent in annotation]}}

    def get_spacy_annotation(self, abstract):
        """ Takes an abstract text and output spacy annotation in json format """
        return nlp(abstract).to_json()

    def extract_abstract(self, page):
        """ takes an entire Wiki pages as input and returns its abstract"""
        # return page[self.find_nth(page, "\n\n", 1) + 2:self.find_nth(page, "\n\n", 2) + 2]      # without page title
        # return page[:self.find_nth(page, "\n\n", 2) + 2].encode('utf-8').decode('utf-8')
        return page[:self.find_nth(page, "\n\n", 1)] + ". " + page[self.find_nth(page, "\n\n", 1) + 1
                                                                   :self.find_nth(page, "\n\n", 2)]\
            .replace(u'\xa0', u' ').replace(u'\u00ad', u'-').replace(u'\u2013', u'-').replace(u'\n\n', u'')

    def find_nth(self, string, substring, n):
        """ Find index of the nth element in the string"""
        return string.find(substring) if n == 1 else string.find(substring, self.find_nth(string, substring, n - 1) + 1)

    def process_wikidump_file(self, path_to_input_file):
        all_pages = []
        skipped_pages = 0
        with open(path_to_input_file, 'r', encoding="UTF-8") as input_file:
            file_length = sum(1 for _ in open(path_to_input_file))
            for num, line in enumerate(input_file, 1):
                wiki_input = json.loads(line)
                if "may refer to" not in wiki_input["text"]:
                    # extract abstracts only
                    wiki_input["text"] = self.extract_abstract(wiki_input["text"])
                    abstract_annotation = self.get_spacy_annotation(wiki_input["text"])  # get parsed abstracts_test
                    if abstract_annotation is not None:
                        page_annotation = {**{"doc_id": wiki_input["id"]}, **abstract_annotation}
                        all_pages.append(page_annotation)
                        # print("Page {}/{} is annotated".format(num, file_length))
                else:
                    skipped_pages += 1

            print("Totally {} pages were processed, {} out of them were skipped.".format(file_length, skipped_pages))
        return all_pages

    def process_wiki_pages(self):
        preprocessed_wiki_dump = []
        for dir, _, files in os.walk(self.root_dir):
            for file in files:
                path_to_input_file = os.path.join(dir, file)
                print("Processing of file", path_to_input_file)
                if "wiki" in path_to_input_file:
                    preprocessed_wiki_dump += self.process_wikidump_file(path_to_input_file)
                    print("File {} is preprocessed".format(path_to_input_file))
        with open(self.root_dir + "/spacy_annotated_pages.json", "w+", encoding="UTF-8") as o_json:
            json.dump(preprocessed_wiki_dump, o_json)
        print("================================================")