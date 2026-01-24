#!/bin/bash

SENDER="192.168.40.2"
LOG_DIR="../logs/channel-characteristics/loss"
RATIOS=("1" "5" "10")

echo "Config(%)  Sent      Received    Lost      Observed(%)  Error(%)"
echo "----------------------------------------------------------------"

for R in "${RATIOS[@]}"; do
    server_pcap="${LOG_DIR}/${R}/Server.pcap"
    client_pcap="${LOG_DIR}/${R}/Client.pcap"

    # Count packets from sender
    sent=$(cat "$server_pcap" | tshark -r - -Y "ip.src == $SENDER" 2>/dev/null | wc -l)
    received=$(cat "$client_pcap" | tshark -r - -Y "ip.src == $SENDER" 2>/dev/null | wc -l)

    if [ "$sent" -eq 0 ]; then
        echo "No packets found in $server_pcap"
        continue
    fi

    lost=$((sent - received))
    
    # Calc percentages
    obs_loss=$(echo "scale=4; ($lost / $sent) * 100" | bc)
    error=$(echo "scale=4; $obs_loss - $R" | bc)

    printf "%-10s %-10s %-10s %-10s %-12s %-10s\n" "$R" "$sent" "$received" "$lost" "$obs_loss" "$error"
done