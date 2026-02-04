#!/usr/bin/env python3
import os
import sys
import re
import subprocess

# add helper scripts to syspath
current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.join(current_dir, "../../scripts")
sys.path.append(scripts_dir)

import extract_avg_ack_rate

# Configuration
LOGS_DIR = "../logs"
RESULTS_DIR = "../results"
ACK_SENDER_IP = "192.168.10.1"
SCRIPT_PLOT = "../../scripts/plot_saturation.py"
DOWNLINK_BPS = 2_000_000

# Capture steady state only
START_TIME = 1440.0
STOP_TIME = 2400.0

def main():
    if not os.path.exists(LOGS_DIR):
        print(f"Error: {LOGS_DIR} not found.")
        sys.exit(1)

    # Group runs
    groups = {}
    pattern = re.compile(r'up_(\d+)_ack_(\d+)_loss_(\d+)')
    
    print(f"Scanning {LOGS_DIR}...")
    subdirs = [f.path for f in os.scandir(LOGS_DIR) if f.is_dir()]

    for folder in subdirs:
        match = pattern.search(os.path.basename(folder))
        if match:
            uplink_bps = int(match.group(1))
            ack_ratio = int(match.group(2))
            loss_rate = int(match.group(3))
            
            pcap = os.path.join(folder, "MissionControl.pcap")
            
            key = (uplink_bps, loss_rate)
            if key not in groups:
                groups[key] = []
            groups[key].append((ack_ratio, pcap))

    
    # Process each group
    for (uplink, loss), runs in groups.items():
        print(f"Processing Uplink: {uplink} bps / Loss: {loss}%")
        
        # Sort runs by ACK ratio (Low -> High)
        runs.sort(key=lambda x: x[0])
        
        plot_inputs = []
        
        # Calculate rates for each run in this group
        for ack, pcap in runs:
            try:
                measured_bps = extract_avg_ack_rate.extract_avg_ack_rate(
                    pcap_path=pcap, 
                    sender_ip=ACK_SENDER_IP, 
                    start_time=START_TIME,
                    stop_time=STOP_TIME
                )
            except Exception as e:
                print(f"  Error extracting {pcap}: {e}")
                measured_bps = 0

            # Format Label (ACK Eliciting Threshold 1 -> Ratio 1:2)
            effective_ratio = ack + 1
            label = f"1:{effective_ratio}"
            
            # Format plotter input "Label=Measured:Capacity"
            plot_inputs.append(f"{label}={measured_bps}:{uplink}")

        # Output path
        output_pdf = os.path.join(RESULTS_DIR, f"saturation_up_{uplink}_loss_{loss}.pdf")
        
        # Define Title
        title = f"Reverse Path Saturation (Asymmetry 1:{int(DOWNLINK_BPS/uplink)}, Loss {loss}%)"
        
        # Build Plot Command
        cmd_plot = [
            sys.executable, SCRIPT_PLOT,
            "--title", title,
            "--output", output_pdf
        ]
        
        # Append all input arguments
        for inp in plot_inputs:
            cmd_plot.extend(["--input", inp])
            
        subprocess.run(cmd_plot)
        print(f"Generated: {output_pdf}")

    print("\nAll saturation plots generated in:", RESULTS_DIR)

if __name__ == "__main__":
    main()