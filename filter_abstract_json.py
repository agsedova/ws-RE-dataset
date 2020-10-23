"""
extract abstracts from wiki pages; save it to json with "id", "url", "title", "text" fields
"""

import glob
import sys
import os
import json
import timeit
import annotation


def main(root_dir):
    for dir, subdirs, files in os.walk(root_dir):
        for file in files:
            path_to_input_file = os.path.join(dir, file)

            print("Processing of file", path_to_input_file)

            if "wiki" in path_to_input_file:
                with open(path_to_input_file, 'r') as input_file:
                    start = timeit.default_timer()

                    file_length = sum(1 for _ in open(path_to_input_file))
                    wiki_pages, all_data = [], []
                    i = 1

                    for line in input_file:
                        print("File {}/{}".format(i, file_length))
                        page = json.loads(line)

                        if "may refer to" not in page["text"]:
                            page["text"] = page["text"][page["text"].find("\n\n") + 2:]

                            page.update(annotation.main(page))
                            all_data.append(page)
                        i += 1

                path_to_output_file = os.path.join(dir, "abstracts", file) + "_abstract.json5"
                os.makedirs(os.path.join(dir, "abstracts"), exist_ok=True)

                with open(path_to_output_file, 'w+', encoding="UTF-8") as output_file:
                    json.dump(all_data, output_file)

                    stop = timeit.default_timer()
                    print("Annotated Wiki abstract are saved to", path_to_output_file, "Time: ", stop - start)

            print("================================================")


if __name__ == '__main__':
    root_dir = sys.arg[1]
    main(root_dir)
