#!/usr/bin/env python3
import subprocess
import argparse
import sys
import os

def extract_pcap_data(pcap_path, sender_ip, output_csv):
    # Check file path
    if not os.path.exists(pcap_path):
        print(f"Error: PCAP file not found!", file=sys.stderr)
        sys.exit(1)

    print(f"Reading: {os.path.basename(pcap_path)}")
    print(f"Filter:  ip.src == {sender_ip}")

    # tshark command
    tshark_cmd = [
        'tshark', '-r', '-', 
        '-Y', f'ip.src == {sender_ip}',
        '-T', 'fields',
        '-e', 'frame.time_epoch',
        '-e', 'frame.len',
        '-E', 'separator=,'
    ]

    try:
        packet_count = 0
        start_time = None  # timestamp of first packet

        with open(output_csv, 'w') as out_f:
            out_f.write("time,len\n") # write csv header
            out_f.flush()

            # Start cat
            p1_cat = subprocess.Popen(['cat', pcap_path], stdout=subprocess.PIPE)
            
            # Start tshark
            p2_tshark = subprocess.Popen(
                tshark_cmd, 
                stdin=p1_cat.stdout, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            p1_cat.stdout.close()
            
            # Extracting packet length and normalize timestamp
            while True:
                line = p2_tshark.stdout.readline()
                if not line:
                    break
                
                parts = line.strip().split(',')
                if len(parts) < 2:
                    continue
                
                try:
                    # Parse absolute timestamp and length
                    current_ts = float(parts[0])
                    length = parts[1]
                    
                    # Set start_time if this is the first packet
                    if start_time is None:
                        start_time = current_ts
                    
                    # Calculate relative time
                    relative_ts = current_ts - start_time
                    
                    out_f.write(f"{relative_ts:.6f},{length}\n")
                    packet_count += 1
                    
                except ValueError:
                    continue
            
            _, stderr = p2_tshark.communicate()

        if packet_count == 0:
            print(f"Warning: 0 packets matched filter 'ip.src == {sender_ip}'.", file=sys.stderr)
        else:
            print(f"Success! Extracted {packet_count} packets to {output_csv}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pcap", required=True)
    parser.add_argument("--csv", required=True)
    parser.add_argument("--sender", required=True)
    args = parser.parse_args()

    # Resolve absolute path
    pcap_path = os.path.abspath(os.path.expanduser(args.pcap))
    
    extract_pcap_data(pcap_path, args.sender, args.csv)

if __name__ == "__main__":
    main()