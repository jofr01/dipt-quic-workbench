echo "Calculating the protocol overhead ratio for default initial RTT"
# Run python script to calculate protocol overhead when initial RTT is configured to default
python3 ../../scripts/protocol_overhead_ratio.py \
  --pcap ../logs/initial-rtt/MarsRover.pcap \
  --sender 192.168.30.2 \
  --filesize 10000000

echo "Calculating the protocol overhead ratio for tuned initial RTT"
# Run python script to calculate protocol overhead when initial RTT is configured to 20 minutes
python3 ../../scripts/protocol_overhead_ratio.py \
  --pcap ../logs/flow-control/MarsRover.pcap \
  --sender 192.168.30.2 \
  --filesize 10000000