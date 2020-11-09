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

'''
# diffbot relations and correcponding entities
EXPECTED_TYPES_PER_PROPERTY = {
  '1':  ('ORG','ORG'),      #SUBSIDIARY_OF
  '2':  ('ORG','PERSON'),   #FOUNDED_BY
  '3':  ('PERSON','ORG'),   #EMPLOYEE_OR_MEMBER_OF
  '4':  ('ORG','PERSON'),   #CEO
  '5':  ('ORG','DATE'),     #DATE_FOUNDED
  '6':  ('ORG','GPE'),      #HEADQUARTERS
  '9':  ('PERSON','ORG'),   #EDUCATED_AT
  '10': ('PERSON','NORP'),  #NATIONALITY - NB! there is no close relation in our list
  '11': ('PERSON','GPE'),   #PLACE_OF_RESIDENCE
  '12': ('PERSON','GPE'),   #PLACE_OF_BIRTH
  '14': ('PERSON','DATE'),  #DATE_OF_DEATH
  '15': ('PERSON','DATE'),  #DATE_OF_BIRTH
  '25': ('PERSON','PERSON'),#SPOUSE
  '34': ('PERSON','PERSON'),#CHILD_OF
  '45': ('PERSON','ORG'),   #POLITICAL_AFFILIATION
}
'''
'''
Spacy entities:
PERSON	People, including fictional.
NORP	Nationalities or religious or political groups.
FAC	Buildings, airports, highways, bridges, etc.
ORG	Companies, agencies, institutions, etc.
GPE	Countries, cities, states.
LOC	Non-GPE locations, mountain ranges, bodies of water.
PRODUCT	Objects, vehicles, foods, etc. (Not services.)
EVENT	Named hurricanes, battles, wars, sports events, etc.
WORK_OF_ART	Titles of books, songs, etc.
LAW	Named documents made into laws.
LANGUAGE	Any named language.
DATE	Absolute or relative dates or periods.
TIME	Times smaller than a day.
PERCENT	Percentage, including ”%“.
MONEY	Monetary values, including unit.
QUANTITY	Measurements, as of weight or distance.
ORDINAL	“first”, “second”, etc.
CARDINAL	Numerals that do not fall under another type.
'''

# all relations that could be extracted with patterns
RELATIONS = {'org:date_founded', 'per:cities_of_residence', 'org:political_religious_affiliation', 'org:website',
             'per:religion', 'per:country_of_death', 'per:title', 'per:member_of', 'per:spouse', 'per:siblings',
             'org:alternate_names', 'per:stateorprovince_of_death', 'per:charges', 'per:city_of_birth',
             'org:stateorprovince_of_headquarters', 'org:number_of_employees_members', 'per:stateorprovince_of_birth',
             'per:employee_or_member_of', 'per:employee_of', 'per:other_family', 'org:parents', 'per:origin',
             'org:subsidiaries', 'org:country_of_headquarters', 'org:member_of', 'per:stateorprovinces_of_residence',
             'per:cause_of_death', 'per:countries_of_residence', 'per:date_of_death', 'org:members',
             'per:city_of_death', 'per:alternate_names', 'org:founded_by', 'per:parents', 'org:top_members_employees',
             'per:date_of_birth', 'org:date_dissolved', 'per:country_of_birth', 'per:schools_attended',
             'org:city_of_headquarters', 'org:dissolved', 'per:age', 'per:statesorprovinces_of_residence',
             'per:children', 'org:shareholders', 'org:founded'}

