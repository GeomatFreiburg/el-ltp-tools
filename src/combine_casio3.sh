#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

# Set input and output directories using absolute paths
INPUT_DIR="$PROJECT_ROOT/Data/CaSiO3_2"
OUTPUT_DIR="$PROJECT_ROOT/Data/CaSiO3_2_combined"

# Set cosmic ray detection parameters
COSMIC_SIGMA=6.0  # Number of standard deviations above local mean
COSMIC_WINDOW=10  # Size of the window for local statistics
COSMIC_ITERATIONS=3  # Number of iterations for cosmic ray detection
COSMIC_MIN=50.0  # Minimum intensity threshold for cosmic ray detection

# Set measurement configuration
CONFIG='[{"num_images": 2, "name": "center"}, {"num_images": 2, "name": "side"}]'

echo "Processing CaSiO3 data..."
echo "Input directory: $INPUT_DIR"
echo "Output directory: $OUTPUT_DIR"
echo "Cosmic ray detection parameters:"
echo "  Sigma: $COSMIC_SIGMA"
echo "  Window size: $COSMIC_WINDOW"
echo "  Iterations: $COSMIC_ITERATIONS"
echo "  Minimum intensity: $COSMIC_MIN"
echo "Measurement configuration: $CONFIG"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Run the Python script
python "$SCRIPT_DIR/combine_data.py" \
    --input "$INPUT_DIR" \
    --output "$OUTPUT_DIR" \
    --start 2 \
    --end 97 \
    --prefix "CaSiO3_2" \
    --cosmic-sigma "$COSMIC_SIGMA" \
    --cosmic-window "$COSMIC_WINDOW" \
    --cosmic-iterations "$COSMIC_ITERATIONS" \
    --cosmic-min "$COSMIC_MIN" \
    --config "$CONFIG"

echo "Processing complete!"