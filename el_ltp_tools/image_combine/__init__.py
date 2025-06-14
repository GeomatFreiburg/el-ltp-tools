import os
import json
import re

import numpy as np
from PIL import Image

import fabio
from ..util.cosmic import detect_cosmic_rays


def get_tiff_filenames(directory_path: str) -> list[str]:
    """Get all .tif and .tiff files in the specified directory.

    Parameters
    ----------
    directory_path : str
        The path to the directory containing the images to combine.

    Returns
    -------
    list
        A list of filenames with .tif or .tiff extension.
    """
    return [
        f
        for f in os.listdir(directory_path)
        if os.path.isfile(os.path.join(directory_path, f))
        and f.lower().endswith((".tif", ".tiff"))
    ]


def combine_images_in_directory(
    directory_path: str,
    cosmic_sigma: float,
    cosmic_window: int,
    cosmic_iterations: int,
    cosmic_min: float,
) -> np.ndarray:
    """
    Combines all tiff/tif images in the given directory.
    The images are combined by adding them together.
    Cosmic rays are removed from the images using the detect_cosmic_rays function.
    For each image, pixels identified as cosmic rays are replaced with the average
    value from the corresponding pixels in other images.

    Parameters
    ----------
    directory_path : str
        The path to the directory containing the images to combine.
    cosmic_sigma : float
        The sigma value for the cosmic ray detection.
    cosmic_window : int
        The window size for the cosmic ray detection.
    cosmic_iterations : int
        The number of iterations for the cosmic ray detection.
    cosmic_min : float
        The minimum intensity threshold for the cosmic ray detection.

    Returns
    -------
    np.ndarray
        The combined image data.
    """
    filenames = get_tiff_filenames(directory_path)
    if not filenames:
        raise FileNotFoundError(f"No files found in {directory_path}")

    imgs = [
        fabio.open(os.path.join(directory_path, filename)) for filename in filenames
    ]
    imgs_data = [img.data.astype(np.float64) for img in imgs]

    # Detect cosmic rays with multiple iterations
    def get_cosmic_mask(img_data):
        combined_mask = np.zeros_like(img_data, dtype=bool)
        cosmic_counts = []
        for _ in range(cosmic_iterations):
            cosmic_mask = detect_cosmic_rays(
                img_data, cosmic_sigma, cosmic_window, cosmic_min
            )
            img_data[cosmic_mask] = np.nan
            combined_mask = np.logical_or(combined_mask, cosmic_mask)
            cosmic_counts.append(np.sum(cosmic_mask))
        print(f"        Found cosmic rays: {', '.join(map(str, cosmic_counts))}")
        return combined_mask

    cosmic_masks = [get_cosmic_mask(img_data) for img_data in imgs_data]

    # Set cosmic ray pixels to NaN in all images and replace with the average of other images
    imgs_data_nan = [
        np.where(cosmic_masks[i], np.nan, imgs_data[i]) for i in range(len(imgs_data))
    ]

    # Replace cosmic ray pixels with the average of other images
    imgs_data = [
        np.where(
            cosmic_masks[i],
            (
                np.nanmean(
                    [imgs_data_nan[j] for j in range(len(imgs_data)) if j != i], axis=0
                )
                if len(imgs_data) > 1
                else imgs_data[i]
            ),  # Use original value if only one image
            imgs_data[i],
        )
        for i in range(len(imgs_data))
    ]

    return np.sum(imgs_data, axis=0)


def get_directory_groups(
    start_idx: int,
    config: list,
    input_directory: str,
    directory_pattern: str = r"g(\d+)",
) -> tuple[list, int]:
    """Group directories based on config and available directories, starting from start_idx.

    Parameters
    ----------
    start_idx : int
        The starting index for the directory groups.
    config : list
        The configuration for the directory groups. Each object maps group names to their number of directories.
        Example: [{"center": 2, "side": 2}]
    input_directory : str
        The path to the input directory.
    directory_pattern : str, optional
        Regular expression pattern to match directory names. Must contain a capture group for the sequence number.
        Default is r"g(\\d+)" which matches directories like "g1", "g2", etc.
        Example for "project_1", "project_2": r"project_(\\d+)"

    Returns
    -------
    list
        A list of dictionaries, each containing the name of the group and the directories in the group.
    current_index : int
        The index of the last directory that was checked.
    """
    groups = []
    current_index = start_idx
    pattern = re.compile(directory_pattern)

    print(f"  Checking directories starting from index {current_index}")

    # Get the first (and only) configuration object
    group_configs = config[0]

    for group_name, num_directories in group_configs.items():
        group_directories = []
        print(f"    Looking for {num_directories} directories for group '{group_name}'")

        for _ in range(num_directories):
            # Find all directories that match the pattern
            matching_directories = []
            for directory_name in os.listdir(input_directory):
                match = pattern.match(directory_name)
                if match:
                    directory_num = int(match.group(1))
                    if directory_num == current_index:
                        matching_directories.append(directory_name)

            if matching_directories:
                directory_name = matching_directories[0]  # Take the first matching directory
                directory_path = os.path.join(input_directory, directory_name)
                print(f"      Found directory: {directory_name}")
                group_directories.append(directory_name)
            else:
                print(f"      No matching directory found for index {current_index}")

            current_index += 1

        if group_directories:
            groups.append({"name": group_name, "directories": group_directories})
            print(f"    Added group '{group_name}' with {len(group_directories)} directories")
        else:
            print(f"    No directories found for group '{group_name}'")

    return groups, current_index


