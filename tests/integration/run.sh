#!/bin/bash

# Run integration workflow tests locally (Snakemake + pytest + Playwright UI tests).

set -euo pipefail

# check we are in the tests/integration directory
if [ ! -d "aviti" ]; then
    echo "Please run this script from the tests/integration directory of the repository."
    exit 1
fi

# check all required commands are available
for cmd in snakemake pytest pnpm wget conda; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "Missing required command: $cmd"
        exit 1
    fi
done

# install Node test dependencies if not already present
pnpm install --frozen-lockfile
pnpm exec playwright install chromium

# download test data (reads and genome) if not already present
if [ ! -d "data" ]; then
    mkdir -p data
    wget -O - https://github.com/lauren-saunders-lab/sci-rocket-test-data/releases/latest/download/test-data.tgz | tar -xvzf - -C data
fi

# run each test workflow and its associated pytest and UI tests
for test_dir in bcl aviti velocity; do

    # remove any old output, except cached resources (e.g. STAR index) to avoid re-indexing for every run.
    if [ -d "$test_dir/output" ]; then
        find "$test_dir/output" -mindepth 1 -maxdepth 1 ! -name "resources" -exec rm -rf {} +
    fi

    # run the workflow
    snakemake --cores all --use-conda --configfile "$test_dir/config.yaml" -s ../../workflow/Snakefile -d "$test_dir"

    # run the python tests
    pytest "$test_dir" -vvv

    # run the UI tests
    rm -rf test-results playwright-report
    pnpm exec playwright test "$test_dir"

done

echo "All integration workflow, pytest, and Playwright tests completed successfully."
