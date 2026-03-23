#!/usr/bin/env python3
import os
import sys
import re
import subprocess

# Configuration
LOGS_DIR = "../logs"
RESULTS_DIR = "../results"
SCRIPT_EXTRACT_TPUT = "../../scripts/extract_throughput.py"
SCRIPT_PLOT = "../../scripts/plot_timeseries.py"
TARGET_RESOLUTION_POINTS = 800
SENDER_IP = "192.168.30.2"

def get_duration_from_csv(csv_path):
    try:
        result = subprocess.run(['tail', '-n', '1', csv_path], capture_output=True, text=True)
        line = result.stdout.strip()
        if not line: return 0.0
        return float(line.split(',')[0])
    except:
        return 0.0

def main():
    if not os.path.exists(LOGS_DIR):
        print(f"Error: {LOGS_DIR} not found.")
        sys.exit(1)
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # Group runs by outage duration
    groups = {}
    pattern = re.compile(r'cca_(.*?)_outage_(\d+)_min')
    
    print(f"Scanning {LOGS_DIR}...")
    subdirs = [f.path for f in os.scandir(LOGS_DIR) if f.is_dir()]

    for folder in subdirs:
        match = pattern.search(os.path.basename(folder))
        if match:
            cca_name = match.group(1)
            duration_min = match.group(2)
            
            pcap = os.path.join(folder, "MarsRover.pcap")
            
            if duration_min not in groups:
                groups[duration_min] = []
            
            if os.path.exists(pcap):
                groups[duration_min].append((cca_name, pcap))

    # Process each outage duration
    for duration_min, runs in groups.items():
        print(f"\nProcessing Outage Duration: {duration_min} minutes")
        runs.sort(key=lambda x: x[0])
        
        plot_inputs = []
        temp_files = []
        durations = []
        
        for cca, pcap in runs:
            csv_path = pcap.replace(".pcap", "_throughput.csv")
            
            # Extract Throughput 
            if not os.path.exists(csv_path):
                print(f"  Extracting throughput for {cca.upper()}...")
                cmd_extract = [
                    sys.executable, SCRIPT_EXTRACT_TPUT,
                    "--pcap", pcap,
                    "--csv", csv_path,
                    "--sender", SENDER_IP,
                ]
                subprocess.run(cmd_extract, check=True)
            
            duration = get_duration_from_csv(csv_path)
            if duration > 0:
                durations.append(duration)

            label = f"{cca.upper()}"
            plot_inputs.append(f"{label}={csv_path}")
            temp_files.append(csv_path)
        
        # Calculate limits based on the longest run in this specific group
        if durations:
            max_duration = max(durations)
            x_limit = max_duration * 1.05 
            calc_binsize = max(1.0, x_limit / TARGET_RESOLUTION_POINTS)
        else:
            x_limit = 5000
            calc_binsize = 10.0

        output_pdf = os.path.join(RESULTS_DIR, f"sender_throughput_outage_{duration_min}m.pdf")
        title = f"Sender Throughput ({duration_min} min Outage)"
        
        # Build Plot Command
        cmd_plot = [
            sys.executable, SCRIPT_PLOT,
            "--title", title,
            "--output", output_pdf,
            "--binsize", str(calc_binsize), 
            "--ylabel", "Throughput (Mbps)",
            "--xlim", str(x_limit)
        ]
        
        for inp in plot_inputs:
            cmd_plot.extend(["--input", inp])
            
        print("  Generating plot...")
        subprocess.run(cmd_plot)
        print(f"  Saved to: {output_pdf}")

        # Cleanup
        for f in temp_files:
            if os.path.exists(f):
                os.remove(f)

    print("\nAll plots generated in:", RESULTS_DIR)

if __name__ == "__main__":
    main()