def process_measurements(
    input_directory: str,
    output_directory: str,
    config: str,
    start_index: int,
    end_index: int,
    cosmic_sigma: float,
    cosmic_window: int,
    cosmic_iterations: int,
    cosmic_min: float,
    prefix: str,
    callback=None,
) -> None:
    """Process all measurements and combine data according to groups.

    Parameters
    ----------
    input_directory : str
        Path to the directory containing the input measurement data.
    output_directory : str
        Path where the combined output files will be saved.
    config : str
        JSON string containing the configuration for directory groups.
        Each group should have a 'name' and 'num_directories' field.
        Example: [{"num_directories": 2, "name": "center"}, {"num_directories": 2, "name": "side"}]
    start_index : int
        The starting index for processing directories.
    end_index : int
        The ending index for processing directories.
    cosmic_sigma : float
        The sigma value for cosmic ray detection.
    cosmic_window : int
        The window size for cosmic ray detection.
    cosmic_iterations : int
        The number of iterations for cosmic ray detection.
    cosmic_min : float
        The minimum intensity threshold for cosmic ray detection.
    prefix : str
        Prefix to use for output filenames.
    callback : function, optional
        A callback function to check if the process should stop.
        Should return True to continue processing, False to stop.
    """
    # Check if input directory exists
    if not os.path.exists(input_directory):
        raise FileNotFoundError(f"Input directory not found: {input_directory}")

    # Check if input directory is readable
    if not os.access(input_directory, os.R_OK):
        raise PermissionError(
            f"No permission to read input directory: {input_directory}"
        )

    # Create output directory if it doesn't exist
    try:
        os.makedirs(output_directory, exist_ok=True)
    except PermissionError:
        raise PermissionError(
            f"No permission to create output directory: {output_directory}"
        )

    # Parse the configuration
    try:
        config_data = json.loads(config)
    except json.JSONDecodeError as e:
        raise ValueError(f"Error parsing configuration JSON: {e}")

    current_index = start_index
    measurement_number = 1

    while current_index <= end_index:
        if callback and not callback():  # Check if we should stop
            return

        print(
            f"\nProcessing measurement {measurement_number} (starting from index {current_index})..."
        )
        groups, next_index = get_directory_groups(
            current_index, config_data, input_directory
        )

        if not groups:  # If no valid groups were found, break the loop
            raise ValueError(
                f"No valid groups found starting from index {current_index}"
            )

        for group in groups:
            if callback and not callback():  # Check if we should stop
                return

            print(f"  Processing {group['name']} measurements...")
            combined_data = None

            for directory_name in group["directories"]:
                if callback and not callback():  # Check if we should stop
                    return

                directory_path = os.path.join(input_directory, directory_name)
                if not os.path.exists(directory_path):
                    raise FileNotFoundError(f"Directory not found: {directory_path}")

                print(f"    Combining data from {directory_name}")
                try:
                    if combined_data is None:
                        combined_data = combine_images_in_directory(
                            directory_path,
                            cosmic_sigma,
                            cosmic_window,
                            cosmic_iterations,
                            cosmic_min,
                        )
                    else:
                        new_data = combine_images_in_directory(
                            directory_path,
                            cosmic_sigma,
                            cosmic_window,
                            cosmic_iterations,
                            cosmic_min,
                        )
                        combined_data += new_data

                except Exception as e:
                    print(f"    Error processing {directory_name}: {e}")
                    continue

            if combined_data is not None:
                output_filename = os.path.join(
                    output_directory,
                    f"{prefix}_{group['name']}_{measurement_number:04d}.tif",
                )
                Image.fromarray(combined_data).save(output_filename)
                print(f"    Saved combined data to {output_filename}")

        current_index = next_index
        measurement_number += 1
