import nl_api
import spacy
import re

nlp = spacy.load("en_core_web_sm")
sentence_index = []


class Entity:
    def __init__(self, entityId, entityInSentence, entityStart, entityEnd, entityType, entityReferences):
        self.entityId = entityId
        self.entityInSentence = entityInSentence
        self.entityStart = entityStart
        self.entityEnd = entityEnd
        self.entityType = entityType
        self.entityReferences = entityReferences


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

'''
logs:
/Users/asedova/PycharmProjects/DiffBot_Corpus/virtualenv_diffbot_corpus/bin/python /Users/asedova/PycharmProjects/DiffBot_Corpus/process_wikidump_pages.py data_samples/abstracts_test
Processing of file data_samples/abstracts_test/AB/wiki_00
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy couldn't analise Diffbot entity, entity is deleted
spacy info added
spacy info added
Page 1/3 is annotated
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy couldn't analise Diffbot entity, entity is deleted
spacy info added
spacy info added
spacy info added
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy couldn't analise Diffbot entity, entity is deleted
spacy info added
spacy info added
SpaCy has additionally analised Diffbot entity, type information is added
SpaCy has additionally analised Diffbot entity, type information is added
SpaCy couldn't analise Diffbot entity, entity is deleted
spacy info added
spacy info added
Page 2/3 is annotated
SpaCy couldn't analise Diffbot entity, entity is deleted
spacy info added
spacy info added
spacy info added
SpaCy couldn't analise Diffbot entity, entity is deleted
spacy info added
spacy info added
Page 3/3 is annotated
New entries are saved to the newly created /abstracts_test.json file
New entries are saved to the newly created /sentences.json file
================================================
Processing of file data_samples/abstracts_test/AB/wiki_01
Page 1/3 is skipped because it is a 'may refer to' page
SpaCy couldn't analise Diffbot entity, entity is deleted
spacy info added
Page 2/3 is annotated
spacy info added
spacy info added
spacy info added
Page 3/3 is annotated
New entries are added to the existing /abstracts_test.json file
New entries are added to the existing /sentences.json file
================================================
Processing of file data_samples/abstracts_test/AA/wiki_00
Page 1/10 is annotated
spacy info added
spacy info added
spacy info added
SpaCy couldn't analise Diffbot entity, entity is deleted
spacy info added
spacy info added
Page 2/10 is annotated
SpaCy has additionally analised Diffbot entity, type information is added
spacy info added
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy has additionally analised Diffbot entity, type information is added
spacy info added
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy has additionally analised Diffbot entity, type information is added
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy couldn't analise Diffbot entity, entity is deleted
Page 3/10 is annotated
Page 4/10 is annotated
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy couldn't analise Diffbot entity, entity is deleted
Page 5/10 is annotated
spacy info added
spacy info added
spacy info added
Page 6/10 is annotated
spacy info added
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy couldn't analise Diffbot entity, entity is deleted
spacy info added
spacy info added
SpaCy couldn't analise Diffbot entity, entity is deleted
spacy info added
SpaCy couldn't analise Diffbot entity, entity is deleted
Page 7/10 is annotated
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy couldn't analise Diffbot entity, entity is deleted
spacy info added
SpaCy couldn't analise Diffbot entity, entity is deleted
Page 8/10 is annotated
SpaCy couldn't analise Diffbot entity, entity is deleted
spacy info added
spacy info added
Page 9/10 is annotated
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy has additionally analised Diffbot entity, type information is added
spacy info added
spacy info added
spacy info added
Page 10/10 is annotated
New entries are added to the existing /abstracts_test.json file
New entries are added to the existing /sentences.json file
================================================
Processing of file data_samples/abstracts_test/AA/wiki_01
spacy info added
spacy info added
SpaCy couldn't analise Diffbot entity, entity is deleted
spacy info added
SpaCy couldn't analise Diffbot entity, entity is deleted
Page 1/19 is annotated
SpaCy has additionally analised Diffbot entity, type information is added
spacy info added
SpaCy couldn't analise Diffbot entity, entity is deleted
spacy info added
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy has additionally analised Diffbot entity, type information is added
SpaCy couldn't analise Diffbot entity, entity is deleted
spacy info added
spacy info added
SpaCy has additionally analised Diffbot entity, type information is added
spacy info added
Page 2/19 is annotated
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy has additionally analised Diffbot entity, type information is added
spacy info added
spacy info added
SpaCy has additionally analised Diffbot entity, type information is added
spacy info added
spacy info added
spacy info added
spacy info added
spacy info added
Page 3/19 is annotated
Page 4/19 is skipped because it is a 'may refer to' page
SpaCy couldn't analise Diffbot entity, entity is deleted
spacy info added
spacy info added
spacy info added
spacy info added
spacy info added
spacy info added
spacy info added
spacy info added
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy has additionally analised Diffbot entity, type information is added
spacy info added
Page 5/19 is annotated
spacy info added
spacy info added
spacy info added
spacy info added
spacy info added
spacy info added
spacy info added
spacy info added
spacy info added
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy couldn't analise Diffbot entity, entity is deleted
spacy info added
SpaCy couldn't analise Diffbot entity, entity is deleted
spacy info added
spacy info added
spacy info added
spacy info added
spacy info added
spacy info added
SpaCy couldn't analise Diffbot entity, entity is deleted
spacy info added
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy couldn't analise Diffbot entity, entity is deleted
Page 6/19 is annotated
SpaCy couldn't analise Diffbot entity, entity is deleted
spacy info added
spacy info added
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy couldn't analise Diffbot entity, entity is deleted
spacy info added
Page 7/19 is annotated
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy couldn't analise Diffbot entity, entity is deleted
spacy info added
spacy info added
SpaCy couldn't analise Diffbot entity, entity is deleted
spacy info added
spacy info added
SpaCy couldn't analise Diffbot entity, entity is deleted
spacy info added
Page 8/19 is annotated
spacy info added
spacy info added
spacy info added
spacy info added
SpaCy couldn't analise Diffbot entity, entity is deleted
Page 9/19 is annotated
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy couldn't analise Diffbot entity, entity is deleted
spacy info added
SpaCy couldn't analise Diffbot entity, entity is deleted
spacy info added
SpaCy has additionally analised Diffbot entity, type information is added
SpaCy has additionally analised Diffbot entity, type information is added
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy has additionally analised Diffbot entity, type information is added
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy couldn't analise Diffbot entity, entity is deleted
Page 10/19 is annotated
spacy info added
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy couldn't analise Diffbot entity, entity is deleted
spacy info added
Page 11/19 is annotated
spacy info added
spacy info added
spacy info added
SpaCy couldn't analise Diffbot entity, entity is deleted
spacy info added
spacy info added
Page 12/19 is annotated
spacy info added
spacy info added
Page 13/19 is annotated
SpaCy couldn't analise Diffbot entity, entity is deleted
spacy info added
spacy info added
spacy info added
Page 14/19 is annotated
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy has additionally analised Diffbot entity, type information is added
SpaCy couldn't analise Diffbot entity, entity is deleted
spacy info added
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy has additionally analised Diffbot entity, type information is added
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy couldn't analise Diffbot entity, entity is deleted
spacy info added
spacy info added
spacy info added
spacy info added
spacy info added
spacy info added
spacy info added
spacy info added
spacy info added
spacy info added
spacy info added
spacy info added
spacy info added
spacy info added
spacy info added
spacy info added
spacy info added
Page 15/19 is annotated
SpaCy couldn't analise Diffbot entity, entity is deleted
SpaCy couldn't analise Diffbot entity, entity is deleted
spacy info added
spacy info added
SpaCy couldn't analise Diffbot entity, entity is deleted
spacy info added
Page 16/19 is annotated
spacy info added
spacy info added
SpaCy has additionally analised Diffbot entity, type information is added
SpaCy couldn't analise Diffbot entity, entity is deleted
spacy info added
spacy info added
spacy info added
spacy info added
spacy info added
Page 17/19 is annotated
spacy info added
SpaCy couldn't analise Diffbot entity, entity is deleted
Page 18/19 is annotated
spacy info added
SpaCy couldn't analise Diffbot entity, entity is deleted
spacy info added
spacy info added
Page 19/19 is annotated
New entries are added to the existing /abstracts_test.json file
New entries are added to the existing /sentences.json file
================================================

Process finished with exit code 0
'''