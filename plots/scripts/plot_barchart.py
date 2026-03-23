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

# Parses 'Label=Value' input flag string
def parse_input_arg(arg):
    try:
        label, val = arg.split('=', 1)
        return str(label.strip()), float(val.strip())
    except ValueError:
        raise argparse.ArgumentTypeError(f"Input must be 'Label=Value' (e.g., '12500=0.45'). Got: {arg}")

def main():
    parser = argparse.ArgumentParser(description="Generate Bar Charts.")
    
    parser.add_argument("--input", action='append', type=parse_input_arg, required=True, 
                        help="Input data in format 'Label=Value'")
    
    parser.add_argument("--output", default="barchart.pdf", help="Output filename")
    parser.add_argument("--title", required=True, help="Plot Title")
    parser.add_argument("--ylabel", default="Value", help="Y-Axis Label")
    parser.add_argument("--xlabel", default="Configuration", help="X-Axis Label")
    
    args = parser.parse_args()

    # Load all data into a pandas DataFrame
    data = []
    for label, val in args.input:
        data.append({"Configuration": label, "Value": val})
        
    df = pd.DataFrame(data)

    if df.empty:
        print("Error: No valid data found to plot.")
        sys.exit(1)

    # Plotting
    plt.figure(figsize=(10, 5))
    
    # Main Barplot
    ax = sns.barplot(
        data=df, 
        x="Configuration", 
        y="Value",
        hue="Configuration",
        palette="tab10",
        legend=False
    )

    # Add values on top of the bars for readability
    for container in ax.containers:
        ax.bar_label(container, fmt='%.0f', padding=3, fontsize=10)

    # Formatting
    plt.title(args.title)
    plt.xlabel(args.xlabel)
    plt.ylabel(args.ylabel)
    max_val = df["Value"].max()
    plt.ylim(bottom=0, top=max_val * 1.15)
    
    # Rotate X-labels
    plt.xticks(rotation=45, ha='right')

    plt.tight_layout()
    
    plt.savefig(args.output)
    print(f"Success! Plot saved to {args.output}")

if __name__ == "__main__":
    main()