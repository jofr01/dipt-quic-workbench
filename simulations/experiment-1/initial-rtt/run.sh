cargo run --release --bin quinn-workbench -- \
  quic \
  --network-graph mars-relay-network.json \
  --network-events events-empty.json \
  --client-ip-address 192.168.10.1 \
  --server-ip-address 192.168.30.2 \
  --requests 1 --response-size 10000000

cp MissionControl.pcap ../../../plots/experiment-1/logs/initial-rtt/MissionControl.pcap
cp MarsRover.pcap ../../../plots/experiment-1/logs/initial-rtt/MarsRover.pcap