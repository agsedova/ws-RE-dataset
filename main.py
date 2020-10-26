# import WikiExtractor
import process_wikidump_pages
from retrieve_patterns import PatternSearch
import sys

if __name__ == "__main__":
    # WikiExtractor.main()
    file_input, file_output = sys.argv[1], sys.argv[2]
    process_wikidump_pages.main(file_input)
    PatternSearch().retrieve_patterns()


