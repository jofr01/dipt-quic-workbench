import argparse
import glob
import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns


sns.set_theme(style="whitegrid", font_scale=1.1)
plt.rcParams.update({'font.family': 'serif', 'lines.linewidth': 1.5})

def load_data(directory, label_prefix):
    """Loads all CSVs in a directory and calculates throughput."""
    data_frames = []
    files = sorted(glob.glob(os.path.join(directory, "*.csv")))
    
    if not files:
        print(f"Warning: No CSV files found in {directory}")
        return pd.DataFrame()

    print(f"Loading {len(files)} traces for {label_prefix}...")

    for f in files:
        try:
            # Read CSV
            df = pd.read_csv(f, names=["time", "len"], header=None)
            
            if df.empty:
                print(f"Skipping empty file: {f}")
                continue

            # Shift all timestamps so the first packet is at T=0.0s
            start_time = df["time"].min()
            df["time"] = df["time"] - start_time
            
            # Bin data into 1-second intervals
            df["time_bin"] = df["time"].astype(float).astype(int)
            
            # Sum bytes per bin and convert to Mbps
            throughput = df.groupby("time_bin")["len"].sum()
            throughput_mbps = (throughput * 8) / 1_000_000
            
            # Create DataFrame
            run_df = pd.DataFrame({
                "Time (s)": throughput_mbps.index,
                "Throughput (Mbps)": throughput_mbps.values,
                "Environment": label_prefix,
                "Trace": os.path.basename(f)
            })
            data_frames.append(run_df)
        except Exception as e:
            print(f"Skipping file {f}: {e}")
            
    return pd.concat(data_frames) if data_frames else pd.DataFrame()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wb-dir", required=True, help="Directory containing Workbench CSVs")
    parser.add_argument("--output", default="throughput_comparison.pdf", help="Output filename")
    parser.add_argument("--capacity", type=float, default=10.0, help="Link capacity in Mbps for reference line")
    args = parser.parse_args()

    # Load Data
    df_wb = load_data(args.wb_dir, "Measured Throughput")
    

    # Plotting
    plt.figure(figsize=(10, 5))
    
    sns.lineplot(
        data=df_wb, 
        x="Time (s)", 
        y="Throughput (Mbps)", 
        hue="Environment", 
        style="Environment",
        palette=["#E63946", "#1D3557"]
    )

    # Reference Line
    plt.axhline(y=args.capacity, color='gray', linestyle='--', alpha=0.5, label=f"Link Capacity ({args.capacity} Mbps)")

    plt.title(f"Channel Capacity Verification ({args.capacity} Mbps Link)")
    plt.ylim(bottom=0)
    plt.xlim(left=0)
    plt.legend(loc="lower right")
    plt.ylabel("Throughput (Mbps)")
    plt.tight_layout()
    
    plt.savefig(args.output)
    print(f"Success! Plot saved to {args.output}")

if __name__ == "__main__":
    main()