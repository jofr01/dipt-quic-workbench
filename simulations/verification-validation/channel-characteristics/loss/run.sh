#!/bin/bash
for LOSS in 1 5 10
do
    for RUN in {1..10}
    do
        cargo run --release --bin quinn-workbench -- \
          quic \
          --network-graph "p2p-quic-${LOSS}.json" \
          --network-events events-empty.json \
          --client-ip-address 192.168.40.1 \
          --server-ip-address 192.168.40.2 \
          --requests 1 --response-size 10485760 \
          --network-rng-seed ${RUN}

        DEST="../../../../plots/verification-validation/logs/channel-characteristics/loss/${LOSS}/run_${RUN}"
        mkdir -p "$DEST"

        cp Client.pcap "$DEST/Client.pcap"
        cp Server.pcap "$DEST/Server.pcap"

        rm Client.pcap Server.pcap
    done
done