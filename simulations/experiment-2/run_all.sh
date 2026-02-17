#!/bin/bash


#### Config ####
RESULTS_DIR="../../plots/experiment-2/logs"
TEMP_DIR="./temp"
BASE_CONFIG="mars-relay-network.json"
EMPTY_EVENTS="events-empty.json"

# Experiment Variables
CCA=("bbr") 
INITIAL_WINDOWS=(10)

# Fixed Parameters 
DOWNLOAD_SIZE=1000000000



##### Run Script ####
mkdir -p "$RESULTS_DIR"
mkdir -p "$TEMP_DIR"

echo "Starting Experiment 4 Simulations..."

for cca in "${CCA[@]}"; do
  for iw in "${INITIAL_WINDOWS[@]}"; do
  
    # Define Test ID and Folder
    TEST_ID="cca_${cca}v3_init_window_${iw}"
    TEST_OUT_DIR="$RESULTS_DIR/$TEST_ID"
    CONFIG_FILE="$TEMP_DIR/${TEST_ID}.json"

    # Create folder for this specific run
    mkdir -p "$TEST_OUT_DIR"

    # Generate config 
    jq --arg cca "$cca" \
        --argjson iw "$iw" \
        '
        # Set CCA
        (.nodes[] | select(.id == "MarsRover" or .id == "MissionControl").quic.congestion_controller) |= $cca |

        # Configure initial window
        (.nodes[] | select(.id == "MarsRover" or .id == "MissionControl").quic.initial_congestion_window_packets) |= $iw
        ' "$BASE_CONFIG" > "$CONFIG_FILE"

    # Run simulation
    echo "Running test: CCA: $cca, Initial Window: $iw"

    cargo run --release --bin quinn-workbench -- \
      quic \
      --network-graph "$CONFIG_FILE" \
      --network-events "$EMPTY_EVENTS" \
      --client-ip-address 192.168.10.1 \
      --server-ip-address 192.168.30.2 \
      --requests 1 \
      --response-size $DOWNLOAD_SIZE 
      > /dev/null 2>&1

    # Move traces
    mv "MarsRover.pcap" "$TEST_OUT_DIR/MarsRover.pcap"
    mv "MarsRover.qlog" "$TEST_OUT_DIR/MarsRover.qlog"

  done
done

# Cleanup temp dir
rm -rf "$TEMP_DIR"

echo "Done! Results saved to $RESULTS_DIR"