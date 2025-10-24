import argparse
import os
import json
import matplotlib.pyplot as plt
from typing import Dict
from el_ltp_tools.diffraction import DetectorConfig, integrate_multi


def parse_args():
    parser = argparse.ArgumentParser(
        description="""
Integrate diffraction data from multiple detector positions.

This script processes diffraction images from multiple detector positions and integrates them
into a single pattern. It supports both individual detector configurations via command line
arguments and a JSON configuration file.

It expects the input images to be named like this:
    <file_prefix>_<detector_name>_<pattern_number>.tif

An example for the input directory is:
    /path/to/images/
    |-- CaSiO3_2_detector1_00001.tif
    |-- CaSiO3_2_detector1_00002.tif
    |-- CaSiO3_2_detector2_00001.tif
    |-- CaSiO3_2_detector2_00002.tif
    ...

The output will be saved in the output directory with the following structure:
    /path/to/output/
    |-- CaSiO3_2_00001.xy
    |-- CaSiO3_2_00002.xy
    ...

Examples:
    # Using individual detector configurations:
    el-ltp-integrate-multi --input-dir /path/to/images --output-dir /path/to/output \\
        --detector detector1 calibration1.json mask1.npy \\
        --detector detector2 calibration2.json mask2.npy

    # Using JSON configuration:
    el-ltp-integrate-multi --input-dir /path/to/images --output-dir /path/to/output \\
        --config-json '{"detector1": {"calibration": "cal1.json", "mask": "mask1.npy"}}'

The script will:
1. Read diffraction images from the input directory
2. Apply calibrations and masks for each detector
3. Integrate the patterns
4. Save the results to the output directory
5. Display a plot of the integrated patterns
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--input-dir",
        required=True,
        help="Directory containing the input diffraction images. Should contain image files "
        "that can be read by the detector configuration.",
    )

    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory where integrated patterns will be saved. Will be created if it "
        "doesn't exist. Output files will be saved in this directory with pattern "
        "numbers as filenames.",
    )

    # Add arguments for each detector position
    parser.add_argument(
        "--detector",
        action="append",
        nargs=3,
        metavar=("NAME", "CALIBRATION", "MASK"),
        help="""Detector configuration. Can be specified multiple times for different detector positions.
Format: --detector NAME CALIBRATION MASK
- NAME: Unique identifier for this detector position
- CALIBRATION: Path to calibration file (typically .json)
- MASK: Path to mask file (typically .npy)

Example: --detector detector1 calibration1.json mask1.npy""",
    )

    # Alternative: accept JSON string
    parser.add_argument(
        "--config-json",
        help="""JSON string containing detector configurations. Alternative to --detector arguments.
Format: {"detector_name": {"calibration": "path/to/calibration.json", "mask": "path/to/mask.npy"}}

Example: '{"detector1": {"calibration": "cal1.json", "mask": "mask1.npy"}}'""",
    )

    return parser.parse_args()


def parse_config(args) -> Dict[str, DetectorConfig]:
    """Parse detector configurations from command line arguments.

    Parameters
    ----------
    args : argparse.Namespace
        Command line arguments containing detector configurations.

    Returns
    -------
    Dict[str, DetectorConfig]
        Dictionary mapping detector names to their configurations.

    Raises
    ------
    ValueError
        If no detector configurations are provided.
    """
    if args.config_json:
        # Parse from JSON string
        return json.loads(args.config_json)

    if not args.detector:
        raise ValueError(
            "No detector configurations provided. Use --detector or --config-json."
        )

    # Parse from individual arguments
    config = {}
    for name, calibration, mask in args.detector:
        config[name] = {"calibration": calibration, "mask": mask}
    return config


def main():
    """Main entry point for the script.

    This function:
    1. Parses command line arguments
    2. Creates the output directory
    3. Processes the diffraction data
    4. Displays a plot of the integrated patterns
    """
    args = parse_args()

    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)

    # Parse configurations
    file_configs = parse_config(args)

    # Process the data
    integrated_patterns, output_filenames = integrate_multi(
        args.input_dir, args.output_dir, file_configs
    )

    print(
        f"Integration completed. {len(integrated_patterns)} patterns saved to {args.output_dir}"
    )

    base_output_filenames = [os.path.basename(f) for f in output_filenames]

    # Plot the results
    plt.figure(figsize=(10, 5))
    for (q, I), f in zip(integrated_patterns, base_output_filenames):
        plt.plot(q, I, label=os.path.basename(f))
    plt.xlabel("q (Å⁻¹)")
    plt.ylabel("Intensity (a.u.)")
    plt.show()


if __name__ == "__main__":
    main()
