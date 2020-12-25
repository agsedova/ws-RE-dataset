from pathlib import Path
import logging
import json
import spacy
import os

from scripts import utils

abstract_analyser = spacy.load("en_core_web_sm")


class WikiDumpProcessor:

    def __init__(self, root_dir: str, path_to_output: str):
        self.root_dir = root_dir
        self.path_to_output = path_to_output
        self.logger = logging.getLogger(__name__)

        Path(self.path_to_output).mkdir(parents=True, exist_ok=True)

    def process_wiki_pages(self) -> None:
        """
        The function reads the wiki pages saved from WikiDump file possibly in multiple files in the following format:
        each page is a dictionary on a new line with fields "id", "url", "title", "text". The pages are preprocessed
        with SpaCy package; the SpaCy output for each original file is saved to a json file with the same name.
        """
        for curr_dir, _, files in os.walk(self.root_dir):
            current_out_dir = os.path.join(self.path_to_output, curr_dir[-2:])
            Path(current_out_dir).mkdir(parents=True, exist_ok=True)
            for file in files:
                path_to_input_file = os.path.join(curr_dir, file)
                self.logger.info("Processing of file {}".format(path_to_input_file))
                current_out_file = os.path.join(current_out_dir, file + "_spacy.json")
                with open(current_out_file, "w", encoding="UTF-8") as o_json:
                    json.dump(self.get_analysed_pages(path_to_input_file), o_json)
                self.logger.info("File {} is processed and saved to {}".format(path_to_input_file, current_out_file))
        utils.log_section("WikiDump is processed", self.logger)

    def get_analysed_pages(self, path_to_input_file: str) -> list:
        """
        The function read the file with wiki pages and process meaningful ones with SpaCy package.
        :param path_to_input_file: path to the file with wiki pages that should be processed
        :return: list of SpaCy annotation for meaningful wiki pages.
        """
        all_pages = []
        skipped_pages = 0
        with open(path_to_input_file, 'r', encoding="UTF-8") as input_file:
            file_length = sum(1 for _ in open(path_to_input_file))
            for num, line in enumerate(input_file, 1):
                wiki_input = json.loads(line)
                if "may refer to" in wiki_input["text"]:
                    skipped_pages += 1
                    continue
                wiki_input["text"] = self.extract_abstract(wiki_input["text"])
                abstract_annotation = abstract_analyser(wiki_input["text"]).to_json()  # get parsed abstracts_test
                if abstract_annotation is not None:
                    page_annotation = {**{"doc_id": wiki_input["id"]}, **abstract_annotation}
                    all_pages.append(page_annotation)
            self.logger.info("{}/{} pages were annotated.".format(file_length-skipped_pages, file_length))
        return all_pages

    @staticmethod
    def extract_abstract(page: str) -> str:
        """
        The function gets an entire Wiki pages and extract its abstract.
        :param page: text of the wiki page
        :return: wiki page abstract
        """
        return page[:utils.find_nth(page, "\n\n", 1)] + ". " + page[utils.find_nth(page, "\n\n", 1) + 1:
                                                                    utils.find_nth(page, "\n\n", 2)] \
            .replace(u'\xa0', u' ').replace(u'\u00ad', u'-').replace(u'\u2013', u'-').replace(u'\n', u'')
