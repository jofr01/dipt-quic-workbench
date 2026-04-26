#!/bin/bash
set -e

echo "Executing all experiments and validation tests. This may take a while..."

echo "Running validation and verification tests..."
(cd ./verification-validation && ./run_all.sh)

echo "Running experiment 1 tests..."
(cd ./experiment-1 && ./run_all.sh)

echo "Running experiment 2 tests..."
(cd ./experiment-2 && ./run_all.sh)

echo "Running experiment 3 tests..."
(cd ./experiment-3 && ./run.sh)

echo "Running experiment 4 tests..."
(cd ./experiment-4 && ./run_all.sh)

echo "Running experiment 5 tests..."
(cd ./experiment-5 && ./run.sh)

# add further experiments

echo "Execution completed!"