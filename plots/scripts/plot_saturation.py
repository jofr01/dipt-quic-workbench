#!/usr/bin/env python3
import argparse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import sys

# Style settings
sns.set_theme(style="whitegrid", font_scale=1.1)
plt.rcParams.update({
    'font.family': 'serif', 
    'lines.linewidth': 1.5,
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'legend.fontsize': 10
})

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, help="Output filename")
    parser.add_argument("--title", required=True, help="Plot Title")
    
    # Input format: "Label=Measured_bps:Capacity_bps"
    parser.add_argument("--input", action='append', required=True, help="Data point in format 'Label=Measured:Capacity'")
    
    args = parser.parse_args()

    data = []

    # Parse Inputs
    for item in args.input:
        try:
            # Split input arg
            label_part, value_part = item.split('=')
            measured_str, capacity_str = value_part.split(':')
            
            measured = float(measured_str)
            capacity = float(capacity_str)
            
            if capacity == 0:
                utilization = 0.0
            else:
                utilization = (measured / capacity) * 100.0
            
            data.append({
                "Scenario": label_part.strip(),
                "Utilization (%)": utilization,
                "Capacity": capacity,
                "Measured": measured
            })
        except ValueError:
            print(f"Warning: Skipping malformed input '{item}'", file=sys.stderr)
            continue

    if not data:
        print("Error: No valid data points provided.", file=sys.stderr)
        sys.exit(1)

    df = pd.DataFrame(data)

    # Plotting
    plt.figure(figsize=(10, 5))
    
    # Custom color logic
    colors = ["tab:red" if x > 100 else "tab:green" for x in df["Utilization (%)"]]
                          
    # Draw bar chart
    ax = sns.barplot(
        x="Scenario", 
        y="Utilization (%)", 
        data=df, 
        palette=colors, 
        hue="Scenario", 
        legend=False
    )

    # Add threshold line
    plt.axhline(100, color='black', linestyle='--', linewidth=1.5, label="Link Capacity (100%)")

    # Add data labels
    for i, p in enumerate(ax.patches):
        height = p.get_height()
        
        # Simpler Label: Just "480%" or "15%"
        label_text = f"{height:.0f}%"
        
        ax.text(p.get_x() + p.get_width() / 2., 
                height + 5, 
                label_text, 
                ha="center", va="bottom", fontsize=10, color='black')

    # Formatting
    plt.title(args.title)
    plt.ylabel("Uplink Utilization (%)")
    plt.xlabel("ACK Decimation Ratio")
    
    # Adjust y-axis limit to fit the labels
    max_util = df["Utilization (%)"].max()
    plt.ylim(0, max(120, max_util * 1.25))
    
    plt.legend(loc="upper right")
    plt.tight_layout()

    plt.savefig(args.output)
    print(f"Success! Plot saved to {args.output}")

if __name__ == "__main__":
    main()