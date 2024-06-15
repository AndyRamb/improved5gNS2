# Dynamic Resource Allocation and QoE-aware Packet Scheduling using HTB in OMNeT++
This Git repository is a fork of earlier research git repository and includes:
1. The Omnet++ Project for dynamic client admission and resource allocation scenarios.
2. Scripts for configuration generation for simulations used in the thesis (in the `algorithm` folder)
3. Configurations for Experiments run for the thesis "Dynamic Resource Allocation and QoE-aware Packet Scheduling using HTB in OMNeT++". (in `simulations` folder and its subfolders)

Requirements for Omnet++ simulation:
1. Omnet++ version 6.0.2 - download here: https://omnetpp.org/download/old
2. INET framework version 4.5.0 - download here: https://inet.omnetpp.org/Download.html
3. Python 3.10.12 - Tested with this version. Probably fine with other versions as well

Installation steps:
1. Download and Compile Omnet++ - follow the guide https://doc.omnetpp.org/omnetpp/InstallGuide.pdf
2. Download, and install the inet4.5 project within the omnet environment. 
3. Download, and install the git repository: "inet-gplus" project within the omnet environment. - https://github.com/AndyRamb/inet-gplus
4. Download, and install this git repository project within the omnet environment.
5. Make sure projects are linked, this project should have both inet-gplus and inet4.5 selected, inet-gplus only inet4.5 selected.
6. Build projects

Steps to make the simulations run:
1. Simulations and result gathering within the thesis is mainly run by ./exportHeatMaps.sh script.
  1. Make sure this script uses paths that make sense for your project. Analysis folder is currently a seperate disk you might want to change this to suit your needs.
  2. Generate and replace the simulation run command by manually copying the command in the graphical interface. (Some parameters is not needed, take a look at mine)
2. Generate a new sim configuration with genSimConfig.py, make sure the uncommented simulation is what you want.
  1. A manual or automated client admission can be set, see the examples of how to set hosts array.
3. Run the generated configName.txt in simulations folder with parallel -j <number of jobs in parallel> --ungroup -a <configName>.txt
