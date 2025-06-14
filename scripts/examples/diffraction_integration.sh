#!/bin/bash

# Example script demonstrating how to use the diffraction integration tool
# This script shows two ways to integrate diffraction data from multiple detector positions

# Example 1: Using individual detector arguments
echo "Example 1: Using individual detector arguments"
el-ltp-integrate-multi \
    --input-dir /path/to/input/images \
    --output-dir /path/to/output \
    --detector center /path/to/center.poni /path/to/center.mask \
    --detector side /path/to/side.poni /path/to/side.mask

# Example 2: Using JSON string
echo -e "\nExample 2: Using JSON string"
el-ltp-integrate-multi \
    --input-dir /path/to/input/images \
    --output-dir /path/to/output \
    --config-json '{"center":{"calibration":"/path/to/center.poni","mask":"/path/to/center.mask"},"side":{"calibration":"/path/to/side.poni","mask":"/path/to/side.mask"}}'

# Note: Before running, make sure to:
# 1. Replace the paths with your actual calibration and mask file paths
# 2. Place your input diffraction images in the input directory
# 3. Create the output directory if it doesn't exist 