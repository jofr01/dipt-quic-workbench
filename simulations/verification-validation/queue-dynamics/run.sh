cargo run --release --bin quinn-workbench -- \
  quic \
  --network-graph p2p-quic.json \
  --network-events events-empty.json \
  --client-ip-address 192.168.40.1 \
  --server-ip-address 192.168.40.2 \
  --requests 1 --response-size 10485760

cp Client.pcap ../../../plots/verification-validation/logs/queue-dynamics/workbench/Client.pcap