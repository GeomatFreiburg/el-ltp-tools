import fabio
import os
import argparse
import numpy as np
import json
from cosmic import remove_cosmic_rays


def parse_arguments():
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


def get_filenames(folder_path):
    """Get all .tif and .tiff files in the specified folder."""
    return [
        f
        for f in os.listdir(folder_path)
        if os.path.isfile(os.path.join(folder_path, f))
        and f.lower().endswith((".tif", ".tiff"))
    ]


def combine_data(
    folder_name, cosmic_sigma, cosmic_window, cosmic_iterations, cosmic_min
):
    filenames = get_filenames(folder_name)
    if not filenames:
        raise FileNotFoundError(f"No files found in {folder_name}")

    # Get the first file to initialize the combined image
    first_file = os.path.join(folder_name, filenames[0])
    img = fabio.open(first_file)
    # Convert to float immediately after loading
    img.data = img.data.astype(np.float64)
    img.data = remove_cosmic_rays(
        img.data,
        cosmic_sigma,
        cosmic_window,
        cosmic_iterations,
        cosmic_min,
    )

    # Process remaining files
    for filename in filenames[1:]:
        file_path = os.path.join(folder_name, filename)
        img_new = fabio.open(file_path)
        # Convert to float immediately after loading
        img_new.data = img_new.data.astype(np.float64)
        img_new.data = remove_cosmic_rays(
            img_new.data,
            cosmic_sigma,
            cosmic_window,
            cosmic_iterations,
            cosmic_min,
        )
        img.data += img_new.data
    return img


def get_folder_groups(start_idx, config, input_folder):
    """Group folders based on config and available folders, starting from start_idx."""
    groups = []
    current_index = start_idx

    print(f"  Checking folders starting from g{current_index}")

    for group_config in config:
        group_folders = []
        print(
            f"    Looking for {group_config['num_images']} images for group '{group_config['name']}'"
        )

        for _ in range(group_config["num_images"]):
            folder_name = f"g{current_index}"
            folder_path = os.path.join(input_folder, folder_name)
            print(f"      Checking folder: {folder_path}")

            if os.path.exists(folder_path):
                print(f"      Found folder: {folder_name}")
                group_folders.append(folder_name)
            else:
                print(f"      Folder not found: {folder_name}")

            current_index += 1

        if group_folders:
            groups.append({"name": group_config["name"], "folders": group_folders})
            print(
                f"    Added group '{group_config['name']}' with {len(group_folders)} folders"
            )
        else:
            print(f"    No folders found for group '{group_config['name']}'")

    return groups, current_index


def process_measurements(args, callback=None):
    """Process all measurements and combine data according to groups."""
    input_folder = args.input

    # Check if input directory exists
    if not os.path.exists(input_folder):
        raise FileNotFoundError(f"Input directory not found: {input_folder}")

    # Check if input directory is readable
    if not os.access(input_folder, os.R_OK):
        raise PermissionError(f"No permission to read input directory: {input_folder}")

    # Create output directory if it doesn't exist
    try:
        os.makedirs(args.output, exist_ok=True)
    except PermissionError:
        raise PermissionError(
            f"No permission to create output directory: {args.output}"
        )

    # Parse the configuration
    try:
        config = json.loads(args.config)
    except json.JSONDecodeError as e:
        raise ValueError(f"Error parsing configuration JSON: {e}")

    current_index = args.start
    measurement_number = 1

    while current_index <= args.end:
        if callback and not callback():  # Check if we should stop
            return

        print(
            f"\nProcessing group {measurement_number} (starting from g{current_index})..."
        )
        groups, next_index = get_folder_groups(current_index, config, input_folder)

        if not groups:  # If no valid groups were found, break the loop
            raise ValueError(f"No valid groups found starting from g{current_index}")

        for group in groups:
            if callback and not callback():  # Check if we should stop
                return

            print(f"  Processing {group['name']} measurements...")
            combined_data = None

            for folder_name in group["folders"]:
                if callback and not callback():  # Check if we should stop
                    return

                folder_path = os.path.join(input_folder, folder_name)
                if not os.path.exists(folder_path):
                    raise FileNotFoundError(f"Folder not found: {folder_path}")

                print(f"    Combining data from {folder_name}")
                try:
                    if combined_data is None:
                        combined_data = combine_data(
                            folder_path,
                            args.cosmic_sigma,
                            args.cosmic_window,
                            args.cosmic_iterations,
                            args.cosmic_min,
                        )
                    else:
                        new_data = combine_data(
                            folder_path,
                            args.cosmic_sigma,
                            args.cosmic_window,
                            args.cosmic_iterations,
                            args.cosmic_min,
                        )
                        combined_data.data += new_data.data
                except FileNotFoundError as e:
                    raise FileNotFoundError(
                        f"File not found in {folder_path}: {str(e)}"
                    )
                except Exception as e:
                    raise RuntimeError(f"Error processing {folder_path}: {str(e)}")

            if combined_data is not None:
                # Save the combined data to the output folder
                output_filename = f"{args.output}/{args.prefix}_{group['name']}_{str(measurement_number).zfill(4)}.tif"
                try:
                    combined_data.write(output_filename)
                    print(f"    Saved combined data to {output_filename}")
                except Exception as e:
                    raise RuntimeError(
                        f"Error saving output file {output_filename}: {str(e)}"
                    )

        current_index = next_index
        measurement_number += 1


if __name__ == "__main__":
    args = parse_arguments()
    process_measurements(args)
