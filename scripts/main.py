import argparse
from scripts.DataPreprocessing import WikiExtractor
from scripts.DataPreprocessing.wikidump_processer import WikiDumpProcessor
from scripts.pattern_search import PatternSearch
import sys
import os


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog=os.path.basename(sys.argv[0]))
    parser.add_argument("--wiki_extractor_input", help="XML wiki dump file")
    parser.add_argument("--wiki_extractor_output", help="")
    parser.add_argument("--path_to_patterns", help="")
    parser.add_argument("--path_to_output_files", help="")
    parser.add_argument("--path_to_retrieved_sentences", help="")
    args = parser.parse_args()

    # wiki_dump, file_input, path_to_patterns, path_to_output_files = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    # WikiExtractor.main()
    # WikiDumpProcessor(args.wiki_extractor_output, args.path_to_output_files).process_wiki_pages()
    PatternSearch(args.path_to_output_files, args.path_to_patterns, args.path_to_retrieved_sentences).retrieve_patterns()


