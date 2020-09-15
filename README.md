# Wikipedia-Search-Engine

## Contents

``` indexer.py ```
``` search.py ```

## Index Creation

#### How to Run
```
python3 indexer.py /inverted_index/ wikiStats.txt
```

There is only one file ```indexer.py``` which creates the index. 
All the index files will be created in the ```inverted_index/``` folder and stats like number of total tokens and unique tokens are stored in ```wikiStats.txt```

#### List of Index Files

  - **vocab.txt** - contains the vocabulary along with frequency
  - **offset.txt** - contains the offset each word in the vocabulary
  - **title.txt** - contains the mapping of document id (manually assigned) and title name
  - **titleOffset.txt** - contains the offset for each title 
  - **fileNumbers.txt** - contains the number of files 
  - **b\*/c\*/i\*/l\*/r\*/t\*.txt** - index files which contains occurence of each token in respective fields
  - **offset_b\*/c\*/i\*/l\*/r\*/t\*.txt** - contains the offset for each of the individual index files of each field 

## Search

#### How to Run
```sh
python3 search.py queries.txt
```

There is only one file ```search.py``` which handles the search. For this the index folder (inverted_index/) must be in the same folder as search.py
```queries.txt``` contain queries on separate lines and the output is written to ```queries_op.txt``` file.
