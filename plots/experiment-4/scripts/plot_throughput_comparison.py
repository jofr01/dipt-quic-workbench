#!/usr/bin/env python3
import os
import sys
import re
import subprocess


# Configuration
LOGS_DIR = "../logs"
RESULTS_DIR = "../results"
SENDER_IP = "192.168.30.2" 
SCRIPT_EXTRACT_CSV = "../../scripts/extract_throughput.py"
SCRIPT_PLOT = "../../scripts/plot_timeseries.py"
DOWNLINK_BPS = 2_000_000
TARGET_RESOLUTION_POINTS = 800


def get_duration_from_csv(csv_path):
    try:
        result = subprocess.run(['tail', '-n', '1', csv_path], capture_output=True, text=True)
        line = result.stdout.strip()
        if not line: 
            return 0.0
        
        # Split by comma, first column is timestamp
        parts = line.split(',')
        return float(parts[0])
    except:
        return 0.0


def main():
    if not os.path.exists(LOGS_DIR):
        print(f"Error: {LOGS_DIR} not found.")
        sys.exit(1)

    # Group runs
    groups = {}
    pattern = re.compile(r'up_(\d+)_ack_(\d+)_loss_(\d+)(?:_seed_(\d+))?')
    
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
        
        # Sort runs by ACK ratio
        runs.sort(key=lambda x: x[0])
        
        plot_inputs = []
        temp_files = []
        max_duration_in_group = 0.0
        
        # Extract CSV for each line in this plot
        for ack, pcap in runs:
            # Store next to pcap
            csv_path = pcap.replace(".pcap", "_throughput.csv")
            
            # Extract Throughput (if csv not existent yet)
            if not os.path.exists(csv_path):
                cmd_extract = [
                    sys.executable, SCRIPT_EXTRACT_CSV,
                    "--pcap", pcap,
                    "--sender", SENDER_IP,
                    "--csv", csv_path
                ]
                subprocess.run(cmd_extract, check=True)
            
            # Peek at duration
            duration = get_duration_from_csv(csv_path)
            if duration > max_duration_in_group:
                max_duration_in_group = duration

            # Format Label (ACK Eliciting Threshold 1 -> Ratio 1:2)
            effective_ratio = ack + 1
            label = f"ACK Ratio 1:{effective_ratio}"
            
            # Add to plotter inputs
            plot_inputs.append(f"{label}={csv_path}")

            # Add CSV to temp files for clean up
            temp_files.append(csv_path)
        

        # Calc dynamic bin size
        if max_duration_in_group > 0:
            calc_binsize = max_duration_in_group / TARGET_RESOLUTION_POINTS
            # Avoid to noisy plots
            calc_binsize = max(1, calc_binsize)
        # Default fallback
        else:
            calc_binsize = 10.0

        # Output path
        output_pdf = os.path.join(RESULTS_DIR, f"throughput_up_{uplink}_loss_{loss}.pdf")
        
        # Define Title
        title = f"Throughput Comparison (Asymmetry Ratio 1:{int(DOWNLINK_BPS/uplink)}, Loss {loss}%)"
        
        # Build Plot Command
        cmd_plot = [
            sys.executable, SCRIPT_PLOT,
            "--title", title,
            "--output", output_pdf,
            "--binsize", str(calc_binsize), 
        ]
        
        # Append all input files
        for inp in plot_inputs:
            cmd_plot.extend(["--input", inp])
            
        subprocess.run(cmd_plot)
        print(f"Generated: {output_pdf}")

        # Cleanup CSVs
        print(f"Cleaning up {len(plot_inputs)} CSV files...")
        for f in temp_files:
            if os.path.exists(f):
                os.remove(f)

    print("\nAll plots generated in:", RESULTS_DIR)

if __name__ == "__main__":
    main()