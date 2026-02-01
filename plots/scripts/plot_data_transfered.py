#!/usr/bin/env python3
import argparse
import os
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

# Load csv, calc troughout and return data frame
def load_and_process(path, label):
    try:
        df = pd.read_csv(path)

        if df.empty:
            print(f"Warning: {path} is empty.")
            return pd.DataFrame()

        # Sort by time to ensure correct cumulative sum
        df = df.sort_values(by="time")
        
        # Calculate Cumulative Sum in MB
        df["cumulative_mb"] = df["len"].cumsum() / 1_000_000
        
        return pd.DataFrame({
            "Time (s)": df["time"],
            "Data Transferred (MB)": df["cumulative_mb"],
            "Configuration": label
        })
    except Exception as e:
        print(f"Error processing {path}: {e}")
        return pd.DataFrame()

def main():
    parser = argparse.ArgumentParser(description="Generate Cumulative Data Transfer Plots.")
    
    # Can be called multiple times
    # e.g., --input "Run 1=run1.csv" --input "Run 2=run2.csv"
    parser.add_argument("--input", action='append', type=parse_input_arg, required=True, 
                        help="Input dataset in format 'Label=path/to/csv'")
    
    parser.add_argument("--output", default="plot.pdf", help="Output filename")
    parser.add_argument("--title", required=True, help="Plot Title")
    parser.add_argument("--xlim", type=float, default=None, help="Limit X-axis (seconds)")
    
    args = parser.parse_args()

    # Load All Data
    all_data = []
    for label, path in args.input:
        print(f"Loading {label} from {path}...")
        df = load_and_process(path, label)
        all_data.append(df)
    
    full_df = pd.concat(all_data) if all_data else pd.DataFrame()

    if full_df.empty:
        print("Error: No valid data found to plot.")
        return

    # Plotting
    plt.figure(figsize=(10, 6))
    
    # Main Staircase Plot
    sns.lineplot(
        data=full_df, 
        x="Time (s)", 
        y="Data Transferred (MB)", 
        hue="Configuration", 
        style="Configuration",
        palette="tab10",
        drawstyle='steps-post', 
        dashes=False
    )

    # Formatting
    plt.title(args.title)
    plt.ylabel("Data Transferred (MB)")
    plt.xlabel("Time (seconds)")
    plt.ylim(bottom=0)
    
    if args.xlim:
        plt.xlim(0, args.xlim)
    else:
        plt.xlim(left=0)

    plt.legend(loc="lower right")
    plt.tight_layout()
    
    plt.savefig(args.output)
    print(f"Success! Plot saved to {args.output}")

if __name__ == "__main__":
    main()