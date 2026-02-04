#!/usr/bin/env python3
import os
import sys
import re
import pandas as pd
import subprocess

# add helper scripts to syspath
current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.join(current_dir, "../../scripts")
sys.path.append(scripts_dir)

import extract_fct
import calc_avg_goodput


# Configuration
LOGS_DIR = "../logs"
FILE_SIZE_BYTES = 360000000
SENDER_IP = "192.168.30.2" 
SCRIPT_PLOT_HEATMAP = "../../scripts/plot_heatmap.py"
DOWNLINK_BPS = 2_000_000
RESULTS_DIR = "../results"




def main():
    if not os.path.exists(LOGS_DIR):
        print(f"Error: {LOGS_DIR} not found.")
        sys.exit(1)

    data_points = []
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
            
            # calc metrics
            fct = extract_fct.extract_fct(pcap, SENDER_IP)
            fct -= 480  # subtract handshake delay (only looking at steady state)
            val = calc_avg_goodput.calc_avg_goodput(fct, FILE_SIZE_BYTES)
            
            data_points.append({
                "Uplink": uplink_bps, 
                "ACK": ack_ratio, 
                "Loss": loss_rate, 
                "Value": val
            })
            print(f"{uplink_bps}bps / ACK {ack_ratio} / Loss {loss_rate}% = {val:.2f} Mbps Goodput")

    if not data_points:
        print("No data found.")
        sys.exit(1)

    df = pd.DataFrame(data_points)

    # Split df in two csvs and generate plots
    for loss in sorted(df["Loss"].unique()):
        subset = df[df["Loss"] == loss].copy()
        
        # create csv
        csv_name = f"summary_loss_{loss}.csv"
        csv_path = os.path.join(RESULTS_DIR, csv_name)
        subset[["Uplink", "ACK", "Value"]].to_csv(csv_path, index=False)
        
        # Generate custom labels
        # y-axis
        sorted_uplinks = sorted(subset["Uplink"].unique(), reverse=True)
        y_labels = []
        for u in sorted_uplinks:
            ratio = int(DOWNLINK_BPS / u)
            y_labels.append(f"1:{ratio}")
        
        # x-axis
        sorted_acks = sorted(subset["ACK"].unique())
        x_labels = []
        for a in sorted_acks:
            # e.g. ACK Eliciting Threshold 1 -> Ratio 1:2
            x_labels.append(f"1:{int(a)+1}")

        # Join into comma separated strings
        y_label_str = ",".join(y_labels)
        x_label_str = ",".join(x_labels)
        
        # Call plotter script
        cmd = [
            sys.executable, SCRIPT_PLOT_HEATMAP,
            "--input", csv_path,
            "--output", os.path.join(RESULTS_DIR, f"goodput_heatmap_loss_{loss}.pdf"),
            "--title", f"Goodput Overview (Loss {loss}%)",
            "--vmin", "0", "--vmax", "2.0",
            "--cmap", "viridis",
            "--cbarlabel", "Goodput (Mbps)",
            "--ylabel", "Asymmetry Ratio",
            "--xlabel", "ACK Decimation Ratio",
            "--yticklabels", y_label_str,
            "--xticklabels", x_label_str
        ]
        
        subprocess.run(cmd)
        print(f"Generated goodput_heatmap_loss_{loss}.pdf")

if __name__ == "__main__":
    main()