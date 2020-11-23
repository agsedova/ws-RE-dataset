RELATION_TO_TYPES = {'org:subsidiaries': ('ORG', 'ORG'),
                     'org:founded_by': ('ORG', 'PERSON'),
                     'per:employee_or_member_of': ('PERSON', 'ORG'),
                     'per:member_of': ('PERSON', 'ORG'),  # EMPLOYEE_OR_MEMBER_OF
                     'per:employee_of': ('PERSON', 'ORG'),  # EMPLOYEE_OR_MEMBER_OF
                     'org:top_members_employees': ('ORG', 'PERSON'),
                     'org:founded': ('ORG', 'DATE'),
                     'org:country_of_headquarters': ('ORG', 'GPE'),
                     'org:city_of_headquarters': ('ORG', 'GPE'),
                     'per:schools_attended': ('PERSON', 'ORG'),
                     'per:nationality': ('PERSON', 'NORP'),
                     'per:statesorprovinces_of_residence': ('PERSON', 'GPE'),
                     'per:countries_of_residence': ('PERSON', 'GPE'),
                     'per:stateorprovince_of_birth': ('PERSON', 'GPE'),
                     'per:country_of_birth': ('PERSON', 'GPE'),
                     'per:city_of_birth': ('PERSON', 'GPE'),
                     'per:date_of_death': ('PERSON', 'DATE'),
                     'per:date_of_birth': ('PERSON', 'DATE'),
                     'per:spouse': ('PERSON', 'PERSON'),
                     'per:children': ('PERSON', 'PERSON'),
                     'per:political_religious_affiliation': ('PERSON', 'ORG')}


PROPERTY_NAMES = {'org:subsidiaries': '1',
                  'org:founded_by': '2',
                  'per:employee_or_member_of': '3',     # EMPLOYEE_OR_MEMBER_OF
                  'per:member_of': '3',         # EMPLOYEE_OR_MEMBER_OF
                  'per:employee_of': '3',         # EMPLOYEE_OR_MEMBER_OF
                  'org:top_members_employees': '4',
                  'org:founded': '5',
                  'org:country_of_headquarters': '6',  # 'HEADQUARTERS',
                  'org:city_of_headquarters': '6',       # 'HEADQUARTERS',
                  'per:schools_attended': '9',      # 'EDUCATED_AT',
                  'per:nationality': '10',          # 'NATIONALITY',
                  'per:statesorprovinces_of_residence': '11',       # 'PLACE_OF_RESIDENCE',
                  'per:countries_of_residence': '11',        # 'PLACE_OF_RESIDENCE',
                  'per:stateorprovince_of_birth': '12',  # 'PLACE_OF_BIRTH'
                  'per:country_of_birth': '12',     # 'PLACE_OF_BIRTH'
                  'per:city_of_birth': '12',    # 'PLACE_OF_BIRTH'
                  'per:date_of_death': '14',         # 'DATE_OF_DEATH',
                  'per:date_of_birth': '15',        # 'DATE_OF_BIRTH',
                  'per:spouse': '25',           # 'SPOUSE'
                  'per:children': '34',      # 'CHILD_OF'
                  'per:political_religious_affiliation': '45'}       # 'POLITICAL_AFFILIATION'

DYGIE_RELATIONS = {'1':  "SUBSIDIARY_OF", '2':  "FOUNDED_BY", '3':  "EMPLOYEE_OR_MEMBER_OF", '4':  "CEO",
                   '5':  "DATE_FOUNDED", '6':  "HEADQUARTERS", '9':  "EDUCATED_AT", '10': "NATIONALITY",
                   '11': "PLACE_OF_RESIDENCE", '12': "PLACE_OF_BIRTH", '14': "DATE_OF_DEATH", '15':"DATE_OF_BIRTH",
                   '25': "SPOUSE", '34': "CHILD_OF", '45': "POLITICAL_AFFILIATION"}

