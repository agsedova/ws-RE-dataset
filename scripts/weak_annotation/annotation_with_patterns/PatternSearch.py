import itertools
import json
import os
import re
import logging
from pathlib import Path
from typing import Dict, Tuple, List, Union

import pandas as pd
import numpy as np
from scripts.weak_annotation.commons import DYGIE_RELATIONS
from joblib import dump
from scripts.utils import (
    get_sentence_matches, prepare_output_dygie, save_loc_stat_to_csv, prepare_output_knodle, return_entity_pair
)
from scripts.weak_annotation.annotation_with_patterns.build_dicts import (
    get_types2entities, get_relation_types_dict, collect_dygie_patterns, collect_knodle_patterns
)

from scripts.weak_annotation.annotation_with_patterns.text_processing import get_sent_for_comparing
from scripts.weak_annotation.annotation_with_patterns.utils import (
    calculate_ent_indices, save_glob_stat_to_csv, read_wiki_dicts_from_file, save_knodle_output,
    build_t_matrix, read_relations_df
)

logger = logging.getLogger(__name__)


class PatternSearch:

    def __init__(
            self,
            path_to_data: str,
            path_to_relations: str,
            path_to_patterns: str,
            path_to_output: str,
            output_format: str = "knodle"
    ):
        """

        HANDLING OF KNODLE EDGE CASES. The one2many cases are handling in the following way:
            - if several entity pairs match in one sample, this sample is saved separately for each entity pair.
                In this case z matrix has different rows for each of the sample correspondingly; each row is one-hot.
            - if one entity pair corresponds to different patterns, the sample is not duplicated.
                In this case row in z matrix has more than one "1" entry.
            - if pattern corresponds to different relations, t matrix (pattern x relation) is not one-hot
                (not ok for knodle, will be filtered out later). Consequently, entity pair may corresdond to different
                relations as well, what makes t matrix (entity pairs x relation) potentially not one-hot as well.

        :param path_to_data:
        :param path_to_patterns:
        :param path_to_output:
        """
        self.path_to_data = path_to_data
        self.path_patterns = path_to_patterns
        self.output_format = output_format
        self.path_out = os.path.join(path_to_output, "knodle_ann_patterns")
        Path(self.path_out).mkdir(parents=True, exist_ok=True)

        self.matches_counter = 0

        if self.output_format == "dygie":
            self.id2relation = DYGIE_RELATIONS
            self.rel2types = get_relation_types_dict()  # build self.rel2types dict {relation_id : arg_types}
            self.patterns, self.rel2patterns, self.pattern_id2pattern, self.pattern_id2pattern_raw = \
                collect_dygie_patterns(self.path_patterns, self.path_out)

        elif self.output_format == "knodle":

            self.relation = read_relations_df(path_to_relations)
            self.rel2rel_id = dict(zip(self.relation.relation, self.relation.relation_id))
            self.rel_id2rel = dict(zip(self.relation.relation_id, self.relation.relation))
            self.rel2types = dict(zip(self.relation.relation_id, self.relation.entity_types))

            self.patterns, self.rel2patterns = collect_knodle_patterns(
                self.path_patterns, self.path_out, self.rel2rel_id
            )

            self.pattern_id2pattern = dict(zip(self.patterns.pattern_id, self.patterns.pattern))
            self.pattern_id2pattern_raw = dict(zip(self.patterns.pattern_id, self.patterns.pattern))
            self.pattern_id2pattern_regex = dict(zip(self.patterns.pattern_id, self.patterns.pattern_regex))
            self.pattern2rel_id = dict(zip(self.patterns.pattern, self.patterns.relation_id))
            self.pattern_id2rel_id = dict(zip(self.patterns.pattern_id, self.patterns.relation_id))

        # todo: check in general, what if there is one-to-multiple correspondence anywhere
        self.entity_pairs = []
        self.processed_entity_pairs = []

        self.knodle_t_matrix = build_t_matrix(
            self.pattern_id2rel_id, (len(self.pattern2rel_id), len(self.rel2rel_id))
        )
        dump(self.knodle_t_matrix, os.path.join(self.path_out, "knodle_t.lib"))

        self.stat_rel_matches = dict.fromkeys(self.rel2types.keys(), 0)  # intialize statistics

    def retrieve_patterns(self):
        Path(self.path_out).mkdir(parents=True, exist_ok=True)

        if self.output_format == "dygie":
            self.retrieve_patterns_n_return_dygie()
        elif self.output_format == "knodle":
            self.retrieve_patterns_n_return_knodle()
        else:
            raise ValueError("Unknown output format! You can choose either knodle or dygie output.")

        self.entity_pairs = pd.DataFrame(self.entity_pairs)
        self.entity_pairs.to_csv(os.path.join(os.path.split(self.path_out)[0], 'entity_pairs.csv'), index=False)

    def retrieve_patterns_n_return_dygie(self):

        if os.path.isdir(self.path_to_data):  # if we retrieve patterns in multiple files (input is a directory)
            self._search_patterns_in_multiple_files_dygie()
        elif os.path.isfile(self.path_to_data):  # if we retrieve patterns in a single file
            _ = self._search_patterns_in_file_dygie()
            logger.info(f'Total match: {self.matches_counter}')
        else:
            logger.info("Check your input! It's neither directory nor file")

    def retrieve_patterns_n_return_knodle(self):
        if os.path.isdir(self.path_to_data):  # if we retrieve patterns in multiple files (input is a directory)
            self._search_patterns_in_multiple_files_knodle()
        elif os.path.isfile(self.path_to_data):  # if we retrieve patterns in a single file
            self._search_patterns_in_file_knodle(self.path_to_data, [self.path_to_data])
        else:
            raise ValueError("Check your input! It's neither directory nor file")

    def _search_patterns_in_multiple_files_dygie(self):
        dygie_output_all = []
        for curr_dir, _, files in os.walk(self.path_to_data):
            logger.info(f'Pattern search in {curr_dir}.')
            self.matches_counter = 0

            current_out_dir = os.path.join(self.path_out, "retrieved", curr_dir[-2:])
            Path(current_out_dir).mkdir(parents=True, exist_ok=True)

            dygie_output_all.append(self._search_patterns_in_file_dygie(curr_dir, current_out_dir, files))
            logger.info(f'Total match: {self.matches_counter}')
        return dygie_output_all

    def _search_patterns_in_multiple_files_knodle(self):
        for curr_dir, _, files in os.walk(self.path_to_data):
            curr_out = os.path.join(self.path_out, os.path.split(curr_dir)[1])
            Path(curr_out).mkdir(parents=True, exist_ok=True)

            logger.info(f'Pattern search in {curr_dir}.')
            self.matches_counter = 0

            self._search_patterns_in_file_knodle(curr_dir, files, curr_out)
            logger.info(f'Total match: {self.matches_counter}')

    def _search_patterns_in_file_dygie(self, curr_dir: str, current_out_dir: str, files: List) -> List:

        ent_pair2rel, pattern2rel, ent_pair2pattern = {}, {}, {}
        dygie_output = []
        for file in files:
            Path(os.path.join(current_out_dir, file[:-11])).mkdir(parents=True, exist_ok=True)
            self.matches_counter = 0

            # load list of dictionaries containing with wiki articles
            wiki_pages = read_wiki_dicts_from_file(os.path.join(curr_dir, file))
            if not wiki_pages:
                continue

            dygie_output.append(self._find_pattern_matches_n_return_dygie(
                wiki_pages, ent_pair2rel, pattern2rel, ent_pair2pattern,
                os.path.join(current_out_dir, file[:-11])
            ))

        return dygie_output

    def _search_patterns_in_file_knodle(self, curr_dir: str, files: List, out: str):

        self.stat_rel_matches = dict.fromkeys(self.stat_rel_matches , 0)
        samples_cut, samples_full, arg1_poses, arg2_poses = [], [], [], []
        z_matrix = np.empty((0, len(self.pattern_id2pattern)))
        ent_pair2rel, pattern2rel, ent_pair2pattern = {}, {}, {}

        for file in files:
            # load list of dictionaries containing with wiki articles
            wiki_pages = read_wiki_dicts_from_file(os.path.join(curr_dir, file))
            if not wiki_pages:
                continue

            # create output folder
            curr_out = os.path.join(out, file.split(".")[0])
            Path(curr_out).mkdir(parents=True, exist_ok=True)

            # perform search in each wiki article & collect statistics
            stat_rel = {key: 0 for key in self.stat_rel_matches.keys()}

            curr_samples_cut, curr_samples_full, curr_z_matrix, arg1_poss, arg2_poss = \
                self._find_pattern_matches_n_return_knodle(
                    wiki_pages, ent_pair2rel, pattern2rel, ent_pair2pattern, stat_rel
                )

            if not curr_samples_cut:
                continue
            samples_full += curr_samples_full
            samples_cut += curr_samples_cut
            arg1_poses += arg1_poss
            arg2_poses += arg2_poss
            z_matrix = np.vstack((z_matrix, curr_z_matrix))

            save_knodle_output(samples_cut, samples_full, arg1_poses, arg2_poses, z_matrix, self.knodle_t_matrix, curr_out)
            save_glob_stat_to_csv(self.stat_rel_matches, self.rel_id2rel, os.path.join(curr_out, 'stat.csv'))

    def _find_pattern_matches_n_return_dygie(self, wiki_pages, entpair2rel, pattern2rel, entpair2pattern, out) -> List:
        dygie_output = []

        # perform search in each wiki article & collect statistics
        stat_rel = {key: 0 for key in self.stat_rel_matches.keys()}

        for w_page in wiki_pages:
            matches = self._find_pattern_matches(w_page, entpair2rel, pattern2rel, entpair2pattern, stat_rel)
            if not matches:
                continue
            dygie_output.append(prepare_output_dygie(matches, w_page))  # prepares dygie specific output

        # todo: save as one dict (in order to concatenate later)
        with open(os.path.join(out, "dygie.json"), "w+") as out_j:
            json.dump(dygie_output, out_j)
        save_loc_stat_to_csv(os.path.join(out, "stat.csv"), stat_rel, self.id2relation)

        return dygie_output

    def _find_pattern_matches_n_return_knodle(
            self, wiki_pages, ent_pair2rel, pattern2rel, ent_pair2pattern, stat_rel
    ) -> Tuple[List, List, np.ndarray, List, List]:
        samples_cut, samples_full, arg1_poses, arg2_poses = [], [], [], []
        z_matrix = np.empty((0, len(self.pattern_id2pattern)))
        for w_page in wiki_pages:
            matches = self._find_pattern_matches(w_page, ent_pair2rel, pattern2rel, ent_pair2pattern, stat_rel)
            if not matches:
                continue
            # prepares knodle output
            curr_samples_cut, curr_samples_full, curr_z_matrix_row, arg1_pos, arg2_pos = prepare_output_knodle(
                matches, w_page, len(self.pattern_id2pattern)
            )
            samples_cut += curr_samples_cut
            samples_full += curr_samples_full
            arg1_poses += arg1_pos
            arg2_poses += arg2_pos
            z_matrix = np.vstack((z_matrix, curr_z_matrix_row))

        return samples_cut, samples_full, z_matrix, arg1_poses, arg2_poses

    def _find_pattern_matches(
            self, wiki_page: Dict, ent_pair2rel: Dict, pattern2rel: Dict, ent_pair2pattern: Dict, stat_rel: Dict
    ) -> Union[List, None]:
        """
        :param wiki_page: dictionary that contains the information about a wiki article
        ("doc_id", "text", "ents", "sents", "tokens").
        """
        types2entities = get_types2entities(wiki_page)  # dict {entity_type : [entities]}
        rel2retrieved_args = {}

        for rel_id, pattern_ids in self.rel2patterns.items():
            rel2retrieved_args[rel_id] = []
            types = self.rel2types[rel_id]  # entity types that are acceptable for this relation

            # if there are no entities of these types, skip the sentence
            if not (types[0] in types2entities.keys() and types[1] in types2entities.keys()):
                continue

            for ent1, ent2 in itertools.product(types2entities[types[0]], types2entities[types[1]]):
                for sent in wiki_page["sents"]:  # for each sentence in a document
                    # make sure that entities are in one sentence
                    if not (sent["start"] <= min(ent1["start"], ent2["start"]) <= sent["end"] and
                            sent["start"] <= max(ent1["end"], ent2["end"]) <= sent["end"]):
                        continue

                    # calculate entities' indices according to the sentence
                    ent1 = calculate_ent_indices(ent1, sent)
                    ent2 = calculate_ent_indices(ent2, sent)

                    # extract the sentence we are working now with
                    sent_text = wiki_page["text"][sent["start"]:sent["end"]]
                    # look for patterns in this sentence
                    rel2retrieved_args = self._perform_search_in_sentence(
                        sent_text, ent1, ent2, types, rel_id, pattern_ids, rel2retrieved_args, ent_pair2pattern,
                        ent_pair2rel, pattern2rel, stat_rel
                    )

        if any(rel2retrieved_args.values()):  # check if there were any matches in doc
            return get_sentence_matches(rel2retrieved_args, self.rel_id2rel)
        else:
            return None

    def _perform_search_in_sentence(
            self, sent: str, ent1: Dict, ent2: Dict, types: Tuple, rel: str, patterns: set, curr_args_output: Dict,
            ent_pair2pattern: Dict, ent_pair2rel: Dict, pattern2rel: Dict, stat_rel: Dict
    ) -> Dict:
        """ Look for pattern matches in a sentence. """

        sent_to_compare = get_sent_for_comparing(ent1, ent2, types, sent)

        if not sent_to_compare:
            return curr_args_output

        matches = self._search_by_pattern(
            rel, patterns, sent, sent_to_compare, ent1, ent2, ent_pair2pattern, ent_pair2rel, pattern2rel, stat_rel
        )
        if matches[rel]:
            for key, value in matches.items():
                curr_args_output[key] += value

        return curr_args_output

    def _search_by_pattern(
            self, rel: str, patterns: set, sent: str, sent_to_compare: str, ent1: Dict, ent2: Dict,
            ent_pair2pattern: Dict, ent_pair2rel: Dict, pattern2rel: Dict, stat_rel: Dict
    ) -> Dict:
        """
        Look up each pattern from the list in string. If there is a match, the information about matched entities
        are added to the dict: {rel_id: [match_1, match_2, ...]}, where
            match_1 = [ent1_params, ent2_params, pattern_id]
        """
        rel2matches = {rel: []}

        for pattern_id in patterns:
            pattern_regex = self.pattern_id2pattern_regex[pattern_id]  # take pattern regex
            match = re.search(pattern_regex, sent_to_compare)

            if match:
                self.stat_rel_matches[rel] += 1  # increment whole statistics
                stat_rel[rel] += 1  # increment local sentence statistics
                self.matches_counter += 1
                rel2matches[rel].append([ent1, ent2, {"pattern_id": pattern_id}])

                # add pattern to relation correspondence
                pattern2rel[pattern_id] = rel

                curr_ent_pair = return_entity_pair(sent, ent1, ent2)  # compose an entity pair
                ent_pair2rel[curr_ent_pair] = rel
                ent_pair2pattern[curr_ent_pair] = self.pattern_id2pattern_raw[pattern_id]

                if curr_ent_pair in self.processed_entity_pairs:
                    for entry in self.entity_pairs:
                        if entry["entity_pair"] == curr_ent_pair:
                            entry["pattern"].add(self.pattern_id2pattern_raw[pattern_id])
                            entry["pattern_id"].add(pattern_id)
                            entry["relation"].add(self.rel_id2rel[rel])
                            entry["relation_id"].add(rel)
                else:
                    curr_ent_pair_id = len(self.processed_entity_pairs)
                    self.entity_pairs.append(
                        {"entity_pair_id": curr_ent_pair_id,
                         "entity_pair": curr_ent_pair,
                         "pattern": {self.pattern_id2pattern_raw[pattern_id]},
                         "pattern_id": {pattern_id},
                         "relation": {self.rel_id2rel[rel]},
                         "relation_id": {rel}})
                    self.processed_entity_pairs.append(curr_ent_pair)
        return rel2matches
