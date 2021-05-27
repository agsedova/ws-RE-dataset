import argparse
from scripts.preprocessing.wiki_dump_spacy_processor import wiki_dump_spacy_processor
from scripts.weak_annotation.pattern_search import PatternSearch
import sys
import os
import logging


logger = logging.getLogger(__name__)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog=os.path.basename(sys.argv[0]))
    parser.add_argument("--wiki_dump", help="")
    parser.add_argument("--wiki_dump_extracted", help="")
    parser.add_argument("--wiki_dump_spacy", default=None, help="")
    parser.add_argument("--path_to_retrieved_sentences", help="")
    parser.add_argument("--path_to_patterns", help="")
    args = parser.parse_args()

    # ==================
    # Step 0: processing of XML wiki dump file with preprocessing/WikiExtractor module
    # WikiExtractor.main(args.wiki_dump)

    # The output of WikiExtractor are the processed files saved to the wiki_extractor_output directory.
    # The wiki_extractor_output directory contains sub-folds AA, AB, ... with files containing wiki articles in each.
    # Each article is stored as a dictionary with keys "id", "url", "title" and "text".

    # ==================
    # Step 1: processing of wiki pages saved from WikiDump file with SpaCy.
    # Output: saved to the args.path_to_output_files directory; the structure of the original files is preserved.

    if args.wiki_dump_spacy is None:
        logger.info("No file with SpaCy annotation was provided. Annotation will be done now.")
        wiki_dump_spacy_processor(
            root_dir=args.wiki_dump_extracted        # directory with wiki articles from wiki dump
        )

    # ==================
    # Step 2: search for patterns in SpaCy output.

    pattern_searcher = PatternSearch(
        path_to_data=args.wiki_dump_spacy,     # directory where the SpaCy output is stored
        path_to_patterns=args.path_to_patterns,     # file that contains the patterns that are to be found
        path_to_output=args.path_to_retrieved_sentences     # directory where the output will be stored
    ).retrieve_patterns()


# --wiki_extractor_input
# data/enwiki-20201101-pages-articles-multistream.xml.bz2
# --wiki_extractor_output
# data/text
# --path_to_patterns
# data/patterns.txt
# --path_to_output_files
# data/output/wikidump/spacy_1
# --path_to_retrieved_sentences
# data/output/test