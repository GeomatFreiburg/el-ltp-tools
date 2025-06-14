#!/bin/bash

# Example script demonstrating different ways to use the cosmic ray removal tool
# This script assumes you have some .tif files in a directory called 'data'

# Create output directory if it doesn't exist
mkdir -p processed

echo "Example 1: Basic usage with default parameters"
python -m el_ltp_tools.cosmic.script data/input.tif processed/output_default.tif

echo -e "\nExample 2: More sensitive detection (lower sigma, smaller window)"
python -m el_ltp_tools.cosmic.script data/input.tif processed/output_sensitive.tif \
    --sigma 3.0 \
    --window-size 3

echo -e "\nExample 3: More aggressive detection with more iterations"
python -m el_ltp_tools.cosmic.script data/input.tif processed/output_aggressive.tif \
    --iterations 5 \
    --min-intensity 100

echo -e "\nExample 4: Conservative detection for noisy images"
python -m el_ltp_tools.cosmic.script data/input.tif processed/output_conservative.tif \
    --sigma 7.0 \
    --window-size 7 \
    --iterations 2

echo -e "\nExample 5: Process multiple files in a loop"
for file in data/*.tif; do
    filename=$(basename "$file")
    echo "Processing $filename..."
    python -m el_ltp_tools.cosmic.script "$file" "processed/cleaned_${filename}"
done