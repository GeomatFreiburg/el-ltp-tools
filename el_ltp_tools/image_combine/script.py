"""
Script for combining and processing measurement data from multiple folders.

This script is designed to process and combine image data from multiple measurement folders,
typically used in electron microscopy or similar imaging experiments. It can handle multiple
image groups (e.g., center and side images) and includes cosmic ray detection and removal.

The script processes images in sequence from a specified range of folders, combining them
according to the provided configuration. It supports cosmic ray detection and removal
using local statistics and intensity thresholds.

Typical folder structure:
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

Usage Examples:
    1. Basic usage with default settings:
        python -m el_ltp_tools.image_combine.script -i /path/to/input -o /path/to/output

    2. Process specific folder range with custom prefix:
        python -m el_ltp_tools.image_combine.script -i /path/to/input -o /path/to/output -s 5 -e 20 -p my_sample

    3. Adjust cosmic ray detection parameters:
        python -m el_ltp_tools.image_combine.script -i /path/to/input -o /path/to/output \
            --cosmic-sigma 7.0 --cosmic-window 15 --cosmic-iterations 4

    4. Custom measurement configuration:
        python -m el_ltp_tools.image_combine.script -i /path/to/input -o /path/to/output \
            --config '[{"num_images": 3, "name": "center"}, {"num_images": 3, "name": "side"}]'

Output:
    The script will create combined images in the output folder with names like:
        my_sample_center_combined.tif
        my_sample_side_combined.tif

    Each combined image is the result of averaging the corresponding images from all
    processed folders, with cosmic ray removal applied during the process.
"""

import argparse
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
        description="Combine measurement data from multiple folders."
    )
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        required=True,
        help="Input folder containing the measurement data. This should be the base directory "
             "containing numbered subfolders with the measurement images.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        required=True,
        help="Output folder where the combined and processed data will be saved. "
             "The script will create this directory if it doesn't exist.",
    )
    parser.add_argument(
        "--start", "-s", 
        type=int, 
        default=1, 
        help="Starting folder index (default: 1). The script will process folders "
             "starting from this number up to the end index."
    )
    parser.add_argument(
        "--end", "-e", 
        type=int, 
        default=100, 
        help="Ending folder index (default: 100). The script will process folders "
             "up to and including this number."
    )
    parser.add_argument(
        "--prefix",
        "-p",
        type=str,
        default="",
        help="Prefix for output files (default: ''). This prefix will be used "
             "for naming the combined output files.",
    )
    parser.add_argument(
        "--cosmic-sigma",
        type=float,
        default=6.0,
        help="Number of standard deviations above local mean to consider a pixel as cosmic ray "
             "(default: 6.0). Higher values make the detection more conservative.",
    )
    parser.add_argument(
        "--cosmic-window",
        type=int,
        default=10,
        help="Size of the window for local statistics (default: 10). This defines the "
             "neighborhood size used for calculating local mean and standard deviation "
             "in cosmic ray detection.",
    )
    parser.add_argument(
        "--cosmic-iterations",
        type=int,
        default=3,
        help="Number of iterations for cosmic ray detection (default: 3). More iterations "
             "may catch additional cosmic rays but increase processing time.",
    )
    parser.add_argument(
        "--cosmic-min",
        type=float,
        default=50.0,
        help="Minimum intensity threshold for cosmic ray detection (default: 50.0). "
             "Pixels below this intensity will not be considered as cosmic rays.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default='[{"num_images": 2, "name": "center"}, {"num_images": 2, "name": "side"}]',
        help='JSON string defining the measurement configuration. Each group should have '
             '"num_images" (number of images to combine) and "name" (identifier for the group). '
             'Default configuration processes 2 center images and 2 side images. '
             'Example: [{"num_images": 2, "name": "center"}, {"num_images": 2, "name": "side"}]',
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    process_measurements(args)
