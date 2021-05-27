def extract_abstract(page: str) -> str:
    """
    The function gets an entire Wiki pages and extract its abstract.
    :param page: text of the wiki page
    :return: wiki page abstract
    """
    return page[:find_nth(page, "\n\n", 1)] + ". " + page[find_nth(page, "\n\n", 1) + 1:find_nth(page, "\n\n", 2)] \
        .replace(u'\xa0', u' ').replace(u'\u00ad', u'-').replace(u'\u2013', u'-').replace(u'\n', u'')


def find_nth(string: str, substring: str, n: int) -> int:
    """ Find index of the nth element in the string"""
    return string.find(substring) if n == 1 else string.find(substring, find_nth(string, substring, n - 1) + 1)