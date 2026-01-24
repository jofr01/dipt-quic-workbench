cargo run --release --bin quinn-workbench -- \
  quic \
  --network-graph p2p-quic-1.json \
  --network-events events-empty.json \
  --client-ip-address 192.168.40.1 \
  --server-ip-address 192.168.40.2 \
  --requests 1 --response-size 12582912

cp Client.pcap ../../../../plots/verification-validation/logs/channel-characteristics/loss/1/Client.pcap
cp Server.pcap ../../../../plots/verification-validation/logs/channel-characteristics/loss/1/Server.pcap

cargo run --release --bin quinn-workbench -- \
  quic \
  --network-graph p2p-quic-5.json \
  --network-events events-empty.json \
  --client-ip-address 192.168.40.1 \
  --server-ip-address 192.168.40.2 \
  --requests 1 --response-size 12582912

cp Client.pcap ../../../../plots/verification-validation/logs/channel-characteristics/loss/5/Client.pcap
cp Server.pcap ../../../../plots/verification-validation/logs/channel-characteristics/loss/5/Server.pcap

cargo run --release --bin quinn-workbench -- \
  quic \
  --network-graph p2p-quic-10.json \
  --network-events events-empty.json \
  --client-ip-address 192.168.40.1 \
  --server-ip-address 192.168.40.2 \
  --requests 1 --response-size 12582912

cp Client.pcap ../../../../plots/verification-validation/logs/channel-characteristics/loss/10/Client.pcap
cp Server.pcap ../../../../plots/verification-validation/logs/channel-characteristics/loss/10/Server.pcap