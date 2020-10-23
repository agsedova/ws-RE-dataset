import wikipedia
import json
import sys


def main(num_of_pages):

    ret = []
    num_of_pages = int(num_of_pages)

    if num_of_pages > 0:
        page_names = set(flatten([wikipedia.random(page) for page in range(num_of_pages)]))
        i = 0
        print("Total number of pages to be collected:", len(page_names))
        for page_name in page_names:
            print("Processing of page", str(i))
            ret.append(get_title_abstract_url_id(page_name))
            i += 1

        with open('wiki_data_' + str(len(page_names)) + '.json5', 'w') as outfile:
            json.dump(ret, outfile)

    else:
        print("Number of Wiki pages to be exctracted is 0; please increase the number at least to 1")


def get_title_abstract_url_id(page_name):
    try:
        return {"id": wikipedia.page(page_name).pageid, "title": page_name,
                "url": wikipedia.page(page_name).url, "abstract": wikipedia.page(page_name).summary}
    except wikipedia.exceptions.DisambiguationError:
        print("DisambiguationError; page is skipped")
        pass
    except wikipedia.exceptions.PageError:
        print("PageError; page is skipped")
        pass


def flatten(x):
    return [a for i in x for a in flatten(i)] if type(x) is list else [x]


if __name__ == '__main__':
    num_of_pages = sys.argv[1]
    main(num_of_pages)




