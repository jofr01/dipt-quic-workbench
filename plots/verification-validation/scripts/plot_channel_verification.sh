# Extract throughput data
python3 ../../scripts/extract_throughput.py \
  --pcap ../logs/channel-characteristics/no-loss/Client.pcap \
  --sender 192.168.40.2 \
  --csv wb_no_loss.csv

# Plot
python3 ../../scripts/plot_timeseries.py \
  --input "Measured Throughput (No Loss)=wb_no_loss.csv" \
  --output verification_throughput.pdf \
  --capacity 2.0 \
  --title "Channel Capacity Verification"

# 3. Cleanup
rm wb_no_loss.csv