#!/usr/bin/env python3

import argparse
import numpy as np
from PIL import Image
import fabio
from el_ltp_tools.cosmic import detect_cosmic_rays_multiple_iterations


def main():
    parser = argparse.ArgumentParser(
        description="""Remove cosmic rays from scientific images using iterative detection.

This tool uses a statistical approach to identify and remove cosmic ray artifacts from scientific images.
It works by:
1. Analyzing local pixel neighborhoods to compute mean and standard deviation
2. Identifying pixels that deviate significantly from their local statistics
3. Iteratively refining the detection to catch both strong and weak cosmic rays
4. Replacing detected cosmic ray pixels with NaN values

The detection is based on the following criteria:
- Pixels must be above a minimum intensity threshold
- Pixels must deviate from their local mean by more than sigma standard deviations
- The detection is performed multiple times to catch both strong and weak cosmic rays

Example usage:
    # Basic usage with default parameters
    el-ltp-remove-cosmic input.tif output.tif

    # More sensitive detection (lower sigma, smaller window)
    el-ltp-remove-cosmic input.tif output.tif --sigma 3.0 --window-size 3

    # More aggressive detection with more iterations
    el-ltp-remove-cosmic input.tif output.tif --iterations 5 --min-intensity 100

    # Conservative detection for noisy images
    el-ltp-remove-cosmic input.tif output.tif --sigma 7.0 --window-size 7 --iterations 2

Note: The output image will have NaN values where cosmic rays were detected.
These can be further processed or interpolated as needed.""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "input_file",
        type=str,
        help="Path to the input image file (tiff/tif)",
    )
    parser.add_argument(
        "output_file",
        type=str,
        help="Path to save the processed image",
    )
    parser.add_argument(
        "--sigma",
        type=float,
        default=5.0,
        help="""Number of standard deviations above local mean to consider as cosmic ray.
Higher values (e.g., 7.0) are more conservative, lower values (e.g., 3.0) are more aggressive.
Default: 5.0""",
    )
    parser.add_argument(
        "--window-size",
        type=int,
        default=5,
        help="""Size of local neighborhood window for statistics.
Must be an odd number. Larger windows (e.g., 7) are better for noisy images,
smaller windows (e.g., 3) are better for sharp features.
Default: 5""",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=3,
        help="""Number of iterations for cosmic ray detection.
More iterations can catch weaker cosmic rays but may also affect real features.
Recommended range: 2-5. Default: 3""",
    )
    parser.add_argument(
        "--min-intensity",
        type=float,
        default=0.0,
        help="""Minimum pixel intensity threshold for cosmic ray detection.
Only pixels above this value will be considered as potential cosmic rays.
Useful for ignoring dark regions or noise floor. Default: 0.0""",
    )

    args = parser.parse_args()

    # Read input image
    try:
        img = fabio.open(args.input_file)
        data = img.data.astype(np.float64)
    except Exception as e:
        print(f"Error reading input file: {e}")
        return

    # Detect cosmic rays
    cosmic_mask = detect_cosmic_rays_multiple_iterations(
        data,
        sigma=args.sigma,
        window_size=args.window_size,
        iterations=args.iterations,
        min_intensity=args.min_intensity,
    )

    # Replace cosmic ray pixels with NaN
    data[cosmic_mask] = np.nan

    # Save the processed image
    try:
        Image.fromarray(data).save(args.output_file)
        print(f"Processed image saved to: {args.output_file}")
        print(f"Number of cosmic ray pixels detected: {np.sum(cosmic_mask)}")
    except Exception as e:
        print(f"Error saving output file: {e}")


if __name__ == "__main__":
    main() 