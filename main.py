from scripts.WikiDumpProcesser import WikiDumpProcesser
from scripts.PatternSearch import PatternSearch
import sys
import os

if __name__ == "__main__":
    # WikiExtractor.main()
    file_input, path_to_patterns, path_to_output_files = sys.argv[1], sys.argv[2], sys.argv[3]
    WikiDumpProcesser(file_input, path_to_output_files).process_wiki_pages()
    print("Processing of WikiDump is now over")
    print("===========================================================================================")
    PatternSearch(path_to_output_files, path_to_patterns, path_to_output_files).search_patterns()


