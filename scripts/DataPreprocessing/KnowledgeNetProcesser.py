import json
import spacy
import os
from pathlib import Path


nlp = spacy.load("en_core_web_sm")


class KnowledgeNetProcesser:

    def __init__(self, path_to_input, path_to_output):
        self.source_file = path_to_input
        self.path_to_output = path_to_output
        Path(self.path_to_output).mkdir(parents=True, exist_ok=True)

    def process_knowledgenet_data(self):
        all_docs = []
        with open(self.source_file, "r", encoding="UTF-8") as input_file:
            for num, line in enumerate(input_file, 1):
                doc = json.loads(line)
                doc["sentences"][0].append(".")
                text = " ".join([item for sentence in doc["sentences"] for item in sentence])
                doc_annotation = nlp(text).to_json()        # spacy annotation
                if doc_annotation is not None:
                    doc_annotation = {**{"doc_id": doc["doc_key"]}, **doc_annotation}
                    all_docs.append(doc_annotation)
        with open(self.path_to_output + "knwldgn_dev_spacy.json", "w", encoding="UTF-8") as o_json:
            json.dump(all_docs, o_json)


if __name__ == "__main__":
    KnowledgeNetProcesser("../../data/knwldgn/knwldgn_dev.json",
                          "../../data/output/").process_knowledgenet_data()



