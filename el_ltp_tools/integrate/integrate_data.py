from pyFAI.multi_geometry import MultiGeometry
import fabio
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
import glob
import re
import os

# Configuration for each file type
file_configs = {
    "center": {
        "keyword": "center",
        "calibration": "../../Data/calibration/20241015_01_after_collision/ceo2_x668y-400_20241015_pily0_00002.poni",
        "mask": "../../Data/masks/CaSiO3_2/base_CaSiO3_2_center.mask",
    },
    "side": {
        "keyword": "side",
        "calibration": "../../Data/calibration/20241015_01_after_collision/ceo2_x668y-400_20241015_pily5_00002.poni",
        "mask": "../../Data/masks/CaSiO3_2/base_CaSiO3_2_side.mask",
    },
}


def get_sorted_files(base_path, keyword):
    """Find and sort files based on keyword and their index number."""
    pattern = f"{base_path}/*{keyword}*.tif"
    files = glob.glob(pattern)

    # Extract number from filename and sort
    def get_index(filename):
        match = re.search(r"(\d+)\.tif$", filename)
        return int(match.group(1)) if match else 0

    return sorted(files, key=get_index)


def integrate_file_pair(center_file, side_file, mg, mask_data):
    """Integrate a single pair of files."""
    # Load data
    img_data = [
        fabio.open(img_file).data[::-1] for img_file in [center_file, side_file]
    ]

    # Integrate using the provided MultiGeometry
    q, I = mg.integrate1d(img_data, npt=500, lst_mask=mask_data, polarization_factor=1)

    return q, I


def main():
    base_path = "../../Data/BX90_13_empty_2_combined"
    output_dir = "../../Data/BX90_13_empty_2_integrated"
    # base_path = "../../Data/CaSiO3_2_combined"
    # output_dir = "../../Data/CaSiO3_2_integrated"
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Load mask data once
    mask_data = [
        np.array(Image.open(file_configs["center"]["mask"])),
        np.array(Image.open(file_configs["side"]["mask"])),
    ]
    
    # Create MultiGeometry once
    poni_filenames = [
        file_configs["center"]["calibration"],
        file_configs["side"]["calibration"],
    ]
    mg = MultiGeometry(poni_filenames, unit="q_A^-1")
    
    # Get sorted files for each type
    center_files = get_sorted_files(base_path, file_configs["center"]["keyword"])
    side_files = get_sorted_files(base_path, file_configs["side"]["keyword"])
    
    # Ensure we have matching pairs
    if len(center_files) != len(side_files):
        raise ValueError("Number of center and side files don't match!")
    
    plt.figure(figsize=(10, 5))
    # Process each pair
    for center_file, side_file in zip(center_files, side_files):
        print(
            f"Processing pair: {os.path.basename(center_file)} and {os.path.basename(side_file)}"
        )
        q, I = integrate_file_pair(center_file, side_file, mg, mask_data)
        plt.plot(q, I)
        
        # Save the integrated pattern
        output_filename = os.path.join(
            output_dir,
            f"{os.path.basename(center_file).replace('.tif', '.xy').replace('center', 'integrated')}"
        )
        np.savetxt(output_filename, np.column_stack((q, I)), header="q(A^-1) I(a.u.)", comments="")
        print(f"Saved integrated pattern to: {output_filename}")
    
    plt.xlabel("q (Å⁻¹)")
    plt.ylabel("Intensity (a.u.)")
    plt.show()


if __name__ == "__main__":
    main()
