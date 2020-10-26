# import WikiExtractor
import process_wikidump_pages
from retrieve_patterns import PatternSearch
import sys

if __name__ == "__main__":
    # WikiExtractor.main()
    file_input, file_output = sys.argv[1], sys.argv[2]
    process_wikidump_pages.main(file_input)
    PatternSearch().retrieve_patterns()


'''
def main(path_to_abstract):
    with open(path_to_abstract + "_tst_annotated.json", 'w+', encoding="UTF-8") as output_file:
        annotated_data = []
        with open(path_to_abstract, 'r') as input_file:
            wiki_pages = json.loads(input_file.read())
            for page in wiki_pages:
                if "may refer to" not in page["text"]:
                    # page["text"] = page["text"][page["text"].find("\n\n") + 2:]

                    annotated_page = parse_abstract.main(page)
                    page["annotatedSentences"] = annotated_page
                    annotated_data.append(page)
        json.dump(annotated_data, output_file)


if __name__ == '__main__':
    path_to_abstract = sys.argv[1]
    main(path_to_abstract)
'''

