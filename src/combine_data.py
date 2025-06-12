import fabio
import os
import argparse
import numpy as np
from scipy import ndimage
import json


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
        "--base-filename",
        "-b",
        type=str,
        default="CaSiO3_",
        help="Base filename for the measurements (default: CaSiO3_)",
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


def get_filenames():
    filenames = []
    for i in range(1, 5):
        filenames.append(base_filename + str(i).zfill(5) + ".tif")
    return filenames


def detect_cosmic_rays(data, sigma, window_size, min_intensity):
    """Detect cosmic rays by comparing pixel values to local statistics."""
    # Create a mask for positive values
    positive_mask = data > 0

    # Create a copy of data where negative values are set to 0
    data_positive = np.where(positive_mask, data, 0)

    # Calculate local mean and standard deviation using only positive values
    # First, calculate the sum and count of positive values in each window
    sum_positive = ndimage.uniform_filter(data_positive, size=window_size)
    count_positive = ndimage.uniform_filter(
        positive_mask.astype(float), size=window_size
    )

    # Calculate mean (avoiding division by zero)
    local_mean = np.where(count_positive > 0, sum_positive / count_positive, 0)

    # Calculate variance for positive values
    sum_squares = ndimage.uniform_filter(data_positive**2, size=window_size)
    local_var = np.where(
        count_positive > 0, (sum_squares / count_positive) - local_mean**2, 0
    )

    local_std = np.sqrt(np.maximum(local_var, 0))

    # Calculate z-scores only for positive values
    z_scores = np.zeros_like(data)
    valid_mask = np.logical_and(positive_mask, local_std > 0)
    z_scores[valid_mask] = (data[valid_mask] - local_mean[valid_mask]) / (
        local_std[valid_mask] + 1e-10
    )

    # Create mask for cosmic rays (pixels that are significantly above local mean)
    cosmic_mask = np.logical_and(z_scores > sigma, positive_mask)

    # Also mask pixels that are more than 2x the local mean
    intensity_mask = np.logical_and(data > (2 * local_mean), positive_mask)

    # Combine masks
    combined_mask = np.logical_or(cosmic_mask, intensity_mask)

    # Apply minimum intensity threshold
    combined_mask = np.logical_and(combined_mask, data > min_intensity)

    return combined_mask


def apply_threshold(data, sigma, window_size, iterations, min_intensity):
    """Apply cosmic ray detection and set detected pixels to NaN."""
    if sigma is not None:
        # Convert to float before any operations
        data = data.astype(np.float64)

        # Store counts for each iteration
        cosmic_counts = []

        # Iterate multiple times to catch all cosmic rays
        for i in range(iterations):
            # Detect cosmic rays
            cosmic_mask = detect_cosmic_rays(data, sigma, window_size, min_intensity)

            # Set cosmic ray pixels to NaN
            data[cosmic_mask] = np.nan

            # Store the count
            cosmic_counts.append(np.sum(cosmic_mask))

        # Print all counts in one line
        print(f"    Found cosmic rays: {', '.join(map(str, cosmic_counts))}")

    return data


def combine_data(folder_name):
    filenames = get_filenames()
    img = fabio.open(folder_name + "/" + filenames[0])
    # Convert to float immediately after loading
    img.data = img.data.astype(np.float64)
    img.data = apply_threshold(
        img.data,
        args.cosmic_sigma,
        args.cosmic_window,
        args.cosmic_iterations,
        args.cosmic_min,
    )

    for filename in filenames[1:]:
        img_new = fabio.open(folder_name + "/" + filename)
        # Convert to float immediately after loading
        img_new.data = img_new.data.astype(np.float64)
        img_new.data = apply_threshold(
            img_new.data,
            args.cosmic_sigma,
            args.cosmic_window,
            args.cosmic_iterations,
            args.cosmic_min,
        )
        img.data += img_new.data
    return img


def get_folder_groups(start_idx, config):
    """Group folders based on config and available folders, starting from start_idx."""
    groups = []
    current_index = start_idx
    
    print(f"  Checking folders starting from g{current_index}")
    
    for group_config in config:
        group_folders = []
        print(f"    Looking for {group_config['num_images']} images for group '{group_config['name']}'")
        
        for _ in range(group_config["num_images"]):
            folder_name = f"g{current_index}"
            folder_path = os.path.join(folder, folder_name)
            print(f"      Checking folder: {folder_path}")
            
            if os.path.exists(folder_path):
                print(f"      Found folder: {folder_name}")
                group_folders.append(folder_name)
            else:
                print(f"      Folder not found: {folder_name}")
            
            current_index += 1
        
        if group_folders:
            groups.append({"name": group_config["name"], "folders": group_folders})
            print(f"    Added group '{group_config['name']}' with {len(group_folders)} folders")
        else:
            print(f"    No folders found for group '{group_config['name']}'")
    
    return groups, current_index


def process_measurements(args):
    """Process all measurements and combine data according to groups."""
    global folder  # Make folder accessible to get_folder_groups
    folder = args.input
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    # Parse the configuration
    try:
        config = json.loads(args.config)
    except json.JSONDecodeError as e:
        print(f"Error parsing configuration JSON: {e}")
        return
    
    current_index = args.start
    measurement_number = 1
    
    while current_index <= args.end:
        print(
            f"\nProcessing group {measurement_number} (starting from g{current_index})..."
        )
        groups, next_index = get_folder_groups(current_index, config)
        
        if not groups:  # If no valid groups were found, break the loop
            print(f"No valid groups found starting from g{current_index}, stopping.")
            break
            
        for group in groups:
            print(f"  Processing {group['name']} measurements...")
            combined_data = None
            
            for folder_name in group["folders"]:
                print(f"    Combining data from {folder_name}")
                if combined_data is None:
                    combined_data = combine_data(folder + "/" + folder_name)
                else:
                    new_data = combine_data(folder + "/" + folder_name)
                    combined_data.data += new_data.data
            
            # Save the combined data to the output folder
            output_filename = f"{args.output}/{args.prefix}_{group['name']}_{str(measurement_number).zfill(4)}.tif"
            combined_data.write(output_filename)
            print(f"    Saved combined data to {output_filename}")
        
        current_index = next_index
        measurement_number += 1


if __name__ == "__main__":
    args = parse_arguments()
    folder = args.input
    base_filename = args.base_filename
    process_measurements(args)
