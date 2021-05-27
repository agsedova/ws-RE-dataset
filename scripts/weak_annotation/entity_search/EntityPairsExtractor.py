import json
import os


class EntityPairsExtractor:
    """
    This class extracts and indexes the entity pairs from the sentences labeled with patterns and saved in dygie format.
    It also saves the relations they correspond to in order to use this information for further sentence labeling.
    """

    def __init__(self, path_to_dygie, path_to_output):
        self.path_to_dygie = path_to_dygie
        self.path_to_output = path_to_output

        self.entity_pair_to_idx = {}
        self.entity_pair_to_rel = {}

    def get_text_ent_pair(self, ent1, ent2):
        return ", ".join(["_".join(ent1), "_".join(ent2)])

    def calculate_ent_pair_idx(self):
        if len(self.entity_pair_to_idx) == 0:
            return 0
        else:
            return list(self.entity_pair_to_idx.values())[-1] + 1

    def update_ent_pair_to_relation(self, entity_pair, relation):
        if entity_pair in self.entity_pair_to_idx:
            entity_pair_idx = self.entity_pair_to_idx[entity_pair]
            if relation not in self.entity_pair_to_rel[entity_pair_idx]:
                self.entity_pair_to_rel[entity_pair_idx].append(relation)
        else:
            entity_pair_idx = self.calculate_ent_pair_idx()
            self.entity_pair_to_idx[entity_pair] = entity_pair_idx
            self.entity_pair_to_rel[entity_pair_idx] = [relation]

    def process_pattern_match(self, sample, match_info):
        """
        input samples: sample tokens as a list
        input match_info: info about extracted relations in sample saved in dygie
            (ent_1_start_pos, ent_1_end_pos, ent_2_start_pos, ent_2_end_pos, relation)
        """
        entity_pair = self.get_text_ent_pair(sample[match_info[0]:match_info[1]+1],
                                             sample[match_info[2]:match_info[3]+1])
        self.update_ent_pair_to_relation(entity_pair, match_info[4])

    def save_dicts(self):
        with open(os.path.join(self.path_to_output, "entity_pair_ids.json"), "w+") as file:
            json.dump(self.entity_pair_to_idx, file)
        with open(os.path.join(self.path_to_output, "entity_pair_to_rel.json"), "w+") as file:
            json.dump(self.entity_pair_to_rel, file)

    def extract_entity_pairs(self):
        for dir, _, files in os.walk(self.path_to_dygie):
            for file in files:
                if not file.endswith('_dygie.json'):
                    continue
                with open(os.path.join(dir, file), "r") as f:
                    annotated_samples = json.load(f)
                for sample in annotated_samples:
                    sample_text = [item for sublist in sample["sentences"] for item in sublist]
                    for sample_relations in sample["relations"]:
                        if len(sample_relations) == 0:
                            continue
                        for relation in sample_relations:
                            self.process_pattern_match(sample_text, relation)
        self.save_dicts()
# if __name__ == "__main__":
#     EntityPairsExtractor("../data/output/wikidump/retrieved_4th_ver",
#                          "../data/output/wikidump/retrieved_4th_ver/_ent_pairs").extract_entity_pairs()
