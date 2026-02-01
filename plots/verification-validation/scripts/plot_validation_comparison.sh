# Extract Workbench data
python3 ../../scripts/extract_throughput.py \
  --pcap ../logs/queue-dynamics/workbench/Client.pcap \
  --sender 192.168.40.2 \
  --csv wb_trace.csv

# Extract NS-3 data (Sender: Node Left)
python3 ../../scripts/extract_throughput.py \
  --pcap ../logs/queue-dynamics/ns-3/trace_node_left.pcap \
  --sender 193.167.100.100 \
  --csv ns3_trace.csv

# Plot comparison
python3 ../../scripts/plot_throughput.py \
  --input "Workbench (Simulation)=wb_trace.csv" \
  --input "NS-3 (Emulation)=ns3_trace.csv" \
  --capacity 2.0 \
  --title "Queue Dynamics Comparison (2 Mbps Link)" \
  --output validation_throughput_comparison.pdf

# Clean up
rm wb_trace.csv ns3_trace.csv