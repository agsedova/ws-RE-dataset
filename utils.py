import os
import json


def find_nth(string, substring, n):
    """ Find index of the nth element in the string"""
    return string.find(substring) if n == 1 else string.find(substring, find_nth(string, substring, n - 1) + 1)


def flatten(x):
    return [a for i in x for a in flatten(i)] if type(x) is list else [x]


def extract_abstract(page):
    """ takes an entire Wiki pages as input and returns its abstract"""
    return page[find_nth(page, "\n\n", 1)+2:find_nth(page, "\n\n", 2)+2]