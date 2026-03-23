# Extract data from run with flow control on
python3 ../../scripts/extract_throughput.py \
  --pcap ../logs/flow-control/MarsRover.pcap \
  --sender 192.168.30.2 \
  --csv flow_control_on.csv
# Extract data from run with flow control off
python3 ../../scripts/extract_throughput.py \
  --pcap ../logs/baseline/MarsRover.pcap \
  --sender 192.168.30.2 \
  --csv flow_control_off.csv

# Plot data
python3 ../../scripts/plot_data_transfered.py \
  --input "FC On (Default)=flow_control_on.csv" \
  --input "FC Off (Baseline Profile)=flow_control_off.csv" \
  --title "Comparison: Flow Control Limited Data Transfer" \
  --output fc_limited_graph.pdf

# Clean up
rm flow_control_on.csv flow_control_off.csv
