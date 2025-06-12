import fabio
import os
import argparse
from pathlib import Path
import numpy as np
from scipy import ndimage

def parse_arguments():
    parser = argparse.ArgumentParser(description='Combine measurement data from multiple folders.')
    parser.add_argument('--input', '-i', type=str, required=True,
                      help='Input folder containing the measurement data')
    parser.add_argument('--output', '-o', type=str, required=True,
                      help='Output folder for combined data')
    parser.add_argument('--start', '-s', type=int, default=2,
                      help='Starting folder index (default: 2)')
    parser.add_argument('--end', '-e', type=int, default=97,
                      help='Ending folder index (default: 97)')
    parser.add_argument('--base-filename', '-b', type=str, default="CaSiO3_",
                      help='Base filename for the measurements (default: CaSiO3_)')
    parser.add_argument('--prefix', '-p', type=str, default="CaSiO3_2",
                      help='Prefix for output files (default: CaSiO3_2)')
    parser.add_argument('--threshold', '-t', type=float, default=None,
                      help='Threshold value for pixel filtering. Pixels above this value and their adjacent pixels will be set to NaN.')
    return parser.parse_args()

def get_filenames():
    filenames = []
    for i in range(1, 5):
        filenames.append(base_filename + str(i).zfill(5) + ".tif")
    return filenames

def apply_threshold(data, threshold):
    """Apply threshold filtering to the data, setting values above threshold and adjacent pixels to NaN."""
    if threshold is not None:
        data = data.astype(float)  # Convert to float to support NaN
        
        # Create mask for pixels above threshold
        mask = data > threshold
        
        # Create a kernel for adjacent pixels (including diagonals)
        kernel = np.ones((3, 3), dtype=bool)
        kernel[1, 1] = False  # Exclude the center pixel as it's already masked
        
        # Dilate the mask to include adjacent pixels
        dilated_mask = ndimage.binary_dilation(mask, kernel)
        
        # Apply the mask to set both thresholded and adjacent pixels to NaN
        data[dilated_mask] = np.nan
        
    return data

def combine_data(folder_name):
    filenames = get_filenames()
    img = fabio.open(folder_name + "/" + filenames[0])
    img.data = apply_threshold(img.data, args.threshold)
    
    for filename in filenames[1:]:
        img_new = fabio.open(folder_name + "/" + filename)
        img_new.data = apply_threshold(img_new.data, args.threshold)
        img.data += img_new.data
    return img

config = [
    {"num_images": 2, "name": "center"},
    {"num_images": 2, "name": "side"},
]

def get_folder_groups(start_idx):
    """Group folders based on config and available folders, starting from start_idx."""
    groups = []
    current_index = start_idx
    
    for group_config in config:
        group_folders = []
        for _ in range(group_config["num_images"]):
            folder_name = f"g{current_index}"
            if os.path.exists(folder + "/" + folder_name):
                group_folders.append(folder_name)
                current_index += 1
        if group_folders:
            groups.append({"name": group_config["name"], "folders": group_folders})
    
    return groups, current_index

def process_measurements(args):
    """Process all measurements and combine data according to groups."""
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    current_index = args.start
    measurement_number = 1
    
    while current_index <= args.end:
        print(
            f"\nProcessing group {measurement_number} (starting from g{current_index})..."
        )
        groups, next_index = get_folder_groups(current_index)
        
        if not groups:  # If no valid groups were found, break the loop
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
