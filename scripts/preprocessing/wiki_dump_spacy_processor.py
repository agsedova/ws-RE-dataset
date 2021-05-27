from pathlib import Path
from typing import List

import logging
import json
import os

from scripts.utils import log_section
from scripts.preprocessing.utils import extract_abstract

import en_core_web_sm
abstract_analyser = en_core_web_sm.load()

logger = logging.getLogger(__name__)


def wiki_dump_spacy_processor(root_dir: str, path_to_output: str = None):
    """
    The function reads the wiki pages saved from WikiDump file possibly in multiple files in the following format:
    each page is a dictionary on a new line with fields "id", "url", "title", "text". The pages are preprocessed
    with SpaCy package; the SpaCy output for each original file is saved to a json file with the same name.
    :param root_dir: path to the directory where all wiki pages saved from WikiDump file are stored.
    :param path_to_output: path to the directory where the files processed with SpaCy should be saved to.
    """

    if path_to_output is None:
        # splitted_root_path = os.path.split(root_dir)
        # path_to_output = os.path.join(splitted_root_path[0], f"{splitted_root_path[1]}_spacy")
        # todo: add proper automatically created output folder
        path_to_output = "spacy_annotation"

    Path(path_to_output).mkdir(parents=True, exist_ok=True)

    for curr_dir, _, files in os.walk(root_dir):
        current_out_dir = os.path.join(path_to_output, curr_dir[-2:])
        Path(current_out_dir).mkdir(parents=True, exist_ok=True)
        for file in files:
            path_to_input_file = os.path.join(curr_dir, file)
            logger.info("Processing of file {}".format(path_to_input_file))
            current_out_file = os.path.join(current_out_dir, file + "_spacy.json")
            with open(current_out_file, "w", encoding="UTF-8") as o_json:
                json.dump(get_analysed_pages(path_to_input_file), o_json)
            logger.info("File {} is processed and saved to {}".format(path_to_input_file, current_out_file))
    log_section("WikiDump processing is finished", logger)


def get_analysed_pages(path_to_input_file: str) -> List:
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
            wiki_input["text"] = extract_abstract(wiki_input["text"])
            abstract_annotation = abstract_analyser(wiki_input["text"]).to_json()  # get parsed abstracts_test
            if abstract_annotation is None:
                continue
            page_annotation = {**{"doc_id": wiki_input["id"]}, **abstract_annotation}
            all_pages.append(page_annotation)
        logger.info("{}/{} pages were annotated.".format(file_length-skipped_pages, file_length))
    return all_pages
