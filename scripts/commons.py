RELATION_TO_TYPES = {'org:subsidiaries': ('ORG', 'ORG'),
                     'org:founded_by': ('ORG', 'PERSON'),
                     'per:employee_or_member_of': ('PERSON', 'ORG'),
                     'org:top_members_employees': ('ORG', 'PERSON'),
                     'org:founded': ('ORG', 'DATE'),
                     'org:country_of_headquarters': ('ORG', 'GPE'),     # todo
                     'org:city_of_headquarters': ('ORG', 'GPE'),        # todo
                     'per:schools_attended': ('PERSON', 'ORG'),
                     'per:statesorprovinces_of_residence': ('PERSON', 'GPE'),   # todo: should we unite?
                     'per:countries_of_residence': ('PERSON', 'GPE'),           # todo: should we unite?
                     'per:stateorprovince_of_birth': ('PERSON', 'GPE'),     # todo
                     'per:country_of_birth': ('PERSON', 'GPE'),     # todo
                     'per:city_of_birth': ('PERSON', 'GPE'),    # todo
                     'per:date_of_death': ('PERSON', 'DATE'),
                     'per:date_of_birth': ('PERSON', 'DATE'),
                     'per:spouse': ('PERSON', 'PERSON'),
                     'per:children': ('PERSON', 'PERSON'),
                     'per:political_religious_affiliation': ('PERSON', 'ORG')}

# todo: add nationality relation patterns ('PERSON','NORP')

# todo - to clarify: 'Ludwig Purtscheller (October 6, 1849 – March 3, 1900) was an Austrian mountaineer and teacher.'
#  : spacy parse it as 'Ludwig Purtscheller $ARG1 \\( $ARG2\\)  was an Austrian mountaineer and teacher.', what doesn't
#  fall into patterns

