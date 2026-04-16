#!/usr/bin/env python3
import os
import sys
import re
import subprocess
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns


# Configuration
LOGS_DIR = "../logs/baseline"
RESULTS_DIR = "../results"
SCRIPT_EXTRACT_CWND = "../../scripts/extract_cwnd.py"
SCRIPT_PLOT = "../../scripts/plot_timeseries.py"
TARGET_RESOLUTION_POINTS = 800

# Micro Plot Configuration
MICRO_START_TIME = 1900
MICRO_END_TIME = 2100
MICRO_CCA = "bbr"

# Style settings
sns.set_theme(style="whitegrid", font_scale=1.1)
plt.rcParams.update({
    'font.family': 'serif', 
    'lines.linewidth': 1.5,
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'legend.fontsize': 10
})


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

            # Special Case: BBR Micro Plot to show probing
            if cca.lower() == MICRO_CCA.lower():
                print(f"Generating Micro Plot for {label}...")
                try:
                    df = pd.read_csv(csv_path)
                    
                    if not df.empty and "cwnd" in df.columns and "time" in df.columns:
                        # Convert CWND from Bytes to MB
                        df["CWND (MB)"] = df["cwnd"] / 1_000_000
                        
                        # Get raw data inside the timeframe
                        df_subset = df[(df["time"] >= MICRO_START_TIME) & (df["time"] <= MICRO_END_TIME)].copy()
                        
                        # Get last known state before the window
                        past_data = df[df["time"] < MICRO_START_TIME]
                        if not past_data.empty:
                            last_cwnd = past_data.iloc[-1]["CWND (MB)"]
                            start_point = pd.DataFrame({"time": [MICRO_START_TIME], "CWND (MB)": [last_cwnd]})
                            df_subset = pd.concat([start_point, df_subset], ignore_index=True)
                            
                        # Carry the last known state to the end of the window
                        if not df_subset.empty:
                            final_cwnd = df_subset.iloc[-1]["CWND (MB)"]
                            end_point = pd.DataFrame({"time": [MICRO_END_TIME], "CWND (MB)": [final_cwnd]})
                            df_subset = pd.concat([df_subset, end_point], ignore_index=True)
                        
                        if not df_subset.empty:
                            plt.figure(figsize=(10, 5))
                            
                            sns.lineplot(
                                data=df_subset, 
                                x="time", 
                                y="CWND (MB)", 
                                drawstyle='steps-post', 
                                linewidth=2,
                                color="tab:blue"
                            )
                            
                            plt.title(f"{label} CWND Probing Dynamics ({MICRO_START_TIME}s - {MICRO_END_TIME}s)")
                            plt.xlabel("Time (seconds)")
                            plt.ylabel("CWND (MB)")
                            plt.xlim(MICRO_START_TIME, MICRO_END_TIME)
                            
                            plt.tight_layout()
                            micro_output = os.path.join(RESULTS_DIR, f"baseline_micro_cwnd_{cca.lower()}.pdf")
                            plt.savefig(micro_output)
                            plt.close()
                            print(f"Success: Saved micro plot to {micro_output}")
                        else:
                            print(f"Warning: No data found for {label} in the {MICRO_START_TIME}s - {MICRO_END_TIME}s window.")
                except Exception as e:
                    print(f"Error generating micro plot for {label}: {e}")
        
        # Calc dynamic bin size
        if max_duration_in_group > 0:
            calc_binsize = max(1, max_duration_in_group / TARGET_RESOLUTION_POINTS)
        else:
            calc_binsize = 10.0

        # Output path
        output_pdf = os.path.join(RESULTS_DIR, f"baseline_cwnd_comparison.pdf")
        
        # Define Title
        title = f"Congestion Window Comparison (Default Configuration)"
        
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