import pytest
from scripts.PatternSearch import PatternSearch
from scripts.commons import DYGIE_RELATIONS

stat = {}
for rel_id, rel_name in DYGIE_RELATIONS.items():
    stat[rel_id] = 0


@pytest.fixture(scope='session')
def get_simple_patterns_sent_test_data():
    ps = PatternSearch("../data/output/spacy", "../data/patterns.txt", "../data/output")
    return [
                [
                    "Mr. Smith, born in 2001",
                    {"start": 0, "end": 9, "start_sent": 0, "end_sent": 9, "label": 'PERSON'},
                    {"start": 19, "end": 23, "start_sent": 19, "end_sent": 23, "label": 'DATE'},
                    ('PERSON', 'DATE'),
                    "15",
                    ps.relation_to_patterns["15"], ps, {"15": []},
                    stat,
                    {'15': [[{"start": 0, "end": 9, "start_sent": 0, "end_sent": 9, "label": 'PERSON'},
                            {"start": 19, "end": 23, "start_sent": 19, "end_sent": 23, "label": 'DATE'},
                            ps.patterns_to_ids["$ARG1 , born in $ARG2"]]]}
                ],
                [
                    "Wikipedia (born 2001)",
                    {"start": 0, "end": 9, "start_sent": 0, "end_sent": 9, "label": 'PERSON'},
                    {"start": 16, "end": 20, "start_sent": 16, "end_sent": 20, "label": 'DATE'},
                    ('PERSON', 'DATE'),
                    "15",
                    ps.relation_to_patterns["15"], ps, {"15": []},
                    stat,
                    {'15': [[{"start": 0, "end": 9, "start_sent": 0, "end_sent": 9, "label": 'PERSON'},
                             {"start": 16, "end": 20, "start_sent": 16, "end_sent": 20, "label": 'DATE'},
                             ps.patterns_to_ids["$ARG1 ( born $ARG2 )"]]]}
                ]
            ]


@pytest.fixture(scope='session')
def get_star_patterns_sent_test_data():
    ps = PatternSearch("../data/output/spacy", "../data/patterns.txt", "../data/output")
    return [
                [
                    "AAA's a perfect subsidiary BBB",
                    {"start": 0, "end": 3, "start_sent": 0, "end_sent": 3, "label": 'ORG'},
                    {"start": 27, "end": 30, "start_sent": 27, "end_sent": 30, "label": 'ORG'},
                    ('ORG', 'ORG'),
                    "1",
                    ps.relation_to_patterns["1"], ps, {"1": []},
                    stat,
                    {'1': [[{"start": 0, "end": 3, "start_sent": 0, "end_sent": 3, "label": 'ORG'},
                            {"start": 27, "end": 30, "start_sent": 27, "end_sent": 30, "label": 'ORG'},
                            ps.patterns_to_ids["$ARG1 's * subsidiary $ARG2"]]]}
                ]
            ]

@pytest.fixture(scope='session')
def get_arg_switch_patterns_sent_test_data():
    ps = PatternSearch("../data/output/spacy", "../data/patterns.txt", "../data/output")
    return [
        [
            "Stanford alumnus Bill",
            {"start": 0, "end": 8, "start_sent": 0, "end_sent": 8, "label": 'ORG'},
            {"start": 17, "end": 21, "start_sent": 17, "end_sent": 21, "label": 'PERSON'},
            ('PERSON', 'ORG'),
            "9", ps.relation_to_patterns["9"], ps, {"9": []}, stat,
            {'9': [[{"start": 0, "end": 8, "start_sent": 0, "end_sent": 8, "label": 'ORG'},
                    {"start": 17, "end": 21, "start_sent": 17, "end_sent": 21, "label": 'PERSON'},
                    ps.patterns_to_ids["$ARG2 alumnus $ARG1"]]]}
        ],
        [
            "Stanford alumnus Bill",
            {"start": 17, "end": 21, "start_sent": 17, "end_sent": 21, "label": 'PERSON'},
            {"start": 0, "end": 8, "start_sent": 0, "end_sent": 8, "label": 'ORG'},
            ('PERSON', 'ORG'),
            "9", ps.relation_to_patterns["9"], ps, {"9": []}, stat,
            {'9': [[{"start": 17, "end": 21, "start_sent": 17, "end_sent": 21, "label": 'PERSON'},
                    {"start": 0, "end": 8, "start_sent": 0, "end_sent": 8, "label": 'ORG'},
                    ps.patterns_to_ids["$ARG2 alumnus $ARG1"]]]}
        ],
        [
            "Bill studied at Stanford",
            {"start": 16, "end": 24, "start_sent": 16, "end_sent": 24, "label": 'ORG'},
            {"start": 0, "end": 4, "start_sent": 0, "end_sent": 4, "label": 'PERSON'},
            ('PERSON', 'ORG'),
            "9", ps.relation_to_patterns["9"], ps, {"9": []}, stat,
            {'9': [[{"start": 16, "end": 24, "start_sent": 16, "end_sent": 24, "label": 'ORG'},
                    {"start": 0, "end": 4, "start_sent": 0, "end_sent": 4, "label": 'PERSON'},
                    ps.patterns_to_ids["$ARG1 studied at $ARG2"]]]}
        ]
    ]


