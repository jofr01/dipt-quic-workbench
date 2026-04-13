# Simulations

In this folder you can find the simulation code.
Each experiment can consist of multiple scenarios.
Each scenario has it's own `run.sh` script to execute the simulation and copy the interesting traces to the [`/plots`](../plots) directory.
With the `run_all.sh` scripts all scenarios belonging to an experiment will be executed.
With the `run_everything` script, all experiments will be executed (might take a while).
Before executing anything ensure that enough storage (300 GB) and memory (min 8 GB) is available.

## Experiment 2: Challenges of Extreme Propagation Delay and High BDP
Here you can execute the terrestrial control scenarios of the second experiment.
On this branch we implemented a new PacketPacing logic to support higher bandwidths.
The results will be automatically copied to the correct folder.
Processing is done on the main branch.