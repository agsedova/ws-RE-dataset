# import WikiExtractor
import WikiDumpProcesser
from retrieve_patterns import PatternSearch
import sys

if __name__ == "__main__":
    file_input, file_output = sys.argv[1], sys.argv[2]
    WikiDumpProcesser.main(file_input)
    PatternSearch().retrieve_patterns()

