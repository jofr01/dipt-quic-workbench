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
LOGS_DIR = "../logs/initial_window"
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

    # Group runs
    groups = {}
    pattern = re.compile(r'cca_(.*?)_init_window_(\d+)')
    
    print(f"Scanning {LOGS_DIR}...")
    subdirs = [f.path for f in os.scandir(LOGS_DIR) if f.is_dir()]

    for folder in subdirs:
        match = pattern.search(os.path.basename(folder))
        if match:
            cca_name = match.group(1)
            init_window = int(match.group(2))
            
            # Filter only cubic
            if cca_name != "cubic":
                continue

            pcap = os.path.join(folder, "MarsRover.pcap")
            
            # Group by CCA
            key = cca_name
            if key not in groups:
                groups[key] = []
            
            if os.path.exists(pcap):
                groups[key].append((init_window, pcap))

    # Process each group
    for cca, runs in groups.items():
        print(f"Processing Group: CCA {cca}")
        
        # Sort runs by Init Window size
        runs.sort(key=lambda x: x[0])
        
        plot_inputs = []
        
        # Extract FCT for each file
        for init_window, pcap in runs:
            print(f"Extracting FCT for Init Window: {init_window}...")
            duration = extract_fct.extract_fct(pcap, sender_ip=SENDER_IP)
            
            if duration is not None:
                # Format: Label=Value
                label = f"{init_window}"
                plot_inputs.append(f"{label}={duration:.6f}")
            else:
                print(f"Warning: Could not extract valid FCT from {pcap}")

        if not plot_inputs:
            print(f"No valid data extracted for {cca}. Skipping plot.")
            continue
        
        # Define Title
        title = f"CUBIC Initial Window Tuning (FCT Comparison)"

        # Output path
        output_pdf = os.path.join(RESULTS_DIR, "cubic_init_window_tuning_fct.pdf")

        # Build Plot Command
        cmd_plot = [
            sys.executable, SCRIPT_PLOT,
            "--title", title,
            "--output", output_pdf,
            "--ylabel", "Flow Completion Time (Seconds)",
            "--xlabel", "Initial Window (Bytes)"
        ]
        
        # Append all input files
        for inp in plot_inputs:
            cmd_plot.extend(["--input", inp])
            
        subprocess.run(cmd_plot)
        print(f"Generated: {output_pdf}")

    print("\nAll plots generated in:", RESULTS_DIR)

if __name__ == "__main__":
    main()