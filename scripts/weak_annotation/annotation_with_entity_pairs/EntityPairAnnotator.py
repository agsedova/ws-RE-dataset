import argparse
import itertools
import logging
from copy import copy
from pathlib import Path
import sys
import os
from typing import List, Tuple

import numpy as np

from scripts.utils import return_entity_pair
from scripts.weak_annotation.annotation_with_entity_pairs.utils import ents_in_sent
from scripts.weak_annotation.annotation_with_patterns.utils import (
    read_wiki_dicts_from_file, save_knodle_output, calculate_ent_indices, save_glob_stat_to_csv,
    build_t_matrix, read_relations_df, read_patterns_df, read_entities_df
)

logger = logging.getLogger(__name__)


class EntityPairsAnnotator:

    def __init__(
            self,
            path_to_spacy_data: str,
            path_to_ent_pairs: str,
            path_to_relations: str,
            path_to_patterns: str,
            path_to_output: str
    ):
        self.path_to_spacy_data = path_to_spacy_data

        self.path_to_output = os.path.join(path_to_output, "annotation_with_entity_pairs")
        Path(self.path_to_output).mkdir(parents=True, exist_ok=True)

        # read entity pairs, relations and patterns info
        self.ent_pairs = read_entities_df(path_to_ent_pairs)
        self.patterns = read_patterns_df(path_to_patterns)
        self.relation = read_relations_df(path_to_relations)

        # create necessary dictionaries
        self.rel_id2rel = dict(zip(self.relation.relation_id, self.relation.relation))

        self.pattern2pattern_id = dict(zip(self.patterns.pattern, self.patterns.pattern_id))
        self.pattern_id2pattern = dict(zip(self.patterns.pattern_id, self.patterns.pattern))
        self.pattern_id2relation_id = dict(zip(self.patterns.pattern_id, self.patterns.relation_id))

        self.ent_pair2ent_pair_id = dict(zip(self.ent_pairs.entity_pair, self.ent_pairs.entity_pair_id))
        self.ent_pair_id2ent_pair = dict(zip(self.ent_pairs.entity_pair_id, self.ent_pairs.entity_pair))
        self.ent_pair2pattern_id = dict(zip(self.ent_pairs.entity_pair, self.ent_pairs.pattern_id))
        self.ent_pair_id2rel_id = dict(zip(self.ent_pairs.entity_pair_id, self.ent_pairs.relation_id))

        # initialize variables for collecting statistics
        self.matches_counter = 0
        self.stat_ent_pair_matches = dict.fromkeys(self.ent_pair2ent_pair_id.values(), 0)        # intialize statistics
        self.stat_pattern_matches = dict.fromkeys(self.pattern2pattern_id.values(), 0)

    def annotate_data_with_ent_pairs(self):

        # sys.stdout = open(os.path.join(self.path_to_output, "console"), 'w')

        if os.path.isdir(self.path_to_spacy_data):  # if the data is stored in multiple files (input is a directory)
            samples, z_matrix_samples2entpairs, z_matrix_samples2patterns = \
                self.annotate_multiple_files()
            logger.info(f"Total match: {self.matches_counter}")

        elif os.path.isfile(self.path_to_spacy_data):  # if there is only one single file
            samples, z_matrix_samples2entpairs, z_matrix_samples2patterns = \
                self.annotate_data(self.path_to_spacy_data)
            logger.info(f"Total match: {self.matches_counter}")
        else:
            logger.info("Check your input! It's neither directory nor file")
            return

        t_matrix_entpairs2rel = build_t_matrix(
            self.ent_pair_id2rel_id, (len(self.ent_pair_id2rel_id), len(self.rel_id2rel))
        )
        t_matrix_patterns2rel = build_t_matrix(
            self.pattern_id2relation_id, (len(self.pattern_id2relation_id), len(self.rel_id2rel))
        )
        save_knodle_output(
            samples, z_matrix_samples2entpairs, t_matrix_entpairs2rel, self.path_to_output, prefix="entpairs"
        )
        save_knodle_output(
            samples, z_matrix_samples2patterns, t_matrix_patterns2rel, self.path_to_output, prefix="patterns"
        )

        # save overall statistics
        save_glob_stat_to_csv(
            self.stat_ent_pair_matches, self.ent_pair_id2ent_pair, os.path.join(self.path_to_output, "stat_entpairs.csv")
        )
        save_glob_stat_to_csv(
            self.stat_pattern_matches, self.pattern_id2pattern, os.path.join(self.path_to_output, "stat_patterns.csv")
        )
        # sys.stdout.close()

    def annotate_multiple_files(self):
        samples = []
        z_matrix_samples2entpairs = np.empty((0, len(self.ent_pair2ent_pair_id)))
        z_matrix_samples2patterns = np.empty((0, len(self.pattern2pattern_id)))

        for dir, _, files in os.walk(self.path_to_spacy_data):
            logger.info(f"Annotation of files in {dir}...")

            for file in files:
                curr_samples, curr_z_matrix_samples2entpairs, curr_z_matrix_samples2patterns = \
                    self.annotate_data(os.path.join(dir, file))
                if len(curr_samples) == 0 and curr_z_matrix_samples2entpairs.size <= 0 and \
                        curr_z_matrix_samples2patterns.size <= 0:
                    continue

                samples += curr_samples
                z_matrix_samples2entpairs = np.vstack((z_matrix_samples2entpairs, curr_z_matrix_samples2entpairs))
                z_matrix_samples2patterns = np.vstack((z_matrix_samples2patterns, curr_z_matrix_samples2patterns))

        return samples, z_matrix_samples2entpairs, z_matrix_samples2patterns

    def annotate_data(self, path_data: str) -> Tuple[List, np.ndarray, np.ndarray]:
        wiki_pages = read_wiki_dicts_from_file(path_data)
        if not wiki_pages:
            return [], np.empty((0, 0)), np.empty((0, 0))
        return self.find_entity_pairs_match(wiki_pages)

    def find_entity_pairs_match(self, data):
        samples = []
        z_matrix_samples2entpairs = np.empty((0, len(self.ent_pair2ent_pair_id)))
        z_matrix_samples2patterns = np.empty((0, len(self.pattern2pattern_id)))

        for doc in data:
            matched_entity_pairs = []
            for ent1, ent2 in itertools.permutations(doc["ents"], 2):
                curr_ent1, curr_ent2 = copy(ent1), copy(ent2)
                sent = ents_in_sent(doc, curr_ent1, curr_ent2)

                if sent:
                    sent_text = doc["text"][sent["start"]:sent["end"]]
                    curr_ent1 = calculate_ent_indices(curr_ent1, sent)
                    curr_ent2 = calculate_ent_indices(curr_ent2, sent)
                    ent_pair = return_entity_pair(sent_text, curr_ent1, curr_ent2)

                    if ent_pair in list(self.ent_pair2pattern_id.keys()) and ent_pair not in matched_entity_pairs:
                        ent_pair_id = self.ent_pair2ent_pair_id[ent_pair]
                        pattern_id = self.ent_pair2pattern_id[ent_pair]

                        z_row_samples2entpairs = np.zeros((len(self.ent_pair2ent_pair_id), ))
                        z_row_samples2entpairs[ent_pair_id] = 1

                        z_row_samples2patterns = np.zeros((len(self.pattern2pattern_id), ))
                        z_row_samples2patterns[pattern_id] = 1

                        samples.append(sent_text)
                        z_matrix_samples2entpairs = np.vstack((z_matrix_samples2entpairs, z_row_samples2entpairs))
                        z_matrix_samples2patterns = np.vstack((z_matrix_samples2patterns, z_row_samples2patterns))

                        matched_entity_pairs.append(ent_pair)
                        self.matches_counter += 1
                        self.stat_ent_pair_matches[ent_pair_id] += 1     # increment statistics
                        for p_id in pattern_id:
                            self.stat_pattern_matches[p_id] += 1  # increment statistics
        return samples, z_matrix_samples2entpairs, z_matrix_samples2patterns


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog=os.path.basename(sys.argv[0]))
    parser.add_argument("--path_to_spacy_data", help="")
    parser.add_argument("--path_to_ent_pairs", help="")
    parser.add_argument("--path_to_relations", help="")
    parser.add_argument("--path_to_patterns", default=None, help="")
    parser.add_argument("--path_to_output", default=None, help="")
    args = parser.parse_args()

    EntityPairsAnnotator(
        args.path_to_spacy_data,
        args.path_to_ent_pairs,
        args.path_to_relations,
        args.path_to_patterns,
        args.path_to_output
    ).annotate_data_with_ent_pairs()
