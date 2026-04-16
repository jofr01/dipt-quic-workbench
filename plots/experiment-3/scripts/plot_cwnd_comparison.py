#!/usr/bin/env python3
import os
import sys
import re
import subprocess


# Configuration
LOGS_DIR = "../logs"
RESULTS_DIR = "../results"
SCRIPT_EXTRACT_CWND = "../../scripts/extract_cwnd.py"
SCRIPT_PLOT = "../../scripts/plot_timeseries.py"
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

    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)

    # Group runs by loss rate
    groups = {}
    pattern = re.compile(r'cca_(.*?)_loss_(\d+)_seed_(\d+)')
    
    print(f"Scanning {LOGS_DIR}...")
    subdirs = [f.path for f in os.scandir(LOGS_DIR) if f.is_dir()]

    for folder in subdirs:
        match = pattern.search(os.path.basename(folder))
        if match:
            cca_name = match.group(1)
            loss_rate = match.group(2)

            qlog = os.path.join(folder, "MarsRover.qlog")
            
            # Group by loss rate
            key = loss_rate
            if key not in groups:
                groups[key] = []
            
            if os.path.exists(qlog):
                groups[key].append((cca_name, qlog))

    # Process each group
    for loss_rate, runs in groups.items():
        print(f"Processing Loss Rate: {loss_rate}%")

        # Sort runs alphabetically by CCA name
        runs.sort(key=lambda x: x[0])
        
        plot_inputs = []
        temp_files = []
        durations = []
        
        # Extract CSV for each line in this plot
        for cca, qlog in runs:
            csv_path = qlog.replace(".qlog", "_cwnd.csv")
            
            # Extract CWND (if csv not existent yet)
            if not os.path.exists(csv_path):
                cmd_extract = [
                    sys.executable, SCRIPT_EXTRACT_CWND,
                    "--qlog", qlog,
                    "--csv", csv_path
                ]
                subprocess.run(cmd_extract, check=True)
            
            # Peek at duration
            duration = get_duration_from_csv(csv_path)
            if duration > 0:
                durations.append(duration)

            # Format Label
            label = f"{cca.upper()}"
            
            # Add to plotter inputs
            plot_inputs.append(f"{label}={csv_path}")
            temp_files.append(csv_path)
        
        # Limit plot and calc dynamic bin size
        if durations:
            min_duration = min(durations)
            x_limit = min_duration * 1.15 
            calc_binsize = max(1.0, x_limit / TARGET_RESOLUTION_POINTS)
        else:
            x_limit = 5000
            calc_binsize = 10.0

        # Output path
        output_pdf = os.path.join(RESULTS_DIR, f"cwnd_comparison_loss_{loss_rate}.pdf")
        
        # Define Title
        title = f"Congestion Window Comparison ({loss_rate}% Packet Loss)"
        
        # Build Plot Command
        cmd_plot = [
            sys.executable, SCRIPT_PLOT,
            "--title", title,
            "--output", output_pdf,
            "--binsize", str(calc_binsize), 
            "--ylabel", "CWND (MB)",
            "--xlim", str(x_limit)
        ]
        
        # Append all input files
        for inp in plot_inputs:
            cmd_plot.extend(["--input", inp])
            
        subprocess.run(cmd_plot)
        print(f"Generated: {output_pdf}")

        # Cleanup CSVs
        print(f"Cleaning up {len(temp_files)} CSV files...")
        for f in temp_files:
            if os.path.exists(f):
                os.remove(f)

    print("\nAll plots generated in:", RESULTS_DIR)

if __name__ == "__main__":
    main()