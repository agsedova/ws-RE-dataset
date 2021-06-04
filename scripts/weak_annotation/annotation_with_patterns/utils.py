import ast
from pathlib import Path
import json
import os
from typing import Dict, Tuple, Union, List

import numpy as np
import pandas as pd
from joblib import dump
import re

from scipy.sparse import csr_matrix


def read_relations_df(path_to_relations: str) -> pd.DataFrame:
    relations = pd.read_csv(path_to_relations)
    try:
        relations['entity_types'] = relations['entity_types'].apply(lambda x: ast.literal_eval(x))
        return relations
    except ValueError:
        relations['entity_types'] = relations['entity_types'].apply(
            lambda x: tuple(re.sub(r"([\(\)])", "", str(x)).split(", "))
        )
        return relations


def read_patterns_df(path_to_patterns: str) -> pd.DataFrame:
    patterns = pd.read_csv(path_to_patterns)
    patterns['relation'] = patterns['relation'].apply(lambda x: list(set(ast.literal_eval(x))))
    patterns['relation_id'] = patterns['relation_id'].apply(lambda x: list(set(ast.literal_eval(x))))
    return patterns


def calculate_ent_indices(ent: dict, sent: dict) -> dict:
    """ Calculate new entity indices in a sentence """
    ent["start_sent"] = ent["start"] - sent["start"]
    ent["end_sent"] = ent["end"] - sent["start"]
    return ent


def read_entities_df(path_to_ent_pairs: str):
    ent_pairs = pd.read_csv(path_to_ent_pairs)
    ent_pairs['pattern'] = ent_pairs['pattern'].apply(lambda x: list(set(ast.literal_eval(x))))
    ent_pairs['pattern_id'] = ent_pairs['pattern_id'].apply(lambda x: list(set(ast.literal_eval(x))))
    ent_pairs['relation'] = ent_pairs['relation'].apply(lambda x: list(set(ast.literal_eval(x))))
    ent_pairs['relation_id'] = ent_pairs['relation_id'].apply(lambda x: list(set(ast.literal_eval(x))))
    return ent_pairs


def get_pattern_id(pattern: str, pattern2id: Dict, pattern_counter: int) -> Tuple[int, int]:
    """ Returns a pattern id from pattern2id dict or creates a new pattern : pattern_id pair """
    if pattern not in pattern2id.keys():
        pattern_id = pattern_counter
        pattern2id[pattern] = pattern_id
        pattern_counter += 1
    else:
        pattern_id = pattern2id[pattern]
    return pattern_id, pattern_counter


def read_wiki_dicts_from_file(inp: str) -> Union[Dict, None]:
    with open(inp) as input_file:
        try:
            data = json.load(input_file)
            return data
        except json.decoder.JSONDecodeError:
            return None
        except UnicodeDecodeError:
            return None


def save_glob_stat_to_csv(stat_dict: Dict, id2relation: Dict, out_file: str) -> None:
    with open(out_file, 'w') as csvfile:
        for key in stat_dict.keys():
            csvfile.write("%s\t%s\n" % (id2relation[key], stat_dict[key]))


def save_knodle_output(
        samples_cut: List, samples_full: List, arg1_poses: List, arg2_poses: List, z_matrix: np.ndarray,
        t_matrix: np.ndarray, out: str, prefix: str = ""
) -> None:
    Path(out).mkdir(parents=True, exist_ok=True)

    # check matrices dimensions
    assert z_matrix.shape[1] == t_matrix.shape[0]
    assert z_matrix.shape[0] == len(samples_cut)
    assert len(samples_full) == len(arg1_poses) == len(arg2_poses) == len(samples_cut)

    # save cut samples as csv
    pd.DataFrame({"sample_cut": samples_cut}).to_csv(os.path.join(out, f'knodle_samples_cut_{prefix}.csv'), index=None)

    # save full samples and their indices as csv
    pd.DataFrame({"sample_full": samples_full, "arg1_pos": arg1_poses, "arg2_pos": arg2_poses}).to_csv(
        os.path.join(out, f'knodle_samples_full_indices_{prefix}.csv'), index=None#
    )

    # save z matrix
    knodle_z_matrix_sparse = csr_matrix(z_matrix)
    dump(knodle_z_matrix_sparse, os.path.join(out, f"knodle_z_{prefix}.lib"))


def build_t_matrix(corr_dict: Dict, t_matrix_dim: Tuple) -> np.ndarray:
    """ The function builds knodle t matrix of a given dimension from a dict """
    t_matrix = np.zeros((t_matrix_dim[0], t_matrix_dim[1]))
    for key, value in corr_dict.items():
        if isinstance(value, list) or isinstance(value, set):
            value = [int(r_id) for r_id in value]
        t_matrix[key][value] = 1
    return t_matrix
