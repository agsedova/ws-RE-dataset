import scripts.nl_api
import spacy
import re
from scripts.commons import Entity


nlp = spacy.load("en_core_web_sm")
sentence_index = []


class EntityExtractor:
    def __init__(self, sentence, annotation):
        self.sentence = sentence
        self.annotation = annotation

    def extract_entities(self):
        """ Search entities in a sentence & annotate them with DiffBot and Spacy"""
        preprocessed_entities = []
        diffbot_sentence_entities = {}
        for raw_entity in self.annotation[0]["entities"]:
            curr_entities = []
            if 'mentions' in raw_entity.keys():
                mentions = [men for men in raw_entity["mentions"] if men["beginOffset"] < self.sentence.sentenceEnd
                            and men["endOffset"] > self.sentence.sentenceStart]
                if len(mentions) > 0:
                    for mention in mentions:
                        curr_entity = self.create_entity(mention, raw_entity)
                        diffbot_sentence_entities[curr_entity.entityInSentence] = curr_entity
                        if curr_entity.entityId not in preprocessed_entities:
                            self.sentence.entities.append(curr_entity)
                            preprocessed_entities.append(curr_entity.entityId)
                        else:
                            next(item for item in curr_entities if item["entityId"] == curr_entity.entityId.
                                 entityReferences.append(curr_entity.entityReferences))
        self.add_spacy_info()
        return self.sentence

    def create_entity(self, mention, raw_entity):
        """ Creates an object of class Entity from DiffBot entity"""
        entity_text = mention["text"]
        ent_begin = mention["beginOffset"]
        ent_end = mention["endOffset"]
        ent_offset = self.sentence.sentenceId + ":" + str(ent_begin) + ":" + str(ent_end)
        entity_uri = ", ".join(raw_entity["allUris"])
        # entity_types = [e["name"] for e in raw_entity["allTypes"]]
        ent_ref = [{"entityName": raw_entity['name'], "entityConfidence": mention["confidence"], "entityUri": entity_uri}]
        return Entity(ent_offset, entity_text, ent_begin, ent_end, "no_type", ent_ref)

    def add_spacy_info(self):
        """ Adds NER information got from SpaCy to Diffbot entities"""
        spacy_sentence_entities = self.spacy_ner()  # perform NER with spacy
        for entity in self.sentence.entities[:]:
            # check if entities from Diffbot were also detected by SpaCy; if yes, add their types to Diffbot annotations
            if entity.entityInSentence in spacy_sentence_entities.keys():
                entity.entityType = spacy_sentence_entities[entity.entityInSentence]["entityLabel"]
                del spacy_sentence_entities[entity.entityInSentence]
            else:
                # run SpaCy NER for this entity; if the same entity is detected, add type to it, else remove
                spacy_ent = nlp(entity.entityInSentence)
                inter_entities = [ent.label_ for ent in spacy_ent.ents if ent.text == entity.entityInSentence]
                if len(inter_entities) != 0:
                    entity.entityType = ", ".join(inter_entities)
                else:
                    self.sentence.entities.remove(entity)
            # if entity contains a whitespace, join it in a sentence with an underscore
            if " " in entity.entityInSentence:
                entity.entityInSentence = self.join_entities(entity.entityInSentence)

        # if there are entities detected by SpaCy but missed by DiffBot, add them to entities list of the sentence
        if len(spacy_sentence_entities) > 0:
            for entity, entity_info in spacy_sentence_entities.items():
                if " " in entity:
                    entity = self.join_entities(entity)
                self.sentence.entities.append(Entity(self.calculate_entity_offset(entity_info), entity,
                                                     entity_info["entityStart"], entity_info["entityEnd"],
                                                     entity_info["entityLabel"], {}))

    def spacy_ner(self):
        """ Performs SpaCy NER analysing of a sentence"""
        sentence_after_spacy = nlp(self.sentence.sentenceText)
        sentence_entities = {}
        for ent in sentence_after_spacy.ents:
            sentence_entities[ent.text] = {"entityId": 0, "entityInSentence": ent.text, "entityStart": ent.start_char,
                                           "entityEnd": ent.end_char, "entityLabel": ent.label_}
        return sentence_entities

    def calculate_entity_offset(self, entity):
        """ Get entity offset for a SpaCy entity"""
        return self.sentence.sentenceId + ":" + str(entity["entityStart"]) + ":" + str(entity["entityEnd"])

    def join_entities(self, entity):
        """ If an entity contains a whitespace, find it in a sentence and join with an underscore"""
        self.sentence.sentenceText = self.sentence.sentenceText[:self.sentence.sentenceText.find(entity)] + \
                                     self.sentence.sentenceText[self.sentence.sentenceText.find(entity)
                                                                :self.sentence.sentenceText.find(entity) + len(entity)]\
                                         .replace(" ", "_") + self.sentence.sentenceText[
                                                              self.sentence.sentenceText.find(entity) + len(entity):]
        return re.sub(" ", "_", entity)

