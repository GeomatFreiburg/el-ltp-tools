"""
Script for combining and processing measurement data from multiple folders.

This script processes and combines image data from multiple measurement folders,
typically used in electron microscopy or similar imaging experiments. It can handle multiple
image groups (e.g., center and side images) and includes cosmic ray detection and removal.

Expected folder structure:
    input_folder/
        g2/
            center_1.tif
            center_2.tif
            side_1.tif
            side_2.tif
        g3/
            center_1.tif
            center_2.tif
            side_1.tif
            side_2.tif
        ...

The output will be saved in the output directory with the following structure:
    output_folder/
        sample_prefix_center_combined.tif
        sample_prefix_side_combined.tif
        ...

Examples:
    # Basic usage with default settings:
    python script.py --input /path/to/input --output /path/to/output

    # Process specific folder range with custom prefix:
    python script.py --input /path/to/input --output /path/to/output -s 5 -e 20 -p my_sample

    # Adjust cosmic ray detection parameters:
    python script.py --input /path/to/input --output /path/to/output \
        --cosmic-sigma 7.0 --cosmic-window 15 --cosmic-iterations 4

    # Custom measurement configuration:
    python script.py --input /path/to/input --output /path/to/output \
        --config '[{"num_images": 3, "name": "center"}, {"num_images": 3, "name": "side"}]'

The script will:
1. Read images from the input directory
2. Apply cosmic ray detection and removal
3. Combine images according to the configuration
4. Save the processed images to the output directory
"""

import argparse
import os
from . import process_measurements


def parse_arguments():
    """Parse the arguments for the script.
    
    Returns:
        argparse.Namespace: Parsed command line arguments containing:
            - input: Input folder containing measurement data
            - output: Output folder for combined data
            - start: Starting folder index
            - end: Ending folder index
            - prefix: Prefix for output files
            - cosmic_sigma: Threshold for cosmic ray detection
            - cosmic_window: Window size for local statistics
            - cosmic_iterations: Number of cosmic ray detection iterations
            - cosmic_min: Minimum intensity threshold
            - config: JSON configuration for measurement groups
    """

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        required=True,
        help="Input folder containing the measurement data. This should be the base directory "
             "containing numbered subfolders with the measurement images. Each subfolder should "
             "contain the images to be combined according to the configuration."
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        required=True,
        help="Output folder where the combined and processed data will be saved. "
             "The script will create this directory if it doesn't exist. "
             "Combined images will be saved with names like: <prefix>_<group>_combined.tif"
    )
    parser.add_argument(
        "--config",
        type=str,
        default='[{"num_images": 2, "name": "center"}, {"num_images": 2, "name": "side"}]',
        help='JSON string defining the measurement configuration. Each group should have '
             '"num_images" (number of images to combine) and "name" (identifier for the group). '
             'Default configuration processes 2 center images and 2 side images. '
             'Example: [{"num_images": 2, "name": "center"}, {"num_images": 2, "name": "side"}]'
    )
    parser.add_argument(
        "--start", "-s", 
        type=int, 
        default=1, 
        help="Starting folder index (default: 1). The script will process folders "
             "starting from this number up to the end index. Folders should be named "
             "like 'g2', 'g3', etc."
    )
    parser.add_argument(
        "--end", "-e", 
        type=int, 
        default=100, 
        help="Ending folder index (default: 100). The script will process folders "
             "up to and including this number. Folders should be named like 'g2', 'g3', etc."
    )
    parser.add_argument(
        "--prefix",
        "-p",
        type=str,
        default="",
        help="Prefix for output files (default: ''). This prefix will be used "
             "for naming the combined output files. Example: if prefix is 'sample' and "
             "group is 'center', output will be 'sample_center_combined_0001.tif'"
    )
    parser.add_argument(
        "--cosmic-sigma",
        type=float,
        default=6.0,
        help="Number of standard deviations above local mean to consider a pixel as cosmic ray "
             "(default: 6.0). Higher values make the detection more conservative. "
             "Recommended range: 5.0-8.0"
    )
    parser.add_argument(
        "--cosmic-window",
        type=int,
        default=10,
        help="Size of the window for local statistics (default: 10). This defines the "
             "neighborhood size used for calculating local mean and standard deviation "
             "in cosmic ray detection. Should be odd number, recommended range: 5-15"
    )
    parser.add_argument(
        "--cosmic-iterations",
        type=int,
        default=3,
        help="Number of iterations for cosmic ray detection (default: 3). More iterations "
             "may catch additional cosmic rays but increase processing time. "
             "Recommended range: 2-5"
    )
    parser.add_argument(
        "--cosmic-min",
        type=float,
        default=50.0,
        help="Minimum intensity threshold for cosmic ray detection (default: 50.0). "
             "Pixels below this intensity will not be considered as cosmic rays. "
             "Adjust based on your image intensity range"
    )
    return parser.parse_args()


def main():
    """Main entry point for the script."""
    args = parse_arguments()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    # Process the measurements
    process_measurements(
        input_directory=args.input,
        output_directory=args.output,
        config=args.config,
        start_index=args.start,
        end_index=args.end,
        cosmic_sigma=args.cosmic_sigma,
        cosmic_window=args.cosmic_window,
        cosmic_iterations=args.cosmic_iterations,
        cosmic_min=args.cosmic_min,
        prefix=args.prefix
    )
    
    print(f"Processing complete! Combined images have been saved to: {args.output}")


if __name__ == "__main__":
    main()