@pytest.fixture(scope='session')
def get_self_patterns_sent_test_data():
    ps = PatternSearch("../data/output/spacy", "../data/patterns.txt", "../data/output")
    return [
                [
                    "Mrs. Smith, Mr. Smith's wife",
                    {"start": 0, "end": 10, "start_sent": 0, "end_sent": 10, "label": 'PERSON'},
                    {"start": 11, "end": 21, "start_sent": 12, "end_sent": 21, "label": 'PERSON'},
                    ('PERSON', 'PERSON'),
                    "25", ps.relation_to_patterns["25"], ps, {"25": []}, stat,
                    {'25': [[{"start": 0, "end": 10, "start_sent": 0, "end_sent": 10, "label": 'PERSON'},
                            {"start": 11, "end": 21, "start_sent": 12, "end_sent": 21, "label": 'PERSON'},
                            ps.patterns_to_ids["$ARG0 , $ARG0 's wife"]]]}
                ]
            ]


@pytest.fixture(scope='session')
def get_art_patterns_sent_test_data():
    ps = PatternSearch("../data/output/spacy", "../data/patterns.txt", "../data/output")
    return [
                [
                    "a Mrs. Smith, the Mr. Smith's wife",
                    {"start": 2, "end": 12, "start_sent": 2, "end_sent": 12, "label": 'PERSON'},
                    {"start": 18, "end": 27, "start_sent": 18, "end_sent": 27, "label": 'PERSON'},
                    ('PERSON', 'PERSON'),
                    "25", ps.relation_to_patterns["25"], ps, {"25": []}, stat,
                    {'25': [[{"start": 2, "end": 12, "start_sent": 2, "end_sent": 12, "label": 'PERSON'},
                            {"start": 18, "end": 27, "start_sent": 18, "end_sent": 27, "label": 'PERSON'},
                            ps.patterns_to_ids["$ARG0 , $ARG0 's wife"]]]}
                ]
            ]

def test_arg_switch_patterns_sent(get_arg_switch_patterns_sent_test_data):
    for data in get_arg_switch_patterns_sent_test_data:
        assert PatternSearch.perform_search_in_sentence(data[6], data[0], data[1], data[2], data[3], data[4], data[5],
                                                        data[7], data[8]) == data[9]


def test_simple_pattern_sent(get_simple_patterns_sent_test_data):
    for data in get_simple_patterns_sent_test_data:
        assert PatternSearch.perform_search_in_sentence(data[6], data[0], data[1], data[2], data[3], data[4], data[5],
                                                        data[7], data[8]) == data[9]


def test_star_patterns_sent(get_star_patterns_sent_test_data):
    for data in get_star_patterns_sent_test_data:
        assert PatternSearch.perform_search_in_sentence(data[6], data[0], data[1], data[2], data[3], data[4], data[5],
                                                        data[7], data[8]) == data[9]


def test_self_patterns_sent(get_self_patterns_sent_test_data):
    for data in get_self_patterns_sent_test_data:
        assert PatternSearch.perform_search_in_sentence(data[6], data[0], data[1], data[2], data[3], data[4], data[5],
                                                        data[7], data[8]) == data[9]


def test_art_patterns(get_art_patterns_sent_test_data):
    for data in get_art_patterns_sent_test_data:
        assert PatternSearch.perform_search_in_sentence(data[6], data[0], data[1], data[2], data[3], data[4], data[5],
                                                        data[7], data[8]) == data[9]