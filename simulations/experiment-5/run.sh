#!/bin/bash


#### Config ####
RESULTS_DIR="../../plots/experiment-5/logs"
TEMP_DIR="./temp"
BASE_CONFIG="mars-relay-network-old.json"
EMPTY_EVENTS="events-empty.json"

# Experiment Variables
CCA=("bbr" "no_cc") 
# OUTAGE_DURATION=(0 15 30 60)
OUTAGE_DURATION=(0)

# Fixed Parameters 
DOWNLOAD_SIZE=1000000000
RTT_MS=120000



##### Run Script ####
mkdir -p "$RESULTS_DIR"
mkdir -p "$TEMP_DIR"

echo "Starting Experiment 5 Simulations..."

for cca in "${CCA[@]}"; do
  for duration in "${OUTAGE_DURATION[@]}"; do

    # Define Test ID and Folder
    TEST_ID="cca_${cca}_outage_${duration}_min"
    TEST_OUT_DIR="$RESULTS_DIR/$TEST_ID"
    CONFIG_FILE="$TEMP_DIR/${TEST_ID}.json"

    # Create folder for this specific run
    mkdir -p "$TEST_OUT_DIR"

    # Calculate timer parameter
    outage_ms=$((duration * 60 * 1000))
    max_idle_timeout_ms=$((outage_ms + 2 * RTT_MS))
    initial_rtt_ms=$RTT_MS

    # Generate config 
    jq --arg cca "$cca" \
        --argjson timeout "$max_idle_timeout_ms" \
        --argjson init_rtt "$initial_rtt_ms" \
        '
        # Set CCA
        (.nodes[] | select(.id == "MarsRover" or .id == "MissionControl").quic.congestion_controller) |= $cca |

        # Configure idle timeout
        (.nodes[] | select(.id == "MarsRover" or .id == "MissionControl").quic.maximum_idle_timeout_ms) |= $timeout |

        # Configure initial RTT
        (.nodes[] | select(.id == "MarsRover" or .id == "MissionControl").quic.initial_rtt_ms) |= $init_rtt |

        # Set initial window to 1 BDP (100000) only for fixed rate controller
        if $cca == "no_cc" then
          (.nodes[] | select(.id == "MarsRover" or .id == "MissionControl").quic.initial_congestion_window_packets) |= 100000
        else
          .
        end
        ' "$BASE_CONFIG" > "$CONFIG_FILE"

    # Run simulation
    echo "Running test: CCA: $cca, Outage duration (min): $duration"

    cargo run --release --bin quinn-workbench -- \
      quic \
      --network-graph "$CONFIG_FILE" \
      --network-events "events-${duration}.json" \
      --client-ip-address 192.168.10.1 \
      --server-ip-address 192.168.30.2 \
      --requests 1 \
      --response-size $DOWNLOAD_SIZE 
      > /dev/null 2>&1

    # Move traces
    mv "MarsRover.pcap" "$TEST_OUT_DIR/MarsRover.pcap"
    mv "MarsRover.qlog" "$TEST_OUT_DIR/MarsRover.qlog"
    mv "MissionControl.pcap" "$TEST_OUT_DIR/MissionControl.pcap"
  done
done

# Cleanup temp dir
rm -rf "$TEMP_DIR"

echo "Done! Results saved to $RESULTS_DIR"