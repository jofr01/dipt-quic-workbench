#!/usr/bin/env python3
import argparse
import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

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
    parser = argparse.ArgumentParser(description="Generate Generic Heatmap from CSV.")
    
    parser.add_argument("--input", required=True, help="Path to summary CSV file")
    parser.add_argument("--output", default="heatmap.pdf", help="Output filename")
    parser.add_argument("--title", required=True, help="Plot Title")
    
    # Formatting
    parser.add_argument("--vmin", type=float, default=None)
    parser.add_argument("--vmax", type=float, default=None)
    parser.add_argument("--cmap", default="viridis")
    parser.add_argument("--cbarlabel", default="Value")
    parser.add_argument("--xlabel", default=None)
    parser.add_argument("--ylabel", default=None)
    parser.add_argument("--xticklabels", default=None, help="Comma-separated list of X-axis labels")
    parser.add_argument("--yticklabels", default=None, help="Comma-separated list of Y-axis labels")
    args = parser.parse_args()

    # Load csv data
    if not os.path.exists(args.input):
        print(f"Error: {args.input} not found")
        return

    df = pd.read_csv(args.input)
    pivot = df.pivot(index=df.columns[0], columns=df.columns[1], values=df.columns[2])

    # Sorting
    pivot = pivot.sort_index(ascending=False)
    pivot = pivot.sort_index(axis=1, ascending=True)

    # Process manual labels (if provided)
    y_labels = pivot.index
    if args.yticklabels:
        y_labels = [x.strip() for x in args.yticklabels.split(',')]
        
    x_labels = pivot.columns
    if args.xticklabels:
        x_labels = [x.strip() for x in args.xticklabels.split(',')]

    # Check for std annotations
    if len(df.columns) >= 4:
        # Extract the 4th column
        pivot_std = df.pivot(index=df.columns[0], columns=df.columns[1], values=df.columns[3])
        pivot_std = pivot_std.sort_index(ascending=False)
        pivot_std = pivot_std.sort_index(axis=1, ascending=True)
        
        # Create a array of strings for the annotations: "Mean ±Std"
        annot_matrix = np.empty_like(pivot, dtype=object)
        for i in range(pivot.shape[0]):
            for j in range(pivot.shape[1]):
                val = pivot.iloc[i, j]
                std = pivot_std.iloc[i, j]
                annot_matrix[i, j] = f"{val:.2f}\n±{std:.2f}"
                    
        annot_data = annot_matrix
        fmt = ""
        annot_size = 10
    else:
        # Fallback for 3 column CSVs (no std)
        annot_data = True
        fmt = ".2f"
        annot_size = 13

    # Plot
    plt.figure(figsize=(8, 6))
    sns.heatmap(
        pivot, 
        annot=annot_data, 
        fmt=fmt, 
        cmap=args.cmap,
        vmin=args.vmin, 
        vmax=args.vmax,
        linewidths=.5, 
        cbar_kws={'label': args.cbarlabel},
        yticklabels=y_labels,
        xticklabels=x_labels,
        annot_kws={"size": annot_size}
    )

    plt.title(args.title)
    if args.ylabel: 
        plt.ylabel(args.ylabel)
    if args.xlabel: 
        plt.xlabel(args.xlabel)
    plt.yticks(rotation=0)

    plt.tight_layout()
    plt.savefig(args.output)
    print(f"Success! Heatmap saved to {args.output}")

if __name__ == "__main__":
    main()