import pytest
import spacy
import en_core_web_sm

from scripts.weak_annotation.pattern_search.PatternSearch import PatternSearch

nlp = en_core_web_sm.load()


@pytest.fixture(scope='session')
def get_spacy_pattern_search_data():
    sent = "Turner Sports. Turner Sports (TS) is the division of Turner Broadcasting System (a subsidiary of AT&T) " \
           "responsible for sports broadcasts on Turner channels including TBS, TNT, TruTV, and CNN en Español (for " \
           "occasional Spanish language simulcasts), and for operating the digital media outlets NCAA.com, NBA.com, " \
           "PGATOUR.com and PGA.com. Turner Sports also operates NBA TV on behalf of the National Basketball " \
           "Association."
    sent_2 = "Stanford alumnus Bill has shown a great success in neuroscience. Great!"
    ann_sent = nlp(sent).to_json()
    ann_sent_2 = nlp(sent_2).to_json()

    ann_sent["doc_id"] = "1507"
    ann_sent_2["doc_id"] = "1234"

    # page_annotation = [{**{"doc_id": "1507"}, **ann_sent}]
    # page_annotation_2 = [{**{"doc_id": "1234"}, **ann_sent_2}]
    ps = PatternSearch("../data/output/spacy", "../data/patterns.txt", "../data/output")
    return [
        [
            ps,
            ann_sent,
            {'1': 0},
            {"doc_key": "1507",
             "sentences": [["Turner", "Sports", "."],
                           ["Turner", "Sports", "(", "TS", ")", "is", "the", "division", "of",
                            "Turner", "Broadcasting", "System", "(", "a", "subsidiary", "of", "AT&T",
                            ")", "responsible", "for", "sports", "broadcasts", "on", "Turner",
                            "channels", "including", "TBS", ",", "TNT", ",", "TruTV", ",", "and",
                            "CNN", "en", "Español", "(", "for", "occasional", "Spanish", "language",
                            "simulcasts", ")", ",", "and", "for", "operating", "the", "digital",
                            "media", "outlets", "NCAA.com", ",", "NBA.com", ",", "PGATOUR.com",
                            "and", "PGA.com", "."],
                           ["Turner", "Sports", "also", "operates", "NBA", "TV", "on", "behalf",
                            "of", "the", "National", "Basketball", "Association", "."]],
             "relations": [[], [[12, 14, 19, 19, "SUBSIDIARY_OF"]], []],
             "tokensToOriginalIndices": [[[0, 6], [7, 13], [13, 14]],
                                         [[15, 21], [22, 28], [29, 30], [30, 32], [32, 33], [34, 36], [37, 40],
                                          [41, 49], [50, 52], [53, 59], [60, 72], [73, 79], [80, 81], [81, 82],
                                          [83, 93], [94, 96], [97, 101], [101, 102], [103, 114], [115, 118], [119, 125],
                                          [126, 136], [137, 139], [140, 146], [147, 155], [156, 165], [166, 169],
                                          [169, 170], [171, 174], [174, 175], [176, 181], [181, 182], [183, 186],
                                          [187, 190], [191, 193], [194, 201], [202, 203], [203, 206], [207, 217],
                                          [218, 225], [226, 234], [235, 245], [245, 246], [246, 247], [248, 251],
                                          [252, 255], [256, 265], [266, 269], [270, 277], [278, 283], [284, 291],
                                          [292, 300], [300, 301], [302, 309], [309, 310], [311, 322], [323, 326],
                                          [327, 334], [334, 335]],
                                         [[336, 342], [343, 349], [350, 354], [355, 363], [364, 367], [368, 370],
                                          [371, 373], [374, 380], [381, 383], [384, 387], [388, 396], [397, 407],
                                          [408, 419], [419, 420]]],
             "annotatedPredicates": [[], ["SUBSIDIARY_OF"], []],
             'patterns': [[], [[12, 14, 19, 19, 249, 'SUBSIDIARY_OF']], []]}
        ],
        [
            ps,
            ann_sent_2,
            {'9': 0, '15': 0},
            {"doc_key": "1234", "sentences": [
                ["Stanford", "alumnus", "Bill", "has", "shown", "a", "great", "success", "in", "neuroscience", "."],
                ["Great", "!"]],
             "relations": [[[0, 0, 2, 2, "EDUCATED_AT"]], []],
             "tokensToOriginalIndices": [
                 [[0, 8], [9, 16], [17, 21], [22, 25], [26, 31], [32, 33], [34, 39], [40, 47], [48, 50], [51, 63],
                  [63, 64]], [[65, 70], [70, 71]]],
             "annotatedPredicates": [["EDUCATED_AT"], []],
             'patterns': [[[0, 0, 2, 2, 105, "EDUCATED_AT"]], []]}
        ]
    ]


@pytest.fixture(scope='session')
def get_multiple_patterns_sent_test_data():
    sent = "Mr. Smith was born in 2001, and Anna studied at Stanford."
    ann_sent = nlp(sent).to_json()
    ann_sent["doc_id"] = "1111"
    # page_annotation = [{**{"doc_id": "1111"}, **ann_sent}]
    ps = PatternSearch("../data/output/spacy", "../data/patterns.txt", "../data/output")
    return [
        [
            ps,
            ann_sent,
            {'9': 0, '15': 0},
            {"doc_key": "1111",
             "sentences": [["Mr.", "Smith", "was", "born", "in", "2001", ",", "and", "Anna", "studied", "at",
                            "Stanford", "."]],
             "relations": [[[1, 1, 5, 5, 'DATE_OF_BIRTH'], [8, 8, 11, 11, "EDUCATED_AT"]]],
             "tokensToOriginalIndices": [[[0, 3],
                                          [4, 9],
                                          [10, 13],
                                          [14, 18],
                                          [19, 21],
                                          [22, 26],
                                          [26, 27],
                                          [28, 31],
                                          [32, 36],
                                          [37, 44],
                                          [45, 47],
                                          [48, 56],
                                          [56, 57]]],
             "annotatedPredicates": [["DATE_OF_BIRTH", "EDUCATED_AT"]],
             'patterns': [[[1, 1, 5, 5, 4, 'DATE_OF_BIRTH'], [8, 8, 11, 11, 88, "EDUCATED_AT"]]]}
        ]
    ]


def test_spacy_pattern_search_data(get_spacy_pattern_search_data):
    for data in get_spacy_pattern_search_data:
        qqq = PatternSearch.find_pattern_matches(data[0], data[1], data[2])
        print(qqq)
        assert PatternSearch.find_pattern_matches(data[0], data[1], data[2]) == data[3]


def test_multiple_pattern_search_data(get_multiple_patterns_sent_test_data):
    for data in get_multiple_patterns_sent_test_data:
        assert PatternSearch.find_pattern_matches(data[0], data[1], data[2]) == data[3]
