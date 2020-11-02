# coding=<UTF-8>

import nl_api
import spacy
from extract_entities import EntityExtractor

nlp = spacy.load("en_core_web_sm")
sentence_index = []

# todo: substitute "(" with "( " etc
# todo: check mistakes with substituting the entities with _! some of the final sentences are wrong --> retrieved.json


class Sentence:
    def __init__(self, sentenceId, sentenceText, sentenceStart, sentenceEnd, entities):
        self.sentenceId = sentenceId
        self.sentenceText = sentenceText
        self.sentenceStart = sentenceStart
        self.sentenceEnd = sentenceEnd
        self.entities = entities

    def as_dict(self):  # old ann_sent
        return {"sentenceId": self.sentenceId, "sentenceText": self.sentenceText, "sentenceStart": self.sentenceStart,
                "sentenceEnd": self.sentenceEnd, "entities": [ent.__dict__ for ent in self.entities]}


class AbstractParser:
    """ Sentence.Parser.parse(WikiAbstract) --> List(Sentence object)"""
    def __init__(self, data):
        self.page_offset = data["id"]
        self.url = data["url"]
        self.title = data["title"]
        self.text = data["text"]
        self.annotated_sentences = []

    def parse(self):
        annotation = nl_api.main(self.text)
        if type(annotation) is list and len(annotation) == 1 and "entities" in annotation[0].keys():
            sentences = [sent.string.strip() for sent in nlp(self.text).sents if sent.string.strip() is not ""]
            for sent in sentences:
                sent_idx_begin, sent_idx_end, sent_offset = self.calculate_sentence_offset(sent)
                # create sentence object
                sentence_object = Sentence(sent_offset, sent, sent_idx_begin, sent_idx_end, [])
                # get entity information
                sentence_object = EntityExtractor(sentence_object, annotation).extract_entities()
                self.annotated_sentences.append(sentence_object)
            return self.annotated_sentences
        else:
            print("Error of the nl_api annotation; this wiki abstract will be eliminated")
            return None

    def calculate_sentence_offset(self, sent):
        idx_begin = self.text.find(sent)
        idx_end = idx_begin + len(sent)
        offset = self.page_offset + ":" + str(idx_begin) + ":" + str(idx_end)
        return idx_begin, idx_end, offset
