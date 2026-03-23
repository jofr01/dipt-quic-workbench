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
    
    # Input format: "Label=Measured_bps:Capacity_bps[:StdDev_bps]"
    parser.add_argument("--input", action='append', required=True, help="Data point in format 'Label=Measured:Capacity[:StdDev]'")
    
    args = parser.parse_args()

    data = []

    # Parse Inputs
    for item in args.input:
        try:
            # Split input arg
            label_part, value_part = item.split('=')
            parts = value_part.split(':')
            
            measured = float(parts[0])
            capacity = float(parts[1])

            # Optional 3rd argument for standard deviation
            std_dev = float(parts[2]) if len(parts) > 2 else 0.0
            
            if capacity == 0:
                utilization = 0.0
                std_utilization = 0.0
            else:
                # Scale utilization and standard deviation into percentage of capacity
                utilization = (measured / capacity) * 100.0
                std_utilization = (std_dev / capacity) * 100.0
            
            data.append({
                "Scenario": label_part.strip(),
                "Utilization (%)": utilization,
                "Std_Utilization": std_utilization,
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

    # Add data labels and error bars
    for i, p in enumerate(ax.patches):
        height = p.get_height()
        x_pos = p.get_x() + p.get_width() / 2.
        
        std_util = df.iloc[i]["Std_Utilization"]
        
        # Draw the error bar if a standard deviation was provided
        if std_util > 0:
            ax.errorbar(x_pos, height, yerr=std_util, fmt='none', c='black', capsize=8, linewidth=1)
            
    
        label_text = f"{height:.0f}%"
        
        # Shift the text label up so they don't overlap the bars
        text_y = height + std_util + 5 if std_util > 0 else height + 5
        
        ax.text(x_pos, 
                text_y, 
                label_text, 
                ha="center", va="bottom", fontsize=10, color='black')

    # Formatting
    plt.title(args.title)
    plt.ylabel("Uplink Utilization (%)")
    plt.xlabel("ACK Decimation Ratio")
    
    # Adjust y-axis limit to fit the labels
    max_total_height = (df["Utilization (%)"] + df["Std_Utilization"]).max()
    plt.ylim(0, max(120, max_total_height * 1.25))
    
    plt.legend(loc="upper right")
    plt.tight_layout()

    plt.savefig(args.output)
    print(f"Success! Plot saved to {args.output}")

if __name__ == "__main__":
    main()