#!/usr/bin/env python3
import argparse

def calc_avg_goodput(fct, filesize):
    if fct <= 0:
        return 0.0
    
    # Calculation => Mbps
    return (filesize * 8) / fct / 1_000_000.0



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fct", type=float, required=True)
    parser.add_argument("--filesize", type=int, required=True)
    
    args = parser.parse_args()

    mbps = calc_avg_goodput(args.fct, args.filesize)
    
    print(f"{mbps:.4f}")

if __name__ == "__main__":
    main()