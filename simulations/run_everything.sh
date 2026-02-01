#!/bin/bash
set -e

echo "Executing all experiments and validation tests. This may take a while..."

echo "Running validation and verification tests..."
(cd ./verification-validation && ./run_all.sh)

echo "Running experiment 1 tests..."
(cd ./experiment-1 && ./run_all.sh)

# add further experiments

echo "Execution completed!"