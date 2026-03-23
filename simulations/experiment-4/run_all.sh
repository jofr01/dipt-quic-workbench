#!/bin/bash
set -e

echo "Running lossless tests..."
(cd ./no-loss && ./run.sh)

echo "Running lossy tests..."
(cd ./loss && ./run.sh)

echo "Done!"