#!/usr/bin/env python3
import subprocess
import os
import sys
import pandas as pd
from scipy import stats

SENDER = "192.168.40.2"
LOG_DIR = "../logs/channel-characteristics/loss"
RATIOS = [1, 5, 10]
NUM_RUNS = 10

def count_packets(pcap_file):
    if not os.path.exists(pcap_file):
        print(f"Warning: File not found {pcap_file}")
        return 0
    
    tshark_cmd = [
        'tshark', '-r', '-',
        '-Y', f'ip.src == {SENDER}'
    ]
    
    try:
        # Start cat
        p1_cat = subprocess.Popen(['cat', pcap_file], stdout=subprocess.PIPE)
        
        # Start tshark
        p2_tshark = subprocess.Popen(
            tshark_cmd, 
            stdin=p1_cat.stdout, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        p1_cat.stdout.close()
        
        # Read the output
        stdout_data, stderr_data = p2_tshark.communicate()
        
        # Count non-empty lines (each line represents one packet)
        lines = [line for line in stdout_data.split('\n') if line.strip()]
        return len(lines)

    except Exception as e:
        print(f"Error processing {pcap_file}: {e}", file=sys.stderr)
        return 0

def main():
    data = []

    print("Extracting packet counts from pcap files")
    
    # Extract data
    for target in RATIOS:
        for run in range(1, NUM_RUNS + 1):
            server_pcap = os.path.join(LOG_DIR, str(target), f"run_{run}", "Server.pcap")
            client_pcap = os.path.join(LOG_DIR, str(target), f"run_{run}", "Client.pcap")
            
            sent = count_packets(server_pcap)
            received = count_packets(client_pcap)

            if sent == 0:
                print(f"Skipping Run {run} for {target}% (0 packets sent)")
                continue
                
            lost = sent - received
            obs_loss = (lost / sent) * 100.0

            print(f"Run {run} for {target}%: {sent} packets sent, {received} packets received, {obs_loss:.2f}% lost")
            
            data.append({
                'target_loss': target,
                'run': run,
                'sent': sent,
                'received': received,
                'observed_loss': obs_loss
            })

    # Convert to data frame
    df = pd.DataFrame(data)

    # Calculate statistics and print
    print("=" * 70)
    print("target_loss, mean_observed, std_dev, p_value")

    for target in RATIOS:
        # Filter data for this specific loss target
        group = df[df['target_loss'] == target]['observed_loss']
            
        mean = group.mean()
        std = group.std()
        
        # 1-Sample t-test
        t_stat, p_val = stats.ttest_1samp(group, target)
        print(target, mean, std, p_val)

if __name__ == "__main__":
    main()