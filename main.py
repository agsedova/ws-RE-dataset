import scripts.WikiExtractor as WikiExtractor
from scripts.WikiDumpProcesser import WikiDumpProcesser
from scripts.PatternSearch import PatternSearch
import sys
import os

if __name__ == "__main__":
    # WikiExtractor.main()
    file_input, path_to_patterns, path_to_entity_types = sys.argv[1], sys.argv[2], sys.argv[3]
    WikiDumpProcesser(file_input).main()
    PatternSearch(os.path.join(file_input, "sentences.json"), path_to_patterns, path_to_entity_types).main()

