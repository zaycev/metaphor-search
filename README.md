## Quering metaphors

#### 1. Cd to the repository root:

```shell
cd /lfs1/vzaytsev/software/metaphor-search/
```

#### 2. Add `metaphor`'s packages to `PYTHONPATH` and set `NLTK` data path (if needed):

```shell
HUGIN_ROOT=$PWD/hugin
SEAR_ROOT=$PWD/sear
METAPHOR_ROOT=$PWD/metaphor

export PYTHONPATH=PYTHONPATH:$HUGIN_ROOT:$SEAR_ROOT:$METAPHOR_ROOT
export NLTK_DATA=/lfs1/vzaytsev/nltk

```

#### 3. Set searcher options:

```shell
# Specify language, choices: ru, es, en
LANG=en
SENTENCES_ROOT=/lfs1/vzaytsev/corpora2/$LANG/sentence_index
DOCUMENTS_ROOT=/lfs1/vzaytsev/corpora2/$LANG/document_index
# change this according to your query file:
QUERY=/lfs1/vzaytsev/corpora2/$LANG/queries/test_query.json
# set any location for found metaphors
OUT_DIR=/lfs1/vzaytsev/corpora2/$LANG/found/
```

#### 4. Run searcher:

```shell
python scripts/run_sentence_candidates.py \
		-i $SENTENCES_ROOT \
		-c $DOCUMENTS_ROOT \
		-l $LANG \
		-f json \
		-q $QUERY \
		-o $OUT_DIR \
		-x 0 \
		-e ".metaphors" \
		-p 1
```

#### 5. Options:

 1. `-i`, `--input` 			LF sentences index root location.
 2. `-c`, `--context_input`	Context index root location.
 3. `-l`, `--language`			Data language: `ru`, `es`, or `en`.
 4. `-f`, `--format`			Output format: `json` or `plain`.
 5. `-o`, `--output`			Location of the output directory.
 6. `-x`, `--output_lf`			Put logic form of found metaphor to output file: `0` or `1`.
 7. `-q`, `--query`				Metaphor search query file.
 8. `-e`, `--extension`			Extension that will be addet to the output files. Default is `.metaphors.json`.
 9. `-p`, `--use_pos`			Use parts of speech. Postfixes such as `-\w+` (`-n`, `-vb`, etc) if present, will be recognised as additional part of speech constraint in query. Default is `0`.

#### Query Example

```json
{
    "annotation": {
        "label": "poverty",
        "language": "english",
        "corpus": "gigaword",

        "source_frame": "building",
        "source_concept_subdomain": "",

        "target_frame": "wealth",
        "target_concept_domain": "economy",
        "target_concept_subdomain": "wealth"
    },
    "query": {
        "max_path_lenght": 100,
        "targets": [
            "money-n"
        ],
        "sources": [
            "water-n"
        ]
    }
}
```
