## Quering metaphors

#### 1. Cd to the repository root:

```
cd /lfs1/vzaytsev/software/metaphor-search/
```

#### 2. Add `metaphor`'s packages to `PYTHONPATH` and set `NLTK` data path (if needed):

```
HUGIN_ROOT=$PWD/hugin
SEAR_ROOT=$PWD/sear
METAPHOR_ROOT=$PWD/metaphor

export PYTHONPATH=PYTHONPATH:$HUGIN_ROOT:$SEAR_ROOT:$METAPHOR_ROOT
export NLTK_DATA=/lfs1/vzaytsev/nltk

```

#### 3. Set searcher options:

```
# Specify language, choices: ru, es, en
LANG=ru
SENTENCES_ROOT=/lfs1/vzaytsev/corpora2/$LANG/sentence_index
DOCUMENTS_ROOT=/lfs1/vzaytsev/corpora2/$LANG/document_index
# change this according to your query file:
QUERY=/lfs1/vzaytsev/corpora2/$LANG/queries/test_query.json
# set any location for found metaphors
OUT_FILE=/lfs1/vzaytsev/corpora2/$LANG/found_metaphors.json
```

#### 4. Run searcher:

```
python scripts/run_sentence_candidates.py \
		-i $SENTENCES_ROOT \
		-c $DOCUMENTS_ROOT \
		-l $LANG \
		-f json \
		-q $QUERY \
		-o $OUT_FILE \
		-g 0
```

#### 5. Options:

 1. `-i`, `--input` 			LF sentences index root location.
 2. `-c`, `--context_input`	Context index root location.
 3. `-l`, `--language`			Data language: `ru`, `es`, or `en`.
 4. `-f`, `--format`			Output format: `json` or `plain`.
 5. `-o`, `--output`			Location of the output file.
 6. `-g`, `--output_lf`			Put logic for of found metaphor to output file: `0` or `1`.


##### 6. Relax and make herbal tea.
