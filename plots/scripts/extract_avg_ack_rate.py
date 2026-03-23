#!/usr/bin/env python3
import subprocess
import argparse
import sys
import os

def extract_avg_ack_rate(pcap_path, sender_ip, start_time=0.0, stop_time=0.0):
    # Check file path
    if not os.path.exists(pcap_path):
        print(f"Error: PCAP file not found!", file=sys.stderr)
        sys.exit(1)

    # tshark command to get timestamps and frame length
    tshark_cmd = [
        'tshark', '-r', '-',
        '-T', 'fields',
        '-e', 'frame.time_epoch',
        '-e', 'frame.len'
    ]

    if sender_ip:
        tshark_cmd.extend(['-Y', f'ip.src == {sender_ip}'])

    try:
        total_bytes = 0
        flow_start_time = None 
        measurement_start_time = None
        last_ts = None
        packet_count = 0

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
        
        # Extract loop
        while True:
            line = p2_tshark.stdout.readline()                
            if not line:
                break

            line = line.strip()
            
            try:
                parts = line.split()
                if len(parts) < 2:
                    continue

                ts = float(parts[0])
                length = int(parts[1])

                # Remember flow start time
                if flow_start_time is None:
                    flow_start_time = ts
                
                # Skip everything before measurement window
                if ts < (flow_start_time + start_time):
                    continue

                # Skip everything after measurement window
                if stop_time > 0 and ts > (flow_start_time + stop_time):
                    break

                # Start Measuring
                if measurement_start_time is None:
                    measurement_start_time = ts
                
                last_ts = ts
                total_bytes += length
                packet_count += 1
                
            except ValueError:
                continue
        
        _, stderr = p2_tshark.communicate()

        if packet_count <= 1 or measurement_start_time is None or last_ts is None:
            return 0

        duration = last_ts - measurement_start_time

        if duration <= 0:
            return 0


        # Calculate ACK rate in bps
        bps = (total_bytes * 8) / duration
        return int(bps)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 0

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pcap", required=True)
    parser.add_argument("--sender", required=True, help="Sender IP (e.g., Mission Control)")
    parser.add_argument("--start-time", type=float, default=0.0, help="Time to ignore at start of flow")
    parser.add_argument("--stop-time", type=float, default=0.0, help="Time to stop the calculation")
    args = parser.parse_args()

    # Resolve absolute path
    pcap_path = os.path.abspath(os.path.expanduser(args.pcap))
    
    rate_bps = extract_avg_ack_rate(pcap_path, args.sender, args.start_time, args.stop_time)
    
    print(f"{rate_bps}")

if __name__ == "__main__":
    main()