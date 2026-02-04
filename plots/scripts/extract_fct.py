#!/usr/bin/env python3
import subprocess
import argparse
import sys
import os

def extract_fct(pcap_path, sender_ip):
    # Check file path
    if not os.path.exists(pcap_path):
        print(f"Error: PCAP file not found!", file=sys.stderr)
        sys.exit(1)


    # tshark command to get only timestamps
    tshark_cmd = [
        'tshark', '-r', '-',
        '-T', 'fields',
        '-e', 'frame.time_epoch'
    ]

    if sender_ip:
        print(f"Filter:  ip.src == {sender_ip}")
        tshark_cmd.extend(['-Y', f'ip.src == {sender_ip}'])

    try:
        packet_count = 0
        first_ts = None
        last_ts = None


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
        
        # Extracting first and last timestamp
        while True:
            line = p2_tshark.stdout.readline()                
            if not line:
                break

            line = line.strip()
            
            try:
                ts = float(line)
                if first_ts is None:
                    first_ts = ts
                last_ts = ts
                packet_count += 1
                
            except ValueError:
                continue
        
        _, stderr = p2_tshark.communicate()

        if packet_count == 0:
            print(f"Warning: 0 packets found.", file=sys.stderr)
            return None
        
        if packet_count == 1:
            return 0.0

        return last_ts - first_ts

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pcap", required=True)
    parser.add_argument("--sender", required=False)
    args = parser.parse_args()

    # Resolve absolute path
    pcap_path = os.path.abspath(os.path.expanduser(args.pcap))
    
    duration = extract_fct(pcap_path, args.sender)
    
    if duration is not None:
        print(f"{duration:.6f}")
        

if __name__ == "__main__":
    main()