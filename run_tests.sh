HUGIN_ROOT=$PWD/hugin
SEAR_ROOT=$PWD/sear
METAPHOR_ROOT=$PWD/metaphor

echo exported:
echo $HUGIN_ROOT
echo $SEAR_ROOT
echo $METAPHOR_ROOT

export PYTHONPATH=PYTHONPATH:$HUGIN_ROOT:$SEAR_ROOT:$METAPHOR_ROOT

TEST_INPUT_ROOT=$PWD/
TEST_OUTPUT_ROOT=$PWD/
SCRIPTS_ROOT=$PWD/scripts

# Russian
# time python $SCRIPTS_ROOT/run_sentence_indexer.py       -t 1 -i $TEST_INPUT_ROOT -o $TEST_OUTPUT_ROOT -l ru -s tiny
# time python $SCRIPTS_ROOT/run_sentence_indexer.py       -t 1 -i $TEST_INPUT_ROOT -o $TEST_OUTPUT_ROOT -l ru -s medium
# time python $SCRIPTS_ROOT/run_sentence_indexer.py       -t 1 -i $TEST_INPUT_ROOT -o $TEST_OUTPUT_ROOT -l ru -s large

# time python $SCRIPTS_ROOT/run_document_indexer.py       -t 1 -i $TEST_INPUT_ROOT -o $TEST_OUTPUT_ROOT -l ru -s tiny    -c ruwac
# time python $SCRIPTS_ROOT/run_document_indexer.py       -t 1 -i $TEST_INPUT_ROOT -o $TEST_OUTPUT_ROOT -l ru -s medium  -c ruwac
# time python $SCRIPTS_ROOT/run_document_indexer.py       -t 1 -i $TEST_INPUT_ROOT -o $TEST_OUTPUT_ROOT -l ru -s large   -c ruwac

time python $SCRIPTS_ROOT/run_sentence_candidates.py    -t 1 -i $TEST_OUTPUT_ROOT -o $TEST_OUTPUT_ROOT -l ru -s tiny    -f json
time python $SCRIPTS_ROOT/run_sentence_candidates.py    -t 1 -i $TEST_OUTPUT_ROOT -o $TEST_OUTPUT_ROOT -l ru -s medium  -f json
time python $SCRIPTS_ROOT/run_sentence_candidates.py    -t 1 -i $TEST_OUTPUT_ROOT -o $TEST_OUTPUT_ROOT -l ru -s large   -f json

# # Spanish
# time python $SCRIPTS_ROOT/run_sentence_indexer.py       -t 1 -i $TEST_INPUT_ROOT -o $TEST_OUTPUT_ROOT -l es -s tiny
# time python $SCRIPTS_ROOT/run_sentence_indexer.py       -t 1 -i $TEST_INPUT_ROOT -o $TEST_OUTPUT_ROOT -l es -s medium
# time python $SCRIPTS_ROOT/run_sentence_indexer.py       -t 1 -i $TEST_INPUT_ROOT -o $TEST_OUTPUT_ROOT -l es -s large

# time python $SCRIPTS_ROOT/run_document_indexer.py       -t 1 -i $TEST_INPUT_ROOT -o $TEST_OUTPUT_ROOT -l es -s tiny    -c gigaword
# time python $SCRIPTS_ROOT/run_document_indexer.py       -t 1 -i $TEST_INPUT_ROOT -o $TEST_OUTPUT_ROOT -l es -s medium  -c gigaword
# time python $SCRIPTS_ROOT/run_document_indexer.py       -t 1 -i $TEST_INPUT_ROOT -o $TEST_OUTPUT_ROOT -l es -s large   -c gigaword

# time python $SCRIPTS_ROOT/run_sentence_candidates.py    -t 1 -i $TEST_OUTPUT_ROOT -o $TEST_OUTPUT_ROOT -l es -s tiny    -f json
# time python $SCRIPTS_ROOT/run_sentence_candidates.py    -t 1 -i $TEST_OUTPUT_ROOT -o $TEST_OUTPUT_ROOT -l es -s medium  -f json
# time python $SCRIPTS_ROOT/run_sentence_candidates.py    -t 1 -i $TEST_OUTPUT_ROOT -o $TEST_OUTPUT_ROOT -l es -s large   -f json

# # English
# time python $SCRIPTS_ROOT/run_sentence_indexer.py       -t 1 -i $TEST_INPUT_ROOT -o $TEST_OUTPUT_ROOT -l en -s tiny
# time python $SCRIPTS_ROOT/run_sentence_indexer.py       -t 1 -i $TEST_INPUT_ROOT -o $TEST_OUTPUT_ROOT -l en -s medium
# time python $SCRIPTS_ROOT/run_sentence_indexer.py       -t 1 -i $TEST_INPUT_ROOT -o $TEST_OUTPUT_ROOT -l en -s large

# time python $SCRIPTS_ROOT/run_document_indexer.py       -t 1 -i $TEST_INPUT_ROOT -o $TEST_OUTPUT_ROOT -l en -s tiny    -c gigaword
# time python $SCRIPTS_ROOT/run_document_indexer.py       -t 1 -i $TEST_INPUT_ROOT -o $TEST_OUTPUT_ROOT -l en -s medium  -c gigaword
# time python $SCRIPTS_ROOT/run_document_indexer.py       -t 1 -i $TEST_INPUT_ROOT -o $TEST_OUTPUT_ROOT -l en -s large   -c gigaword

# time python $SCRIPTS_ROOT/run_sentence_candidates.py     -p 1 -x 1 -t 1 -i $TEST_OUTPUT_ROOT -o $TEST_OUTPUT_ROOT -l en -s tiny
# time python $SCRIPTS_ROOT/run_sentence_candidates.py    -p 1 -x 1 -t 1 -i $TEST_OUTPUT_ROOT -o $TEST_OUTPUT_ROOT -l en -s medium
# time python $SCRIPTS_ROOT/run_sentence_candidates.py    -p 1 -x 1 -t 1 -i $TEST_OUTPUT_ROOT -o $TEST_OUTPUT_ROOT -l en -s large
