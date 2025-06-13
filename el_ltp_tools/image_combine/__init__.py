import os
import json
import numpy as np
import fabio
from ..util.cosmic import remove_cosmic_rays


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
    """
    Combines all images (with ".tif" or ".tiff" extension) in the given folder.
    The images are combined by adding them together.
    Cosmic rays are removed from the images using the remove_cosmic_rays function.

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
    fabio.fabio.Image
        The combined image.
    """
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


def process_measurements(args, callback=None):
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
    if not os.access(input_folder, os.R.OK):
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

                except Exception as e:
                    print(f"    Error processing {folder_name}: {e}")
                    continue

            if combined_data is not None:
                output_filename = os.path.join(
                    args.output, f"{args.prefix}_{group['name']}_{measurement_number:04d}.tif"
                )
                combined_data.write(output_filename)
                print(f"    Saved combined data to {output_filename}")

        current_index = next_index
        measurement_number += 1
