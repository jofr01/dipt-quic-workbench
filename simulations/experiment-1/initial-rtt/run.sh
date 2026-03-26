cargo run --release --bin quinn-workbench -- \
  quic \
  --network-graph mars-relay-network.json \
  --network-events events-empty.json \
  --client-ip-address 192.168.10.1 \
  --server-ip-address 192.168.30.2 \
  --requests 1 --response-size 10000000

DEST_DIR="../../../plots/experiment-1/logs/initial-rtt/"
mkdir -p "$DEST_DIR"

cp MissionControl.pcap "$DEST_DIR"
cp MarsRover.pcap "$DEST_DIR"