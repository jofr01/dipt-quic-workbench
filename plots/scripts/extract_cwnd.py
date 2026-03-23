#!/usr/bin/env python3
import json
import argparse
import sys
import os

def extract_qlog_data(qlog_path, output_csv):
    # Check file path
    if not os.path.exists(qlog_path):
        print(f"Error: QLOG file not found!", file=sys.stderr)
        sys.exit(1)

    print(f"Reading: {os.path.basename(qlog_path)}")

    try:
        update_count = 0
        start_time = None  # timestamp of first event

        with open(output_csv, 'w') as out_f:
            out_f.write("time,cwnd\n") # write csv header
            out_f.flush()

            # Open qlog file
            with open(qlog_path, 'r') as in_f:
                
                # Extracting congestion window and normalize timestamp
                while True:
                    line = in_f.readline()
                    if not line:
                        break
                    
                    # QLOG has a separator '\x1e' at the start of lines
                    line = line.strip('\x1e').strip()
                    if not line:
                        continue
                    
                    try:
                        record = json.loads(line)
                        
                        # Filter for metric updates
                        if record.get("name") != "recovery:metrics_updated":
                            continue
                            
                        data = record.get("data", {})
                        if "congestion_window" not in data:
                            continue

                        # Parse absolute timestamp (ms) and cwnd (bytes)
                        current_ts = float(record["time"])
                        cwnd = int(data["congestion_window"])
                        
                        # Set start_time if this is the first packet
                        if start_time is None:
                            start_time = current_ts
                        
                        # Calculate relative time (convert ms to seconds)
                        relative_ts = (current_ts - start_time) / 1000.0
                        
                        out_f.write(f"{relative_ts:.6f},{cwnd}\n")
                        update_count += 1
                        
                    except (ValueError, json.JSONDecodeError):
                        continue
            
        if update_count == 0:
            print(f"Warning: 0 cwnd updates matched filter.", file=sys.stderr)
        else:
            print(f"Success! Extracted {update_count} cwnd updates to {output_csv}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--qlog", required=True)
    parser.add_argument("--csv", required=True)
    args = parser.parse_args()

    # Resolve absolute path
    qlog_path = os.path.abspath(os.path.expanduser(args.qlog))
    
    extract_qlog_data(qlog_path, args.csv)

if __name__ == "__main__":
    main()