#!/usr/bin/env python3
import argparse
import sys
import os
import subprocess
import tempfile
import pandas as pd

def main():
    parser = argparse.ArgumentParser(description="Calculate Protocol Overhead Ratio.")
    parser.add_argument("--pcap", required=True, help="Path to the .pcap file")
    parser.add_argument("--sender", required=True, help="IP address of the sender")
    parser.add_argument("--filesize", type=int, required=True, help="Size of the transferred file in bytes")
    
    args = parser.parse_args()

    # Locate the extract_throughput.py script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    extract_script = os.path.join(script_dir, "extract_throughput.py")

    if not os.path.exists(extract_script):
        print(f"Error: Could not find '{extract_script}'.", file=sys.stderr)
        sys.exit(1)

    # Create a temporary file for the CSV data
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        temp_csv_path = tmp.name

    try:
        # Call extract_throughput.py via subprocess
        print(f"Extracting data using {os.path.basename(extract_script)} ---")
        cmd = [
            sys.executable, extract_script,
            "--pcap", args.pcap,
            "--sender", args.sender,
            "--csv", temp_csv_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Extraction failed:\n{result.stderr}", file=sys.stderr)
            sys.exit(1)

        # Load data in df
        df = pd.read_csv(temp_csv_path)
        
        if df.empty:
            print(f"Warning: No packets found for sender {args.sender}.")
            return

        # Calculate Metrics
        total_sent = df['len'].sum()
        ratio = total_sent / args.filesize
        percentage = (ratio - 1) * 100

        print(f"--- Results ---")
        print(f"Total Bytes Sent:       {total_sent:,} bytes")
        print(f"Application Payload:    {args.filesize:,} bytes")
        print(f"Protocol Overhead Ratio: {ratio:.4f}")
        print(f"Inefficiency Overhead:   {percentage:.2f}%")

    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
    finally:
        # Cleanup
        if os.path.exists(temp_csv_path):
            os.remove(temp_csv_path)

if __name__ == "__main__":
    main()