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
    
    Parameters
    ----------
    calibration : str
        Path to the .poni calibration file for this detector position.
    mask : str
        Path to the mask file (.mask) for this detector position.
    """
    calibration: str
    mask: str


def get_sorted_files(base_path: str, keyword: str) -> list[str]:
    """Find and sort files based on keyword and their index number.
    
    Parameters
    ----------
    base_path : str
        Directory to search for files.
    keyword : str
        Keyword to match in filenames (e.g., 'center', 'side').
        
    Returns
    -------
    list[str]
        List of sorted file paths matching the pattern.
    """
    pattern = f"{base_path}/*{keyword}*.tif"
    files = glob.glob(pattern)

    # Extract number from filename and sort
    def get_index(filename):
        match = re.search(r"(\d+)\.tif$", filename)
        return int(match.group(1)) if match else 0

    return sorted(files, key=get_index)


def integrate_multi(
    input_dir: str, output_dir: str, config: Dict[str, DetectorConfig], progress_callback=None
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Process and integrate data from multiple detector positions.
    
    This function takes data from multiple detector positions (e.g., center, side),
    each with its own calibration and mask, and integrates them together using
    pyFAI's MultiGeometry integration.
    
    Parameters
    ----------
    input_dir : str
        Directory containing the input .tif files.
    output_dir : str
        Directory where integrated .xy files will be saved.
    config : Dict[str, DetectorConfig]
        Dictionary mapping detector position names to their configurations.
        Each configuration must specify calibration and mask file paths.
    progress_callback : callable, optional
        Function to call with progress messages. Should accept a single string argument.
               
    Returns
    -------
    list[tuple[np.ndarray, np.ndarray]]
        List of tuples containing (q, I) arrays for each integrated pattern.
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
    
    # Check if any configuration has no files
    if not any(config_files.values()):
        raise ValueError("No files found in any configuration!")
    
    # Ensure all configurations have the same number of files
    num_files = len(next(iter(config_files.values())))
    if not all(len(files) == num_files for files in config_files.values()):
        raise ValueError("Number of files don't match across all configurations!")
    
    integrated_patterns = []
    # Process each set of files
    for i in range(num_files):
        # Get the current file from each configuration
        current_files = [files[i] for files in config_files.values()]
        msg = f"Processing files: {[os.path.basename(f) for f in current_files]}"
        print(msg)
        if progress_callback:
            progress_callback(msg)
        
        # Extract base name from first file (removing configuration name and extension)
        first_file = os.path.basename(current_files[0])
        base_name = re.sub(r'_[^_]+_\d+\.tif$', '', first_file)
        
        # Load data from all files
        img_data = [fabio.open(img_file).data[::-1] for img_file in current_files]
        
        # Integrate using the provided MultiGeometry
        q, I = mg.integrate1d(
            img_data, npt=500, lst_mask=mask_data, polarization_factor=1
        )
        integrated_patterns.append((q, I))
        
        # Save the integrated pattern with the base name (index starting from 1)
        output_filename = os.path.join(output_dir, f"{base_name}_{i+1:04d}.xy")
        np.savetxt(
            output_filename,
            np.column_stack((q, I)),
            header="q(A^-1) I(a.u.)",
            comments="# ",
        )
        msg = f"Saved integrated pattern to: {output_filename}"
        print(msg)
        if progress_callback:
            progress_callback(msg)
        print()  # Add blank line after each save message
    
    return integrated_patterns 