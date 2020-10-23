import glob
import sys
import os


def main(root_dir):
    for filename in glob.iglob(root_dir + '**/**/wiki_*', recursive=True):
        paths = filename.split("/")
        path_to_abstracts = os.path.join(paths[0], paths[1], "abstracts")
        os.makedirs(path_to_abstracts, exist_ok=True)
        with open(path_to_abstracts + "/" + paths[2] + "_abstract", 'w+', encoding="UTF-8") as output_file:
            with open(filename, 'r') as input_file:
                for line in input_file:
                    if line.startswith("<doc "):
                        # new page starts
                        output_file.write("\n")
                        empty_lines = 0
                        output_file.write(line)
                    elif line == "\n":
                        empty_lines += 1
                    else:
                        if empty_lines == 0:
                            continue
                        if empty_lines == 1:
                            output_file.write(line)


if __name__ == '__main__':
    root_dir = sys.arg[1]
    main(root_dir)
