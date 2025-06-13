from pyFAI.multi_geometry import MultiGeometry
import fabio
import numpy as np
from PIL import Image
import glob
import re
import os
from typing import TypedDict, Dict


class DetectorConfig(TypedDict):
    """Configuration for a single detector position.
    
    Attributes:
        calibration: Path to the .poni calibration file for this detector position
        mask: Path to the mask file (.mask) for this detector position
    """
    calibration: str
    mask: str


def get_sorted_files(base_path: str, keyword: str) -> list[str]:
    """Find and sort files based on keyword and their index number.
    
    Args:
        base_path: Directory to search for files
        keyword: Keyword to match in filenames (e.g., 'center', 'side')
        
    Returns:
        List of sorted file paths matching the pattern
    """
    pattern = f"{base_path}/*{keyword}*.tif"
    files = glob.glob(pattern)

    # Extract number from filename and sort
    def get_index(filename):
        match = re.search(r"(\d+)\.tif$", filename)
        return int(match.group(1)) if match else 0

    return sorted(files, key=get_index)


def integrate_multi(
    input_dir: str, output_dir: str, config: Dict[str, DetectorConfig]
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Process and integrate data from multiple detector positions.
    
    This function takes data from multiple detector positions (e.g., center, side),
    each with its own calibration and mask, and integrates them together using
    pyFAI's MultiGeometry integration.
    
    Args:
        input_dir: Directory containing the input .tif files
        output_dir: Directory where integrated .xy files will be saved
        config: Dictionary mapping detector position names to their configurations.
               Each configuration must specify calibration and mask file paths.
               Example:
               {
                   "center": {
                       "calibration": "path/to/center.poni",
                       "mask": "path/to/center.mask"
                   },
                   "side": {
                       "calibration": "path/to/side.poni",
                       "mask": "path/to/side.mask"
                   }
               }
               
    Returns:
        List of tuples containing (q, I) arrays for each integrated pattern
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Load mask data for all configurations
    mask_data = [np.array(Image.open(cfg["mask"])) for cfg in config.values()]
    
    # Create MultiGeometry once
    poni_filenames = [cfg["calibration"] for cfg in config.values()]
    mg = MultiGeometry(poni_filenames, unit="q_A^-1")
    
    # Get sorted files for each configuration
    config_files = {
        config_name: get_sorted_files(input_dir, config_name)
        for config_name in config.keys()
    }
    
    # Ensure all configurations have the same number of files
    num_files = len(next(iter(config_files.values())))
    if not all(len(files) == num_files for files in config_files.values()):
        raise ValueError("Number of files don't match across all configurations!")
    
    integrated_patterns = []
    # Process each set of files
    for i in range(num_files):
        # Get the current file from each configuration
        current_files = [files[i] for files in config_files.values()]
        print(f"Processing files: {[os.path.basename(f) for f in current_files]}")
        
        # Load data from all files
        img_data = [fabio.open(img_file).data[::-1] for img_file in current_files]
        
        # Integrate using the provided MultiGeometry
        q, I = mg.integrate1d(
            img_data, npt=500, lst_mask=mask_data, polarization_factor=1
        )
        integrated_patterns.append((q, I))
        
        # Save the integrated pattern
        output_filename = os.path.join(output_dir, f"integrated_{i:04d}.xy")
        np.savetxt(
            output_filename,
            np.column_stack((q, I)),
            header="q(A^-1) I(a.u.)",
            comments="",
        )
        print(f"Saved integrated pattern to: {output_filename}")
        print()  # Add blank line after each save message
    
    return integrated_patterns 