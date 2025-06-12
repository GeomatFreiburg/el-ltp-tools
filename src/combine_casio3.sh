#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Define input and output paths relative to the script location
INPUT_DIR="../../Data/CaSiO3_2"
OUTPUT_DIR="../../Data/CaSiO3_2_combined"

# Create absolute paths
INPUT_PATH="$(cd "$SCRIPT_DIR/$INPUT_DIR" && pwd)"
OUTPUT_PATH="$(cd "$SCRIPT_DIR/$OUTPUT_DIR" && pwd)"

# Set threshold value (comment out or set to empty to disable thresholding)
# Values above this threshold will be set to NaN
THRESHOLD=350

echo "Processing CaSiO3 data..."
echo "Input directory: $INPUT_PATH"
echo "Output directory: $OUTPUT_PATH"
if [ ! -z "$THRESHOLD" ]; then
    echo "Using threshold value: $THRESHOLD (values above threshold will be set to NaN)"
fi

# Run the Python script with the appropriate parameters
python3 "$SCRIPT_DIR/combine_data.py" \
    --input "$INPUT_PATH" \
    --output "$OUTPUT_PATH" \
    --start 2 \
    --end 97 \
    --base-filename "CaSiO3_" \
    --prefix "CaSiO3_2" \
    ${THRESHOLD:+--threshold $THRESHOLD}

echo "Done!" 