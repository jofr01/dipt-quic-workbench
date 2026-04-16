#!/usr/bin/env python3
import argparse
import os
import sys
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

# Style settings
sns.set_theme(style="whitegrid", font_scale=1.1)
plt.rcParams.update({
    'font.family': 'serif', 
    'lines.linewidth': 1.5,
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'legend.fontsize': 10
})

# Parses 'Label=Path' input flag string
def parse_input_arg(arg):
    try:
        label, path = arg.split('=', 1)
        return label.strip(), path.strip()
    except ValueError:
        raise argparse.ArgumentTypeError(f"Input must be 'Label=Path/to/file.csv'. Got: {arg}")

# Load csv, process data and return data frame
def load_and_process(path, label, bin_size):
    try:
        df = pd.read_csv(path)

        if df.empty:
            print(f"Warning: {path} is empty.")
            return pd.DataFrame()

        # Binning
        df["time_bin"] = (df["time"] // bin_size) * bin_size
        
        # Mode detection based on columns
        if "len" in df.columns:
            # Throughput Mode: Convert Bytes/Bin to Mbps
            grouped = df.groupby("time_bin")["len"].sum()
            values = (grouped * 8) / 1_000_000 / bin_size
            
            if not values.empty:
                max_bin = values.index.max()
                # Create timeline up to runs last packet
                full_timeline = [i * bin_size for i in range(int(max_bin / bin_size) + 1)]
                # Reindex and fill missing intermediate bins with 0
                values = values.reindex(full_timeline).fillna(0)
            
        elif "cwnd" in df.columns:
            # CWND Mode: Highest value in bin (capture the operating window, filter out probing), convert Bytes to MB
            values = df.groupby("time_bin")["cwnd"].mean() / 1_000_000
            
            if not values.empty:
                max_bin = values.index.max()
                # Create timeline up to runs last event
                full_timeline = [i * bin_size for i in range(int(max_bin / bin_size) + 1)]
                # Reindex and forward-fill missing intermediate bins
                values = values.reindex(full_timeline).ffill().bfill()

        elif "latest_rtt" in df.columns:
            # RTT Mode: Highest value in bin (we are interested in peaks)
            values = df.groupby("time_bin")["latest_rtt"].max()
            
            if not values.empty:
                max_bin = values.index.max()
                # Create timeline up to runs last event
                full_timeline = [i * bin_size for i in range(int(max_bin / bin_size) + 1)]
                # Reindex and forward-fill missing intermediate bins
                values = values.reindex(full_timeline).ffill().bfill()
            
        else:
            # Fallback
            val_col = df.columns[1]
            values = df.groupby("time_bin")[val_col].mean()
        
        return pd.DataFrame({
            "Time (s)": values.index,
            "Value": values.values,
            "Configuration": label
        })
    except Exception as e:
        print(f"Error processing {path}: {e}")
        return pd.DataFrame()

def main():
    parser = argparse.ArgumentParser(description="Generate Plots.")
    
    parser.add_argument("--input", action='append', type=parse_input_arg, required=True, 
                        help="Input dataset in format 'Label=path/to/csv'")
    
    parser.add_argument("--output", default="plot.pdf", help="Output filename")
    parser.add_argument("--title", required=True, help="Plot Title")
    parser.add_argument("--ylabel", default="Throughput (Mbps)", help="Y-Axis Label")
    parser.add_argument("--capacity", type=float, default=None, help="Reference Line Value")
    parser.add_argument("--xlim", type=float, default=None, help="Limit X-axis (seconds)")
    parser.add_argument("--binsize", type=float, default=1.0, help="Calculation Intervall (seconds)")
    # Optional markers for link outages
    parser.add_argument("--outage-duration", type=float, default=0.0, help="Outage duration in minutes")
    parser.add_argument("--outage-offset", type=float, default=240.0, help="Simulation start offset in seconds")

    
    args = parser.parse_args()

    # Load all data and combine in one df
    all_data = []

    for label, path in args.input:
        print(f"Loading {label} from {path}...")
        df = load_and_process(path, label, args.binsize)
        if not df.empty:
            all_data.append(df)
            
    full_df = pd.concat(all_data) if all_data else pd.DataFrame()

    if full_df.empty:
        print("Error: No valid data found to plot.")
        sys.exit(1)

    # Plotting
    plt.figure(figsize=(10, 5))
    
    # Main Lineplot
    sns.lineplot(
        data=full_df, 
        x="Time (s)", 
        y="Value", 
        hue="Configuration", 
        style="Configuration",
        palette="tab10",
        dashes=False,
        errorbar="sd",
        estimator="mean"
    )

    # Reference Line
    if args.capacity:
        plt.axhline(y=args.capacity, color='tab:red', linestyle='--', alpha=0.6, 
                   label=f"Reference")

    # Formatting
    plt.title(args.title)
    plt.xlabel("Time (seconds)")
    plt.ylim(bottom=0)
    
    # Set Y Label directly from args
    plt.ylabel(args.ylabel)

    if args.xlim:
        plt.xlim(0, args.xlim)
    else:
        plt.xlim(left=0)

    # Outage marker
    if args.outage_duration > 0:
        d_sec = args.outage_duration * 60
        cycle_sec = 3 * d_sec
        offset = args.outage_offset
        
        # Determine the maximum x value to stop drawing lines
        max_x = args.xlim if args.xlim else full_df["Time (s)"].max()
        
        k = 0
        added_labels = False
        
        while True:
            # Calculate absolute simulation times
            t_sim_start = (2 * d_sec) + (k * cycle_sec)
            t_sim_end = t_sim_start + d_sec
            
            # Shift times to match the plot x-axis
            t_plot_start = t_sim_start - offset
            t_plot_end = t_sim_end - offset
            
            # Stop if the next start line is beyond the plot limits
            if t_plot_start > max_x:
                break
                
            # Draw Outage Start (Red dotted line)
            if t_plot_start >= 0:
                plt.axvline(x=t_plot_start, color='tab:red', linestyle=':', linewidth=1.5, alpha=0.8,
                            label="Outage Start" if not added_labels else "")   # Only add labels once
                            
            # Draw Outage End (Green dashed-dotted line)
            if t_plot_end <= max_x and t_plot_end >= 0:
                plt.axvline(x=t_plot_end, color='tab:green', linestyle='-.', linewidth=1.5, alpha=0.8,
                            label="Outage End" if not added_labels else "")
                            
            added_labels = True
            k += 1

    plt.legend(loc="lower right")
    plt.tight_layout()
    
    plt.savefig(args.output)
    print(f"Success! Plot saved to {args.output}")

if __name__ == "__main__":
    main()