#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Define input and output paths relative to the script location
INPUT_DIR="../../data/2024-10-15_CaSiO3"
OUTPUT_DIR="../../data/2024-10-15_CaSiO3_combined"

# Create absolute paths
INPUT_PATH="$(cd "$SCRIPT_DIR/$INPUT_DIR" && pwd)"
OUTPUT_PATH="$(cd "$SCRIPT_DIR/$OUTPUT_DIR" && pwd)"

# Set cosmic ray detection parameters
COSMIC_SIGMA=6.0  # Number of standard deviations above local mean
COSMIC_WINDOW=10  # Size of the window for local statistics
COSMIC_ITERATIONS=3  # Number of iterations for cosmic ray detection
COSMIC_MIN=50.0  # Minimum intensity threshold for cosmic ray detectiondd

echo "Processing CaSiO3 data..."
echo "Input directory: $INPUT_PATH"
echo "Output directory: $OUTPUT_PATH"
echo "Cosmic ray detection parameters:"
echo "  Sigma: $COSMIC_SIGMA"
echo "  Window size: $COSMIC_WINDOW"
echo "  Iterations: $COSMIC_ITERATIONS"
echo "  Minimum intensity: $COSMIC_MIN"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_PATH"

# Run the Python script with the appropriate parameters
python3 "$SCRIPT_DIR/combine_data.py" \
    --input "$INPUT_PATH" \
    --output "$OUTPUT_PATH" \
    --start 2 \
    --end 97 \
    --base-filename "CaSiO3_" \
    --prefix "CaSiO3_2" \
    --cosmic-sigma "$COSMIC_SIGMA" \
    --cosmic-window "$COSMIC_WINDOW" \
    --cosmic-iterations "$COSMIC_ITERATIONS" \
    --cosmic-min "$COSMIC_MIN"

echo "Processing complete!" 