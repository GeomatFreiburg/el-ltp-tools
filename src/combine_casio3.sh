#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Define input and output paths relative to the script location
INPUT_DIR="../../Data/CaSiO3_2"
OUTPUT_DIR="../../Data/CaSiO3_2_combined"

# Create absolute paths
INPUT_PATH="$(cd "$SCRIPT_DIR/$INPUT_DIR" && pwd)"
OUTPUT_PATH="$(cd "$SCRIPT_DIR/$OUTPUT_DIR" && pwd)"

# Set cosmic ray detection parameters
SIGMA=20.0  # Number of standard deviations above local mean
WINDOW_SIZE=10  # Size of the window for local statistics
ITERATIONS=6  # Number of iterations for cosmic ray detection

echo "Processing CaSiO3 data..."
echo "Input directory: $INPUT_PATH"
echo "Output directory: $OUTPUT_PATH"
echo "Using cosmic ray detection:"
echo "  - Sigma: $SIGMA (standard deviations above local mean)"
echo "  - Window size: $WINDOW_SIZE (pixels)"
echo "  - Iterations: $ITERATIONS"

# Run the Python script with the appropriate parameters
python3 "$SCRIPT_DIR/combine_data.py" \
    --input "$INPUT_PATH" \
    --output "$OUTPUT_PATH" \
    --start 2 \
    --end 97 \
    --base-filename "CaSiO3_" \
    --prefix "CaSiO3_2" \
    --sigma $SIGMA \
    --window-size $WINDOW_SIZE \
    --iterations $ITERATIONS

echo "Done!" 