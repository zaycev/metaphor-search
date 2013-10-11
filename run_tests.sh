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

# time python $SCRIPTS_ROOT/run_sentence_indexer.py -t 1 -i $TEST_INPUT_ROOT -o $TEST_OUTPUT_ROOT -s tiny
# time python $SCRIPTS_ROOT/run_sentence_indexer.py -t 1 -i $TEST_INPUT_ROOT -o $TEST_OUTPUT_ROOT -s medium
# time python $SCRIPTS_ROOT/run_sentence_indexer.py -t 1 -i $TEST_INPUT_ROOT -o $TEST_OUTPUT_ROOT -s large

# time python $SCRIPTS_ROOT/run_sentence_searcher.py -t 1 -i $TEST_INPUT_ROOT -o $TEST_OUTPUT_ROOT -s tiny -l 10000 -d 1
# time python $SCRIPTS_ROOT/run_sentence_searcher.py -t 1 -i $TEST_INPUT_ROOT -o $TEST_OUTPUT_ROOT -s medium -l 100000 -d 1
# time python $SCRIPTS_ROOT/run_sentence_searcher.py -t 1 -i $TEST_INPUT_ROOT -o $TEST_OUTPUT_ROOT -s large -l 1000000 -d 1

# time python $SCRIPTS_ROOT/run_sentence_frequencies.py -t 1 -i $TEST_OUTPUT_ROOT -s tiny
# time python $SCRIPTS_ROOT/run_sentence_frequencies.py -t 1 -i $TEST_OUTPUT_ROOT -s medium
# time python $SCRIPTS_ROOT/run_sentence_frequencies.py -t 1 -i $TEST_OUTPUT_ROOT -s large

# time python $SCRIPTS_ROOT/run_sentence_candidates.py -t 1 -i $TEST_OUTPUT_ROOT -o $TEST_OUTPUT_ROOT -l russian -f plain -s tiny
# time python $SCRIPTS_ROOT/run_sentence_candidates.py -t 1 -i $TEST_OUTPUT_ROOT -o $TEST_OUTPUT_ROOT -l russian -f plain -s medium
time python $SCRIPTS_ROOT/run_sentence_candidates.py -t 1 -i $TEST_OUTPUT_ROOT -o $TEST_OUTPUT_ROOT -l russian -f plain -s large