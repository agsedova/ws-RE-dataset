import wikipedia
import json
import sys
import utils


class WikiDataCollector:
    """
    Collects Wikipedia pages with wikipedia pack and save them to dictionary
    {"id": page_id, "title": page_name, "url": page_url, "abstract": page_abstract}
    """

    def __init__(self, num_of_pages, output_path):
        self.num_of_pages = int(num_of_pages)
        self.output_path = output_path

    def collect_wiki_data(self):
        ret = []
        if int(self.num_of_pages) > 0:
            page_names = set(utils.flatten([wikipedia.random(page) for page in range(self.num_of_pages)]))
            i = 0
            print("Total number of pages to be collected:", len(page_names))
            for page_name in page_names:
                print("Processing of page", str(i))
                page_info = self.get_title_abstract_url_id(page_name)
                if page_info:
                    ret.append(page_info)
                i += 1
            with open(self.output_path + '/wiki_data_' + str(len(page_names)) + '.json5', 'w') as outfile:
                json.dump(ret, outfile)
                # for r in ret:
                #     json.dump(str(r), outfile)
        else:
            print("Number of Wiki pages to be extracted is 0; please increase the number at least to 1")

    def get_title_abstract_url_id(self, page_name):
        try:
            return {"id": wikipedia.page(page_name).pageid, "title": page_name,
                    "url": wikipedia.page(page_name).url, "abstract": wikipedia.page(page_name).summary}
        except wikipedia.exceptions.DisambiguationError:
            print("DisambiguationError; page is skipped")
            pass
        except wikipedia.exceptions.PageError:
            print("PageError; page is skipped")
            pass


if __name__ == '__main__':
    WikiDataCollector(sys.argv[1], sys.argv[2]).collect_wiki_data()



