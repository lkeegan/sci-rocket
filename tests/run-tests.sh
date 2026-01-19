#!/bin/bash

# A script to run all CI test workflows locally
# Note that the order matters, as the star index generated in the first test is reused in subsequent tests,
# and the "two_runs" tests assume that the corresponding "one_run" test has already been run.

set -ex

# check we are in the tests directory
if [ ! -d "test_fastq_from_aviti_one_run" ]; then
    echo "Please run this script from the tests directory of the repository."
    exit 1
fi

# remove any previous test workflow outputs
rm -rf test_*/output

# download test data (reads and genome) if not already present
if [ ! -d "data" ]; then
    mkdir -p data
    wget -O - https://github.com/lauren-saunders-lab/sci-rocket-test-data/releases/download/2026.01.08/test-data.tgz | tar -xvzf - -C data
fi

# run each test workflow and its associated pytest tests
for test_dir in test_bcl_one_run test_bcl_two_runs test_fastq_from_bcl_one_run test_fastq_from_bcl_two_runs test_fastq_from_aviti_one_run test_fastq_from_aviti_two_runs; do
    snakemake --cores all --use-conda --configfile $test_dir/config.yaml -s ../workflow/Snakefile -d $test_dir
    pytest $test_dir -vvv
done

echo "All tests completed successfully."
