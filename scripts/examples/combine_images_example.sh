#!/bin/bash

# Example script demonstrating how to use the image combination tool
# This script shows how to combine and process measurement data from multiple folders
# with cosmic ray detection and removal.

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Set input and output directories using absolute paths
INPUT_DIR="/home/clemens/Dropbox/Beamtimes/2024-10 DESY LTP-EL/Data/CaSiO3_2"
OUTPUT_DIR="/home/clemens/Dropbox/Beamtimes/2024-10 DESY LTP-EL/Data/CaSiO3_2_combined"

# Set start and end indices for the measurements
START_INDEX=2
END_INDEX=97

# Set the prefix for the output files
OUTPUT_FILE_PREFIX="CaSiO3_2"

# Set cosmic ray detection parameters
# These parameters control how aggressively cosmic rays are detected and removed:
# - sigma: Number of standard deviations above local mean (higher = more conservative)
# - window: Size of neighborhood for local statistics
# - iterations: Number of detection passes
# - min: Minimum intensity threshold for cosmic ray detection
COSMIC_SIGMA=6.0
COSMIC_WINDOW=10
COSMIC_ITERATIONS=3
COSMIC_MIN=50.0

# Set measurement configuration
# This JSON string defines how images should be grouped and combined
# The configuration is a list containing a single object that maps measurement names
# to their number of directories to combine
# Example: [{"center": 2, "side": 2}] means:
#   - Combine 2 directories for the "center" measurement
#   - Combine 2 directories for the "side" measurement
CONFIG_JSON='[{"center": 2, "side": 2}]'



########################################################
# Run the script
########################################################

echo "Processing CaSiO3 data..."
echo "Input directory: $INPUT_DIR"
echo "Output directory: $OUTPUT_DIR"
echo "Cosmic ray detection parameters:"
echo "  Sigma: $COSMIC_SIGMA (standard deviations above local mean)"
echo "  Window size: $COSMIC_WINDOW (pixels for local statistics)"
echo "  Iterations: $COSMIC_ITERATIONS (detection passes)"
echo "  Minimum intensity: $COSMIC_MIN (threshold for detection)"
echo "Measurement configuration: $CONFIG_JSON"
echo "Start index: $START_INDEX"
echo "End index: $END_INDEX"
echo "Output file prefix: $OUTPUT_FILE_PREFIX"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Run the el-ltp-combine-images command
# Parameters:
#   --input: Base directory containing numbered subfolders with measurement images
#   --output: Directory for combined and processed data
#   --start: Starting folder index (inclusive)
#   --end: Ending folder index (inclusive)
#   --prefix: Prefix for output files
#   --cosmic-sigma: Threshold for cosmic ray detection
#   --cosmic-window: Window size for local statistics
#   --cosmic-iterations: Number of detection passes
#   --cosmic-min: Minimum intensity threshold
#   --config-json: JSON configuration for measurement groups
el-ltp-combine-images \
    --input "$INPUT_DIR" \
    --output "$OUTPUT_DIR" \
    --start "$START_INDEX" \
    --end "$END_INDEX" \
    --prefix "$OUTPUT_FILE_PREFIX" \
    --cosmic-sigma "$COSMIC_SIGMA" \
    --cosmic-window "$COSMIC_WINDOW" \
    --cosmic-iterations "$COSMIC_ITERATIONS" \
    --cosmic-min "$COSMIC_MIN" \
    --config-json "$CONFIG_JSON"

echo "Processing complete!"
echo "Combined images have been saved to: $OUTPUT_DIR"
echo "Output files will be named like: CaSiO3_2_center_combined.tif, CaSiO3_2_side_combined.tif"