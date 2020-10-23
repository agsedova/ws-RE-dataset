import annotation
import json
import sys


def main(path_to_abstract):
    with open(path_to_abstract + "_tst_annotated.json", 'w+', encoding="UTF-8") as output_file:
        annotated_data = []
        with open(path_to_abstract, 'r') as input_file:
            wiki_pages = json.loads(input_file.read())
            for page in wiki_pages:
                if "may refer to" not in page["text"]:
                    # page["text"] = page["text"][page["text"].find("\n\n") + 2:]

                    annotated_page = annotation.main(page)
                    page["annotatedSentences"] = annotated_page
                    annotated_data.append(page)
        json.dump(annotated_data, output_file)


if __name__ == '__main__':
    path_to_abstract = sys.argv[1]
    main(path_to_abstract)

