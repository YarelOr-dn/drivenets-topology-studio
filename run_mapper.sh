#!/bin/bash
# Network Topology Mapper Runner
# Usage: ./run_mapper.sh <PE_IP> [output_dir]
#
# Example:
#   ./run_mapper.sh 100.64.0.220
#   ./run_mapper.sh 100.64.0.210 /tmp/reports

PE_IP="${1:-100.64.0.220}"
OUTPUT_DIR="${2:-reports}"

echo "========================================"
echo "Network Topology Mapper"
echo "Device: $PE_IP"
echo "Output: $OUTPUT_DIR"
echo "========================================"
echo ""
echo "Note: Interface discovery takes 60-120 seconds on large devices."
echo "Please be patient..."
echo ""

cd /home/dn/CURSOR
python3 -u -m network_mapper.mapper "$PE_IP" -o "$OUTPUT_DIR"

echo ""
echo "Done! Check $OUTPUT_DIR for the report."











