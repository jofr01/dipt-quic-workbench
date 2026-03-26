#!/bin/bash


#### Config ####
RESULTS_DIR="../../../plots/experiment-4/logs"
TEMP_DIR="./temp"
BASE_CONFIG="mars-relay-network.json"
EMPTY_EVENTS="events-empty.json"

# Experiment Variables
UPLINK_BWS=(100000 50000 25000 12500 6250 3125) 
ACK_THRESHOLDS=(1 3 7 15 31 63)
SEEDS=(1 2 3 4 5)

# Fixed Parameters
DOWNLOAD_SIZE=360000000



##### Run Script ####
mkdir -p "$RESULTS_DIR"
mkdir -p "$TEMP_DIR"

echo "Starting Experiment 4 Simulations (1% Loss)..."

for bw in "${UPLINK_BWS[@]}"; do
  for ack in "${ACK_THRESHOLDS[@]}"; do
    for seed in "${SEEDS[@]}"; do
      # Define Test ID and Folder
      TEST_ID="up_${bw}_ack_${ack}_loss_1_seed_${seed}"
      TEST_OUT_DIR="$RESULTS_DIR/$TEST_ID"
      CONFIG_FILE="$TEMP_DIR/${TEST_ID}.json"

      # Create folder for this specific run
      mkdir -p "$TEST_OUT_DIR"

      # Generate config 
      jq --argjson bw "$bw" \
          --argjson ack "$ack" \
          '
          # Set Uplink Bandwidth
          (.links[] | select(.id == "DSNGateway->MarsOrbiter").bandwidth_bps) |= $bw |

          # Configure ACK Frequency
          (.nodes[] | select(.id == "MarsRover" or .id == "MissionControl").quic.ack_frequency_config.ack_eliciting_threshold) |= $ack
          ' "$BASE_CONFIG" > "$CONFIG_FILE"

      # Run simulation
      echo "Running test: Bw: $bw, Ack: $ack, Loss: 1%, Seed: $seed"

      cargo run --release --bin quinn-workbench -- \
        quic \
        --network-graph "$CONFIG_FILE" \
        --network-events "$EMPTY_EVENTS" \
        --client-ip-address 192.168.10.1 \
        --server-ip-address 192.168.30.2 \
        --requests 1 \
        --response-size $DOWNLOAD_SIZE \
        --network-rng-seed "$seed" \
        > /dev/null 2>&1

      # Move traces
      mv "MissionControl.pcap" "$TEST_OUT_DIR/MissionControl.pcap"
    done
  done
done


# Cleanup temp dir
rm -rf "$TEMP_DIR"

echo "Done! Results saved to $RESULTS_DIR"