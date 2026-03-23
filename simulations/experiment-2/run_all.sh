#!/bin/bash
set -e

echo "Running baseline tests..."
(cd ./baseline && ./run.sh)

echo "Running initial window tuning tests..."
(cd ./initial-window && ./run.sh)

echo "Done!"