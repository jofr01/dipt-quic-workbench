#!/bin/bash


#### Config ####
RESULTS_DIR="../../plots/experiment-3/logs"
TEMP_DIR="./temp"
BASE_CONFIG="mars-relay-network.json"
EMPTY_EVENTS="events-empty.json"

# Experiment Variables
CCA=("cubic" "bbr") 
LOSS_RATES=(0 1 5 10 20 30)
SEEDS=(1 2 3 4 5 6 7 8 9 10)


# Fixed Parameters 
DOWNLOAD_SIZE=1000000000



##### Run Script ####
mkdir -p "$RESULTS_DIR"
mkdir -p "$TEMP_DIR"

echo "Starting Experiment 3 Simulations..."

for cca in "${CCA[@]}"; do
  for loss in "${LOSS_RATES[@]}"; do
    for seed in "${SEEDS[@]}"; do

      # If loss is 0%, we only need 1 run because it is deterministic, skip all other seeds
      if [ "$loss" -eq 0 ] && [ "$seed" -ne 1 ]; then
        continue
      fi

      # Define Test ID and Folder
      TEST_ID="cca_${cca}_loss_${loss}_seed_${seed}"
      TEST_OUT_DIR="$RESULTS_DIR/$TEST_ID"
      CONFIG_FILE="$TEMP_DIR/${TEST_ID}.json"

      # Create folder for this specific run
      mkdir -p "$TEST_OUT_DIR"

      # Generate config 
      jq --arg cca "$cca" \
         --argjson loss "$loss" \
         '
         # Set CCA
         (.nodes[] | select(.id == "MarsRover" or .id == "MissionControl").quic.congestion_controller) |= $cca |

         # Configure loss rate
         (.nodes[] | select(.id == "MarsRover" or .id == "MissionControl").packet_loss_ratio) |= ($loss / 100.0) |

         # Set initial window to 1 BDP (25000) only for CUBIC
         if $cca == "cubic" then
           (.nodes[] | select(.id == "MarsRover" or .id == "MissionControl").quic.initial_congestion_window_packets) |= 25000
         else
           .
         end
         ' "$BASE_CONFIG" > "$CONFIG_FILE"

      # Run simulation
      echo "Running test: CCA: $cca, Loss: $loss%, Seed: $seed"

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
      mv "MarsRover.pcap" "$TEST_OUT_DIR/MarsRover.pcap"
      mv "server.qlog" "$TEST_OUT_DIR/MarsRover.qlog"
    done
  done
done

# Cleanup temp dir
rm -rf "$TEMP_DIR"

echo "Done! Results saved to $RESULTS_DIR"