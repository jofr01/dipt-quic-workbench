# Plots

The scripts in this folder are used to generate the plots for this thesis.
Therefore, the pcaps and qlog files from QUIC Workbench simulations have to be placed in the respective folders.
Executing the simulations using the run scripts will automatically update the traces.

## Requirements

To process the simulation traces and generate the plots, your system must have the following tools installed:

* **tshark** - version 4.4.9 (Used to extract raw packet metrics from `.pcap` files)
* **jq** - version 1.8.1 (Used for command-line parsing of JSON data)
* **Python** - version 3.13

### Installing System Tools
```bash
sudo apt-get update
sudo apt-get install tshark jq
```
### Installing Python Dependencies
The data processing and plotting scripts rely on a few Python packages.
You can install the exact versions used in this thesis via the provided requirements.txt file:
```bash
pip install -r requirements.txt
```

## Scripts

In the `/scripts` folder you can find generalized processing scripts to extract the different metrics.
These scripts are designed to be universal and will be called with the appropriate flags to process data of a specific experiment.
Centralizing them removes redundancies and ensures that the same techniques are applied consistently.

### 1. `extract_throughput.py`
**Purpose:** Extracts raw packet timestamps and lengths from a PCAP file into a CSV format  
**Method:** Uses a `cat | tshark` pipe to read files safely without permission errors  
**Usage:**
```bash
python3 extract_throughput.py \
    --pcap <file.pcap> \
    --sender <IP> \
    --csv <output.csv>
```

### 2. `plot_timeseries.py`
**Purpose:** Generates timeseries plots from one or more CSV files (Throughput or CWND)  
**Method:** Auto-detects data type (packet len vs cwnd) to switch between throughput calculation (sum + Mbps conversion) and raw value averaging  
**Usage:**
```bash
python3 plot_timeseries.py \
    --input <Run 1=data1.csv> \
    --input <Run 2=data2.csv> \
    --ylabel "CWND (MB) or Throughput (Mbps)" \
    --capacity <reference line position (Mbps)> \
    --xlim <x-axis limit (seconds)> \
    --title <title> \
    --output <plot.pdf>
```

### 3. `protocol_overhead_ratio.py`
**Purpose:** Calculates the Protocol Overhead Ratio (Total Bytes Sent / Payload Size)  
**Method:** Acts as a wrapper around `extract_throughput.py`, sums up extracted data and divides it by the payload size  
**Usage:**
```bash
python3 protocol_overhead_ratio.py \
    --pcap <file.pcap> \
    --sender <IP> \
    --filesize <bytes>
```

### 4. `plot_data_transfered.py`
**Purpose:** Plots the culumative bytes of data transfered over time    
**Method:** Sums up data cumulative, supports multiple traces, and applies consistent styling  
**Usage:**
```bash
python3 plot_data_transfered.py \
    --input <Run 1=data1.csv> \
    --input <Run 2=data2.csv> \
    --xlim <x-axis limit (seconds)> \
    --title <title> \
    --output <plot.pdf>
```

### 5. `extract_fct.py`
**Purpose:** Extracts the flow completion time   
**Method:** Reads pcap and substracts last minus first packet timestamp  
**Usage:**
```bash
python3 extract_fct.py \
    --pcap <file.pcap> \
    --sender <IP>
```

### 6. `calc_avg_goodput.py`
**Purpose:** Calculates average goodput in Mbps  
**Method:** Simple division of filesize by flow completion time and conversion in Mbps  
**Usage:**
```bash
python3 calc_avg_goodput.py \
    --fct <Flow Completion Time (seconds)> \
    --filesize <File Size (bytes)>
```

### 7. `plot_heatmap.py`
**Purpose:** Generates a heatmap graph based on a csv  
**Method:** Takes a CSV with at least 3 columns: Row, Column, Value
- Automatically sorts rows (descending) and columns (ascending)
- Supports manual axis label overrides
- Scales can be clamped to ensure consistency across multiple plots

**Usage:**
```bash
python3 plot_heatmap.py \
    --input <data.csv> \
    --title <title> \
    --output <heatmap.pdf>
    --vmin <0> --vmax <2.0> \
    --yticklabels <Label A,Label B> \
    --xticklabels <Label 1,Label 2>
```

### 8. `extract_avg_ack_rate.py`
**Purpose:** Calculates the average ACK rate  
**Method:** Calculates the total packet length sum over the duration of the flow, optionally define time window to use  
**Usage:**
```bash
python3 extract_avg_ack_rate.py \
    --pcap <file.pcap> \
    --sender <IP> \
    --start-time <Start calc window (seconds)> \
    --stop-time <Stop calc window (seconds)>
```

