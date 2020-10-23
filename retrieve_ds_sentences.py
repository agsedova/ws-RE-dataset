from elasticsearch import Elasticsearch
from nltk.tokenize import word_tokenize
import re
import argparse, sys

# Solr/Lucene special characters: + - ! ( ) { } [ ] ^ " ~ * ? : \
# There are also operators && and ||, but we're just going to escape
# the individual ampersand and pipe chars.
# Also, we're not going to escape backslashes!
# http://lucene.apache.org/java/2_9_1/queryparsersyntax.html#Escaping+Special+Characters
ESCAPE_CHARS_RE = re.compile(r'(?<!\\)(?P<char>[&|+\-!(){}[\]^"~*?:])')


def escape(value):
    r"""Escape un-escaped special characters and return escaped value.

    >>> escape(r'foo+') == r'foo\+'
    True
    >>> escape(r'foo\+') == r'foo\+'
    True
    >>> escape(r'foo\\+') == r'foo\\+'
    True
    """
    return ESCAPE_CHARS_RE.sub(r'\\\g<char>', value)


def results(es, es_index, query_str):
    """Return results for query_str in es_index"""
    # TODO
    return es.search(index=es_index, body={"query": {
        "query_string" : {
            "default_field" : "text",
            "query" : query_str
        }
    }}, size=10)


def hit_title(hit):
    """Return title of hit"""
    # TODO
    return hit["_source"]["title"]


def hit_text(hit):
    """Return text of hit"""
    # TODO
    return hit["_source"]["text"]


def context(needle, haystack, window=50, highlight_leftright=("", "")):
    start = haystack.lower().find(needle.lower())
    if -1 == start:
        return ""
    end = start + len(needle)
    left = haystack[start-window:start]
    middle = highlight_leftright[0] + haystack[start: end] + highlight_leftright[1]
    right = haystack[end:end+window]
    return left + middle + right


def longest_match(haystack, needles):
    longest = 0
    best_needle = None
    haystack = " " + haystack + " "
    for needle in needles:
        search_needle = " " + needle.lower() + " "
        idx = haystack.lower().find(search_needle)
        if idx >=0 and len(needle) > longest:
            best_needle = haystack[idx+1:idx+1+len(needle)]
            longest = len(needle)
    return best_needle


def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--pairs', required = True)
#    parser.add_argument('-o', '--out', required = True)
    opts = parser.parse_args(args)

    es = Elasticsearch()
    with open(opts.pairs, 'r') as pairs_filename:
        for line in pairs_filename:
            parts = line.strip().split("\t|\t")
            entity1_aliases_concat = parts[0]
            entity2_aliases_concat = parts[1]
            e1_aliases = entity1_aliases_concat.split("\t")
            e2_aliases = entity2_aliases_concat.split("\t")
            e1_query = '("' + '" OR "'.join([escape(e) for e in e1_aliases]) + '")'
            e2_query = '("' + '" OR "'.join([escape(e) for e in e2_aliases]) + '")'
            query_str = e1_query + " AND " + e2_query
            res = results(es, 'wiki-sentences', query_str)
            for hit in res['hits']['hits']:
                #title = hit_title(hit)
                text = ' '.join(word_tokenize(hit_text(hit)))
                best_query = longest_match(text, [' '.join(word_tokenize(e)) for e in e1_aliases])
                best_answer = longest_match(text, [' '.join(word_tokenize(e)) for e in e2_aliases])
                if best_query and best_answer and not best_answer in best_query:
                    print(text + "\t" + best_query + "\t" + best_answer)


if __name__ == "__main__":
    main(sys.argv[1:])
