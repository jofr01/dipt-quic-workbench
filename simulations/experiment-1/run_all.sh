#!/bin/bash
set -e

echo "Running idle timeout tests..."
(cd ./idle-timeout && ./run.sh)

echo "Running initial rtt tests..."
(cd ./initial-rtt && ./run.sh)

echo "Running flow control tests..."
(cd ./flow-control && ./run.sh)

echo "Running baseline tests..."
(cd ./baseline && ./run.sh)

echo "Done!"