# if we use all relations that could be exctracted with patterns + add diffbot types constraints where correspond
#       + create own types constrants
# TYPES_PER_RELATION = {'org:subsidiaries': ('ORG', 'ORG'),
#                       'org:founded_by': ('ORG', 'PERSON'),
#                       'org:founded': ('ORG', 'DATE'),
#                       'org:date_founded': ('ORG', 'DATE'),
#                       'org:stateorprovince_of_headquarters': ('ORG', 'GPE'),
#                       'org:country_of_headquarters': ('ORG', 'GPE'),
#                       'org:city_of_headquarters': ('ORG', 'GPE'),
#                       'org:top_members_employees': ('ORG', 'PERSON'),
#                       'org:number_of_employees_members': ('ORG', 'CARDINAL'),
#                       'org:parents': ('ORG', 'ORG'),
#                       'org:political_religious_affiliation': ('PERSON', 'ORG'),
#                       'org:date_dissolved': ('ORG', 'DATA'),
#                       'org:dissolved': ('ORG', 'DATA'),
#                       'org:shareholders': ('ORG', 'PERSON'),
#                       'org:alternate_names': ('ORG', 'ORG'),
#
#                       'per:employee_or_member_of': ('PERSON', 'ORG'),
#                       'per:employee_of': ('PERSON', 'ORG'),
#                       'per:schools_attended': ('PERSON', 'ORG'),
#                       'per:stateorprovinces_of_residence': ('PERSON', 'GPE'),
#                       'per:statesorprovinces_of_residence': ('PERSON', 'GPE'),
#                       'per:countries_of_residence': ('PERSON', 'GPE'),
#                       'per:cities_of_residence': ('PERSON', 'GPE'),
#                       'per:origin': ('PERSON', 'GPE'),
#                       'per:stateorprovince_of_birth': ('PERSON', 'GPE'),
#                       'per:country_of_birth': ('PERSON', 'GPE'),
#                       'per:city_of_birth': ('PERSON', 'GPE'),
#                       'per:stateorprovince_of_death': ('PERSON', 'GPE'),
#                       'per:country_of_death': ('PERSON', 'GPE'),
#                       'per:city_of_death': ('PERSON', 'GPE'),
#                       'per:date_of_death': ('PERSON', 'DATE'),
#                       'per:date_of_birth': ('PERSON', 'DATE'),
#                       'per:spouse': ('PERSON', 'PERSON'),
#                       'per:children': ('PERSON', 'PERSON'),
#                       'per:parents': ('PERSON', 'PERSON'),
#                       'per:siblings': ('PERSON', 'PERSON'),
#                       'per:other_family': ('PERSON', 'PERSON'),
#                       'per:age': ('PERSON', 'CARDINAL'),
#                       'per:religion': ('PERSON', 'NORP'),
#                       'per:alternate_names': ('PERSON', 'PERSON'),
#
#                       'per:member_of': ('_', '_'),
#                       'org:member_of': ('_', '_'),
#                       'org:members': ('_', '_'),
#                       'org:website': ('_', '_'),
#                       'per:title': ('_', '_'),
#                       'per:charges': ('_', '_'),
#                       'per:cause_of_death': ('_', '_')}

TYPES_PER_RELATION = {'org:subsidiaries': ('ORG', 'ORG'), 'org:founded_by': ('ORG', 'PERSON'),
                      'per:employee_or_member_of': ('PERSON', 'ORG'), 'org:top_members_employees': ('ORG', 'PERSON'),
                      'org:founded': ('ORG', 'DATE'), 'org:country_of_headquarters': ('ORG', 'GPE'),
                      'org:city_of_headquarters': ('ORG', 'GPE'), 'per:schools_attended': ('PERSON', 'ORG'),
                      'per:stateorprovinces_of_residence': ('PERSON', 'GPE'),
                      'per:statesorprovinces_of_residence': ('PERSON', 'GPE'),
                      'per:countries_of_residence': ('PERSON', 'GPE'),
                      'per:cities_of_residence': ('PERSON', 'GPE'),
                      'per:stateorprovince_of_birth': ('PERSON', 'GPE'),
                      'per:country_of_birth': ('PERSON', 'GPE'),
                      'per:city_of_birth': ('PERSON', 'GPE'),
                      'per:date_of_death': ('PERSON', 'DATE'),
                      'per:date_of_birth': ('PERSON', 'DATE'),
                      'per:spouse': ('PERSON', 'PERSON'),
                      'per:children': ('PERSON', 'PERSON'),
                      'per:political_religious_affiliation': ('PERSON', 'ORG')}

# todo: write 'per:political_religious_affiliation' patterns - done
# todo: write 'per:nationality' patterns

