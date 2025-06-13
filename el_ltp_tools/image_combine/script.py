import argparse
from . import process_measurements


def parse_arguments():
    """Parse the arguments for the script."""

    parser = argparse.ArgumentParser(
        description="Combine measurement data from multiple folders."
    )
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        required=True,
        help="Input folder containing the measurement data",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        required=True,
        help="Output folder for combined data",
    )
    parser.add_argument(
        "--start", "-s", type=int, default=2, help="Starting folder index (default: 2)"
    )
    parser.add_argument(
        "--end", "-e", type=int, default=97, help="Ending folder index (default: 97)"
    )
    parser.add_argument(
        "--prefix",
        "-p",
        type=str,
        default="CaSiO3_2",
        help="Prefix for output files (default: CaSiO3_2)",
    )
    parser.add_argument(
        "--cosmic-sigma",
        type=float,
        default=6.0,
        help="Number of standard deviations above local mean to consider a pixel as cosmic ray (default: 5.0)",
    )
    parser.add_argument(
        "--cosmic-window",
        type=int,
        default=10,
        help="Size of the window for local statistics (default: 5)",
    )
    parser.add_argument(
        "--cosmic-iterations",
        type=int,
        default=3,
        help="Number of iterations for cosmic ray detection (default: 3)",
    )
    parser.add_argument(
        "--cosmic-min",
        type=float,
        default=50.0,
        help="Minimum intensity threshold for cosmic ray detection (default: 100.0)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default='[{"num_images": 2, "name": "center"}, {"num_images": 2, "name": "side"}]',
        help='JSON string defining the measurement configuration. Each group should have "num_images" and "name". Default: [{"num_images": 2, "name": "center"}, {"num_images": 2, "name": "side"}]',
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    process_measurements(args)