### 9. `plot_saturation.py`
**Purpose:** Visualizes uplink saturation levels across different scenarios  
**Method:** Takes "Measured Rate" vs "Link Capacity" pairs as input, calculates utilization percentage, and renders a bar chart.
It highlights overloaded scenarios (Utilization > 100%) in red and safe scenarios in green.  
**Usage:**
```bash
python3 plot_saturation.py \
    --output <plot.pdf> \
    --title <Title> \
    --input <Label=Measured:Capacity[:StdDev]> \
    --input <Scenario B=21000:25000:120>
```

### 10. `extract_cwnd.py`
**Purpose:** Extracts congestion window updates from a QLOG trace file into a CSV format  
**Method:** Parses JSON-SEQ records for `recovery:metrics_updated` events and normalizes timestamps relative to the start  
**Usage:**
```bash
python3 extract_cwnd.py \
    --qlog <file.qlog> \
    --csv <output.csv>
```

### 11. `plot_barchart.py`
**Purpose:** Generates bar charts from provided data points (Label=Value pairs) 
**Method:** Parses command-line inputs and renders a bar chart, appending exact value labels to the top of each bar.
**Usage:**
```bash
python3 plot_barchart.py \
    --input <"Scenario 1=5812"> \
    --input <"Scenario 2=4782"> \
    --title "Flow Completion Time" \
    --ylabel "Completion Time (Seconds)" \
    --xlabel "Configuration" \
    --output <barchart.pdf>
```

### 12. `extract_rtt.py`
**Purpose:** Extracts RTT measurement updates from a QLOG trace file into a CSV format  
**Method:** Parses JSON-SEQ records for `recovery:metrics_updated` events and normalizes timestamps relative to the start  
**Usage:**
```bash
python3 extract_rtt.py \
    --qlog <file.qlog> \
    --csv <output.csv>
```


## Verification and Validation
To reproduce the results, run the QUIC Interop Runner and copy the left nodes pcaps from the log folder generated by the "validation" test case to the folder `/logs/queue-dynamics/ns-3`.
All other files can be created running the script under `/simulation/verification-validation/run_all.sh`.

The script `plot_channel_verification.sh` plots the throughput measurement of a simple workbench simulation.  
The script `verify_loss.py` calculates the observed loss and compares it to the configured loss ratio, using t-test methodology.  
The script `plot_validation_comparison.sh` plots the throughput of the workbench compared to the ns-3 reference emulation.  


## Experiment 1: Baseline Feasibility
This experiment doesn't need a lot of plots, because we are mainly interested in general functionality of the protocol, which can be checked by analyzing the traces in wireshark.

To calculate the protocol overhead caused by spurius retransmission the script `print_overhead.sh` is used.
To generate the staircase plot showcasing flow control limitation the `plot_flow_control_graph.py` is used.  


## Experiment 2: High BDP Challenge
This experiment evaluates the performance of different congestion controllers in the extreme LFN scenario we find in deep space.  

First, we run a baseline comparison of CUBIC, NewReno, BBRv1 and BBRv3.
The results of those runs can be plotted with the `plot_baseline_cwnd_comparison.py` and `plot_baseline_throughput_comparison.py` scripts.

Second, we run a control scenario with same BDP, but low latency with CUBIC, NewReno and BBRv1.
The results of those runs can be plotted with the `plot_control_cwnd_comparison.py` and `plot_control_throughput_comparison.py` scripts.

After that, we tests if tuning the initial window to the real BDP size can help improving the performance.
These tests are conducted using CUBIC.
The results can be plotted using the scripts `plot_cubic_init_window_tuning_cwnd.py` and `plot_cubic_init_window_tuning_fct.py`.  


## Experiment 3: Resilience to Packet Loss
This experiment evaluates the performance under random loss.
We compare BBRv1 and CUBIC over 10 indepent runs for each configuration.  

The script `plot_goodput_overview.py` calculates the averaged goodput for each scenario, averaged over all runs and plots it in a line chart with error bars indicating the standard deviation.
The scripts `plot_cwnd_comparison.py` and `plot_throughput_comparison.py` generate plots showing the timeseries dynamics of the simulations.  


## Experiment 4: Link Asymmetry
The objective of this experiment is to quantify the performance degradation of QUIC due to severe channel asymmetry.

`plot_heatmaps.py` generates heatmaps that are summarizing the performance for all combinations of uplink bandwidth and ACK ratio.
`plot_reverse_path_saturation.py` generates bar charts that show the saturation of the uplink for all scenarios.
A saturation above 100% indicates that there is ACK congestion.
For all scenarios with loss we averaged the results over 5 indepent runs and show the mean and standard deviation.  

`plot_throughput_comparison.py` generates timeseries throughput plots to allow analysis of the dynamical behavior of the endpoints.  