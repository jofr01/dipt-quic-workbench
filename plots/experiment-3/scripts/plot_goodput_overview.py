#!/usr/bin/env python3
import os
import re
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict

# add helper scripts to syspath
current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.join(current_dir, "../../scripts")
sys.path.append(scripts_dir)

import extract_fct
import calc_avg_goodput

# Configuration
LOGS_DIR = "../logs"
RESULTS_DIR = "../results"
SENDER_IP = "192.168.30.2"
FILE_SIZE_BYTES = 1000000000

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
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # Dictionary to hold raw values
    raw_data = defaultdict(list)
    pattern = re.compile(r'cca_(.*?)_loss_(\d+)_seed_(\d+)')
    
    print(f"Scanning {LOGS_DIR}...")
    subdirs = [f.path for f in os.scandir(LOGS_DIR) if f.is_dir()]

    for folder in subdirs:
        match = pattern.search(os.path.basename(folder))
        if match:
            cca = match.group(1).upper()
            loss_rate = int(match.group(2))
            
            pcap = os.path.join(folder, "MarsRover.pcap")
            if not os.path.exists(pcap):
                continue

            pcap_size_bytes = os.path.getsize(pcap)
            if pcap_size_bytes < FILE_SIZE_BYTES:
                print(f"Warning: PCAP too small ({pcap_size_bytes/1e6:.1f} MB) in {folder}. Transfer has been aborted. Setting goodput to 0.")
                raw_data[(cca, loss_rate)].append(0.0)
                continue
            
            # calc metrics
            fct = extract_fct.extract_fct(pcap, SENDER_IP)
            fct -= 120  # subtract handshake delay (only looking at steady state)
            val = calc_avg_goodput.calc_avg_goodput(fct, FILE_SIZE_BYTES)
            
            raw_data[(cca, loss_rate)].append(val)

    # Process grouped data to get mean and std
    plot_data = defaultdict(dict)
    for (cca, loss), vals in raw_data.items():
        mean_val = np.mean(vals)
        std_val = np.std(vals) if len(vals) > 1 else 0.0
        print(f"CCA {cca} / Loss {loss}%: Mean = {mean_val:.3f} Mbps, Std = {std_val:.3f} Mbps (over {len(vals)} runs)")
        
        plot_data[cca][loss] = (mean_val, std_val)


    # Plotting
    plt.figure(figsize=(8, 5))
    
    # Sort loss rates
    loss_rates = sorted(list(set(loss for _, loss in raw_data.keys())))

    # Space out points evenly
    x_positions = np.arange(len(loss_rates))
    
    colors = {"CUBIC": "tab:blue", "BBR": "tab:orange"}
    markers = {"CUBIC": "o", "BBR": "s"}
    
    for cca in plot_data:
        means = []
        stds = []
        for lr in loss_rates:
            mean, std = plot_data[cca].get(lr, (0, 0))
            means.append(mean)
            stds.append(std)
            
        # Plot with error bars
        plt.errorbar(x_positions, means, yerr=stds, label=cca, 
                     color=colors.get(cca, "black"), marker=markers.get(cca, "x"),
                     capsize=4, capthick=1.0, elinewidth=1.0, linewidth=1.2, markersize=6)

    # Formatting the plot
    plt.title("Goodput Comparison under Different Loss Rates (Averaged)")
    plt.xlabel("Packet Loss Rate (%)")
    plt.ylabel("Average Goodput (Mbps)")
    
    # Set X-ticks exactly to tested loss rates
    plt.xticks(x_positions, [f"{lr}" for lr in loss_rates])
    plt.ylim(bottom=0)
    plt.legend()
    
    plt.tight_layout()
    output_path = os.path.join(RESULTS_DIR, "goodput_overview.pdf")
    plt.savefig(output_path)
    print(f"Saved goodput plot to {output_path}")

if __name__ == "__main__":
    main()