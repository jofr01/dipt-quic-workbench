#!/usr/bin/env python3
import os
import sys
import re
import subprocess


# Configuration
LOGS_DIR = "../logs/control"
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
            
            qlog = os.path.join(folder, "MarsRover.qlog")
            
            # Group by Init Window
            key = init_window
            if key not in groups:
                groups[key] = []
            
            if os.path.exists(qlog):
                groups[key].append((cca_name, qlog))

    # Process each group
    for init_window, runs in groups.items():
        print(f"Processing Group: Init Window {init_window}")
        
        # Sort runs alphabetically by CCA name
        runs.sort(key=lambda x: x[0])
        
        plot_inputs = []
        temp_files = []
        max_duration_in_group = 0.0
        
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
            if duration > max_duration_in_group:
                max_duration_in_group = duration

            # Format Label
            label = f"{cca.upper()}"
            
            # Add to plotter inputs
            plot_inputs.append(f"{label}={csv_path}")
            temp_files.append(csv_path)
        
        # Calc dynamic bin size
        if max_duration_in_group > 0:
            calc_binsize = max(1, max_duration_in_group / TARGET_RESOLUTION_POINTS)
        else:
            calc_binsize = 10.0

        # Output path
        output_pdf = os.path.join(RESULTS_DIR, f"control_cwnd_comparison.pdf")
        
        # Define Title
        title = f"Congestion Window in Terrestrial Control Scenario (Default Configuration)"
        
        # Build Plot Command
        cmd_plot = [
            sys.executable, SCRIPT_PLOT,
            "--title", title,
            "--output", output_pdf,
            "--binsize", str(calc_binsize), 
            "--ylabel", "CWND (MB)"
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