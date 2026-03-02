#!/bin/bash

# A script to run the CI integration test workflows locally

set -ex

# check we are in the tests/integration directory
if [ ! -d "aviti" ]; then
    echo "Please run this script from the tests/integration directory of the repository."
    exit 1
fi

# download test data (reads and genome) if not already present
if [ ! -d "data" ]; then
    mkdir -p data
    wget -O - https://github.com/lauren-saunders-lab/sci-rocket-test-data/releases/latest/download/test-data.tgz | tar -xvzf - -C data
fi

# run each test workflow and its associated pytest tests
for test_dir in bcl aviti velocity; do
    # remove any old output, except cached resources (e.g. STAR index) to avoid rebuilding every run.
    if [ -d "$test_dir/output" ]; then
        find "$test_dir/output" -mindepth 1 -maxdepth 1 ! -name "resources" -exec rm -rf {} +
    fi

    snakemake --cores all --use-conda --configfile "$test_dir/config.yaml" -s ../../workflow/Snakefile -d "$test_dir"
    pytest "$test_dir" -vvv
done

echo "All integration tests completed successfully."
