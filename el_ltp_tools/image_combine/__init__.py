import os
import json

import numpy as np
from PIL import Image

import fabio
from ..util.cosmic import detect_cosmic_rays


def get_tiff_filenames(folder_path: str) -> list[str]:
    """Get all .tif and .tiff files in the specified folder.

    Parameters
    ----------
    folder_path : str
        The path to the folder containing the images to combine.

    Returns
    -------
    list
        A list of filenames with .tif or .tiff extension.
    """
    return [
        f
        for f in os.listdir(folder_path)
        if os.path.isfile(os.path.join(folder_path, f))
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
    Combines all tiff/tif images in the given folder.
    The images are combined by adding them together.
    Cosmic rays are removed from the images using the detect_cosmic_rays function.
    For each image, pixels identified as cosmic rays are replaced with the average
    value from the corresponding pixels in other images.

    Parameters
    ----------
    folder_name : str
        The path to the folder containing the images to combine.
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
            np.nanmean(
                [imgs_data_nan[j] for j in range(len(imgs_data)) if j != i], axis=0
            ),
            imgs_data[i],
        )
        for i in range(len(imgs_data))
    ]

    return np.sum(imgs_data, axis=0)


def get_folder_groups(
    start_idx: int, config: list, input_folder: str
) -> tuple[list, int]:
    """Group folders based on config and available folders, starting from start_idx.

    Parameters
    ----------
    start_idx : int
        The starting index for the folder groups.
    config : list
        The configuration for the folder groups.
    input_folder : str
        The path to the input folder.

    Returns
    -------
    list
        A list of dictionaries, each containing the name of the group and the folders in the group.
    current_index : int
        The index of the last folder that was checked.
    """
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


def process_measurements(args, callback=None) -> None:
    """Process all measurements and combine data according to groups.

    Parameters
    ----------
    args : argparse.Namespace
        The arguments for the script.
    callback : function, optional
        A callback function to check if the process should stop.
    """
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
                        combined_data = combine_images_in_directory(
                            folder_path,
                            args.cosmic_sigma,
                            args.cosmic_window,
                            args.cosmic_iterations,
                            args.cosmic_min,
                        )
                    else:
                        new_data = combine_images_in_directory(
                            folder_path,
                            args.cosmic_sigma,
                            args.cosmic_window,
                            args.cosmic_iterations,
                            args.cosmic_min,
                        )
                        combined_data += new_data

                except Exception as e:
                    print(f"    Error processing {folder_name}: {e}")
                    continue

            if combined_data is not None:
                output_filename = os.path.join(
                    args.output,
                    f"{args.prefix}_{group['name']}_{measurement_number:04d}.tif",
                )
                Image.fromarray(combined_data).save(output_filename)
                print(f"    Saved combined data to {output_filename}")

        current_index = next_index
        measurement_number += 1
