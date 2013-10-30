https://www.airbnb.com/rooms/1132551
https://www.airbnb.com/rooms/642263
https://www.airbnb.com/rooms/1403973


json.dump(
  json.load(open("/Users/zvm/Desktop/work/EN_docs_ISI.converted.json", "r")),
  open("/Users/zvm/Desktop/work/EN_docs_ISI.converted.2.json", "wb"),
  indent=8)

HUGIN_ROOT=$PWD/hugin
SEAR_ROOT=$PWD/sear
METAPHOR_ROOT=$PWD/metaphor
export PYTHONPATH=PYTHONPATH:$HUGIN_ROOT:$SEAR_ROOT:$METAPHOR_ROOT

INDEX_ROOT=/lfs1/vzaytsev/corpora2/ru/sentences_index
RUWAC_ROOT=/lfs1/vzaytsev/corpora2/ru/ruwac_index
OUT_FILE=/lfs1/vzaytsev/corpora2/ru/test.txt
QUERY=/lfs1/vzaytsev/software/metaphor-search/test_data/large/russian.json


python scripts/run_sentence_candidates.py -i $INDEX_ROOT -l russian -f json -s large -c $RUWAC_ROOT -q $QUERY -o $OUT_FILE
