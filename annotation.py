# coding=<UTF-8>

import json
import sys
import nl_api
from spacy.lang.en import English
import re

import torch

nlp = English()
nlp.add_pipe(nlp.create_pipe('sentencizer'))

sentence_index = []

# def main(input_file):
#
#     with open(input_file, encoding="UTF-8") as f:
#         data = json.load(f)
#
#         for doc in data:
#             doc["annotatedSentences"] = parse_document(doc["text"])
#
#         with open('wiki_00_abstract_parsed.json5', 'w') as outfile:
#             json.dump(data, outfile)
#
#


def collect_patterns(patterns_file):
    patterns = {}
    with open(patterns_file) as input:
        for line in input.readlines():
            if not line.startswith("#") and line != "\n":
                relation, pattern = line.replace("\n", "").split(" ", 1)
                # pattern = pattern.replace("\n", "").split(" ", 1)
                # pattern = (pattern[0], pattern[1].rsplit(" ", 1)[0], pattern[1].rsplit(" ", 1)[1])
                patterns[pattern] = relation
    return patterns


def check_pattern(sentence, patterns):
    for patt in patterns:
        print(patt)
        patt = re.sub(patt, "$ARG1", "")
        match = re.search(r"")

    return ""


def build_sentence_annotation(abstract_text, page_offset, annotation, patterns):
    sentences = [sent.string.strip() for sent in nlp(abstract_text).sents]

    # annotated_data = {"annotatedSentences": [], "statements": []}
    ann_abstracts = []
    entity2id = {}

    for sent in sentences:

        check_pattern(sent, patterns)

        preprocessed_entities = []
        preprocessed_chars = 0

        sent_idx_begin = abstract_text.find(sent)
        sent_idx_end = sent_idx_begin + len(sent)
        sent_offset = page_offset + ":" + str(sent_idx_begin) + ":" + str(sent_idx_end)

        ann_sent = {"sentenceId": sent_offset, "sentenceText": sent, "sentenceStart": sent_idx_begin,
                    "sentenceEnd": sent_idx_end, "entities": []}

        sentence_index.append({"sentenceId": sent_offset, "sentenceText": sent, "abstractText": abstract_text})

        for entity in annotation[0]["entities"]:
            if 'mentions' in entity.keys():
                mentions = [men for men in entity["mentions"] if men["beginOffset"] < sent_idx_end and
                            men["endOffset"] > sent_idx_begin]
                if len(mentions) > 0:
                    for mention in mentions:
                        entity_types = [e["name"] for e in entity["allTypes"]]
                        entity_text = mention["text"]
                        ent_begin = mention["beginOffset"] - preprocessed_chars
                        ent_end = mention["endOffset"] - preprocessed_chars
                        ent_id = sent_offset + ":" + str(ent_begin) + ":" + str(ent_end)
                        ent_conf = mention["confidence"]
                        ent_uris = [uri for uri in entity["allUris"]]

                        ent_ref = [{"entityName": entity['name'], "entityConfidence": ent_conf, "entityUri": ent_uris,
                                    "entityTypes": entity_types}]

                        if ent_id not in preprocessed_entities:
                            ent_dict = {"entityId": ent_id, "entityInSentence": entity_text,
                                        "entityStart": ent_begin, "entityEnd": ent_end,
                                        "entityReferences": ent_ref}
                            ann_sent["entities"].append(ent_dict)
                        else:
                            next(item for item in ann_sent["entities"] if item["entityId"] == ent_id)["entityReferences"] \
                                .append(ent_ref)
                        preprocessed_entities.append(ent_id)

                        entity2id[entity_text] = ent_id

        ann_sent['entities'] = sorted(ann_sent['entities'], key=lambda k: k['entityId'])

        ann_abstracts.append(ann_sent)
        preprocessed_chars += sent_idx_end + 1

    print("New annotated abstract is saved")

    return ann_abstracts


def main(data, patterns):

    abstract_text = data["text"]
    page_offset = data["id"]

    annotation = nl_api.main(abstract_text)

    if type(annotation) is list and len(annotation) == 1 and "entities" in annotation[0].keys():
        # and "statements" in annotation[0].keys():
        return build_sentence_annotation(abstract_text, page_offset, annotation, patterns)

        # for statement in annotation[0]["statements"]:
        #
        #     evidences = []
        #     if len(statement["evidence"]) > 0:
        #         for ev in statement["evidence"]:
        #             entity, value = [], []
        #             if "entityMentions" in ev.keys():
        #                 entity = [{"text": e["text"], "id": entity2id[e["text"]]} for e in ev["entityMentions"]]
        #             if "valueMentions" in ev.keys():
        #                 value = [{"text": e["text"], "id": entity2id[e["text"]]} for e in ev["valueMentions"]]
        #             evidences.append({"entity1Mentions": entity, "entity2Mentions": value})
        #
        #     stat_dict = {"humanReadable": statement["humanReadable"], "entity1text": statement["entity"]["name"],
        #                  "entity2text": statement["value"]["name"], "relation": statement["property"]["name"],
        #                  "confidence": statement["confidence"], "evidence": evidences}
        #     statements.append(stat_dict)

    else:
        print("Error of the nl_api annotation; this wiki abstract will be eliminated because of", annotation)
        return "", ""

    # sent = '_'.join(sent[a:b] for a, b in zip(entities_begin, entities_end))


if __name__ == '__main__':
    input_file = sys.argv[1]
    output_file = sys.argv[3]
    output_file_sentence_index = sys.argv[4]

    patterns = collect_patterns(sys.argv[2])

    with open(input_file, encoding="UTF-8") as f:
        data = json.load(f)
        for doc in data:
            curr_sentence_index = []
            if "may refer to" not in doc["text"]:
                doc["text"] = doc["text"][doc["text"].find("\n\n") + 1:]
                doc["annotatedSentences"] = main(doc, patterns)
                # sentence_index.append(curr_sentence_index)

    with open(output_file + ".json", 'w+', encoding="UTF-8") as out:
        json.dump(data, out)
        print("Annotated Wiki abstract are saved to", output_file)

    with open(output_file_sentence_index + ".json", 'w+', encoding="UTF-8") as out_sent_idx:
        json.dump(sentence_index, out_sent_idx)
        print("Sentences are saved to", output_file_sentence_index)

"""



"""
