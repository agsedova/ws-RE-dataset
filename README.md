# DiffBot_Corpus

## [main.py](https://github.com/agsedova/DiffBot_Corpus/blob/master/main.py)

The main script for execution the wiki abstract annotations.

## [WikiDumpProcesser.py](https://github.com/agsedova/DiffBot_Corpus/blob/master/WikiDumpProcesser.py)
Parse the Wikipedia pages saved as wiki dump. 

## [parse_abstract.py](https://github.com/agsedova/DiffBot_Corpus/blob/master/parse_abstract.py)
Parcing the wikipedia abstract. Class AbstractParser creates the objects of class Sentence with all information regarding the sentence in dataset: offset, indices, url etc + list of entities found by DiffBot and Spacy in this sentence with all corresponding information(class EntityExtractor).

## [extract_entities.py](https://github.com/agsedova/DiffBot_Corpus/blob/master/extract_entities.py)
Extract the entities from the sentences and add them to Sentence.Entities. Class EntityExtractor analyses the wiki abstracts with Diffbot and Spacy, compares the received entities and create the objects of class Entities with all entities information.

## [PatternSearch.py](https://github.com/agsedova/DiffBot_Corpus/blob/master/PatternSearch.py)
Look for sentences given pattern. Creates and uses Elasticsearch index for that.  

## [WikiDataCollector.py](https://github.com/agsedova/DiffBot_Corpus/blob/master/WikiDataCollector.py)
(deprecated) another way to collect wikipedia data: using Wikipedia package for python.


