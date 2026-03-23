#!/bin/bash
set -e

echo "Running loss verification tests..."
(cd ./channel-characteristics/loss && ./run.sh)

echo "Running no-loss verification tests..."
(cd ./channel-characteristics/no-loss && ./run.sh)

echo "Running queue dynamics tests..."
(cd ./queue-dynamics && ./run.sh)

echo "Done!"