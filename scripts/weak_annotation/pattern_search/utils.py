from typing import Dict, Tuple


def calculate_ent_indices(ent: dict, sent: dict) -> dict:
    """ Calculate new entity indices in a sentence """
    ent["start_sent"] = ent["start"] - sent["start"]
    ent["end_sent"] = ent["end"] - sent["start"]
    return ent


def get_pattern_id(pattern: str, pattern2id: Dict, pattern_counter: int) -> Tuple[int, int]:
    """ Returns a pattern id from pattern2id dict or creates a new pattern : pattern_id pair """
    if pattern not in pattern2id.keys():
        pattern_id = pattern_counter
        pattern2id[pattern] = pattern_id
        pattern_counter += 1
    else:
        pattern_id = pattern2id[pattern]
    return pattern_id, pattern_counter


def save_glob_stat_to_csv(stat_dict: Dict, id2relation: Dict, out_file: str) -> None:
    with open(out_file, 'w') as csvfile:
        for key in stat_dict.keys():
            csvfile.write("%s\t%s\n" % (id2relation[key], stat_dict[key]))
