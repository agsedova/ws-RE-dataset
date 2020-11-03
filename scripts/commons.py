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


class Entity:
    def __init__(self, entityId, entityInSentence, entityStart, entityEnd, entityType, entityReferences):
        self.entityId = entityId
        self.entityInSentence = entityInSentence
        self.entityStart = entityStart
        self.entityEnd = entityEnd
        self.entityType = entityType
        self.entityReferences = entityReferences