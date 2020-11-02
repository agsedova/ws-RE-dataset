import os
import json


def find_nth(string, substring, n):
    """ Find index of the nth element in the string"""
    return string.find(substring) if n == 1 else string.find(substring, find_nth(string, substring, n - 1) + 1)


def save_to_json(dir, filename, new_enty):
    """ Create a json file and save data in it or add new entries to already existing json file"""
    path_to_output_file = dir + filename
    if os.path.isfile(path_to_output_file):
        with open(path_to_output_file, 'r+', encoding="UTF-8") as output_file:
            data = json.load(output_file)
            updated_data = {**data, **new_enty}
            output_file.seek(0)
            json.dump(updated_data, output_file)
            # json.dumps(updated_data, output_file)
            output_file.truncate()
            print("New entries are added to the existing {} file".format(filename))
    else:
        with open(path_to_output_file, 'w+', encoding="UTF-8") as output_file:
            json.dump(new_enty, output_file)
            print("New entries are saved to the newly created {} file".format(filename))
    # with open(path_to_output_file, 'w+', encoding="UTF-8") as output_file:
    #     json.dump(new_abstract, output_file)
    #     print("New .json file is created, abstracts_test are saved")


def flatten(x):
    return [a for i in x for a in flatten(i)] if type(x) is list else [x]


def extract_abstract(page):
    """ takes an entire Wiki pages as input and returns its abstract"""
    return page[find_nth(page, "\n\n", 1)+2:find_nth(page, "\n\n", 2)+2]