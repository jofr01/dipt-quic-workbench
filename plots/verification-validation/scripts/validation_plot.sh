#!/bin/bash
set -e

# --- Configuration ---
PCAP_NS3_DIR="../logs/queue-dynamics/ns-3"
PCAP_WB_DIR="../logs/queue-dynamics/workbench"
PYTHON_SCRIPT="./plot_throughput.py"
OUTPUT_FILE="validation_throughput_comparison.pdf"
LINK_CAPACITY=2

# Create Workspace
TMP_DIR=$(mktemp -d)
echo "Created workspace: $TMP_DIR"

cleanup() {
    rm -rf "$TMP_DIR"
}
trap cleanup EXIT

# Extraction
extract_csv() {
    local input_dir=$1
    local output_subdir=$2
    local label=$3

    mkdir -p "$TMP_DIR/$output_subdir"
    echo "--- Processing $label Traces ---"
    
    count=$(ls "$input_dir"/*.pcap 2>/dev/null | wc -l)
    if [ "$count" -eq 0 ]; then
        echo "WARNING: No .pcap files found in $input_dir"
        return
    fi

    for pcap in "$input_dir"/*.pcap; do
        filename=$(basename "$pcap" .pcap)
        outfile="$TMP_DIR/$output_subdir/${filename}.csv"
        
        cat "$pcap" | tshark -r - \
               -Y "quic" \
               -T fields \
               -e frame.time_relative -e ip.len \
               -E separator=, \
               > "$outfile"
        echo "Extracted: $filename"
    done
}

# Run extraction for both files
extract_csv "$PCAP_NS3_DIR" "ns3" "NS-3"
extract_csv "$PCAP_WB_DIR" "wb" "Workbench"

# Plot results with python
echo "--- Generating Plot ---"
python3 "$PYTHON_SCRIPT" \
    --ns3-dir "$TMP_DIR/ns3" \
    --wb-dir "$TMP_DIR/wb" \
    --output "$OUTPUT_FILE" \
    --capacity "$LINK_CAPACITY"