#!/usr/bin/env python3
import os
import sys
import re
import subprocess

# add helper scripts to syspath
current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.join(current_dir, "../../scripts")
sys.path.append(scripts_dir)

import extract_fct


# Configuration
LOGS_DIR = "../logs"
RESULTS_DIR = "../results"
SCRIPT_PLOT = "../../scripts/plot_barchart.py"
TARGET_RESOLUTION_POINTS = 800
SENDER_IP = "192.168.30.2" 


def main():
    if not os.path.exists(LOGS_DIR):
        print(f"Error: {LOGS_DIR} not found.")
        sys.exit(1)

    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)

    # Match test runs
    pattern = re.compile(r'cca_(.*?)_outage_(\d+)_min')
    
    print(f"Scanning {LOGS_DIR}...")
    subdirs = [f.path for f in os.scandir(LOGS_DIR) if f.is_dir()]

    # Collect all runs in a single list
    runs = []

    for folder in subdirs:
        match = pattern.search(os.path.basename(folder))
        if match:
            cca_name = match.group(1)
            duration_min = int(match.group(2))
            
            pcap = os.path.join(folder, "MarsRover.pcap")
            if os.path.exists(pcap):
                runs.append((duration_min, cca_name, pcap))



    # Sort primarily by outage duration, then by CCA name
    runs.sort(key=lambda x: (x[0], x[1]))
    
    plot_inputs = []
    
    # Extract FCT for each file
    for duration_min, cca_name, pcap in runs:
        print(f"Extracting FCT for {cca_name.upper()} (Outage: {duration_min}m)...")
        fct = extract_fct.extract_fct(pcap, sender_ip=SENDER_IP)
        
        if fct is not None:
            # Format: Label=Value
            label = f"{duration_min}m {cca_name.upper()}"
            plot_inputs.append(f"{label}={fct:.6f}")
        else:
            print(f"Warning: Could not extract valid FCT from {pcap}")

    if not plot_inputs:
        print("No valid data extracted. Exiting.")
        sys.exit(1)
        
    # Define Title
    title = "FCT Comparison for Intermittent Connectivity"

    # Output path
    output_pdf = os.path.join(RESULTS_DIR, "fct_overview_outages.pdf")

    # Build Plot Command
    cmd_plot = [
        sys.executable, SCRIPT_PLOT,
        "--title", title,
        "--output", output_pdf,
        "--ylabel", "Flow Completion Time (Seconds)",
        "--xlabel", "Outage Duration & Congestion Control"
    ]
    
    # Append all input files
    for inp in plot_inputs:
        cmd_plot.extend(["--input", inp])
        
    subprocess.run(cmd_plot)
    print(f"Generated: {output_pdf}")

if __name__ == "__main__":
    main()