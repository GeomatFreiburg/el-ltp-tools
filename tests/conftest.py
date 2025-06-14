import os
import tempfile
import shutil
import numpy as np
from PIL import Image
import pytest


@pytest.fixture
def mock_poni_file():
    """Create a mock .poni calibration file."""
    temp_dir = tempfile.mkdtemp()
    poni_path = os.path.join(temp_dir, "test.poni")
    
    # Create a .poni file with the correct format
    poni_content = """# Nota: C-Order, 1 refers to the Y axis, 2 to the X axis 
# Calibration done at Tue Oct 15 22:20:08 2024
poni_version: 2
Detector: Detector
Detector_config: {"pixel1": 1.0e-4, "pixel2": 1.0e-4, "max_shape": [100, 100]}
Distance: 1.0
Poni1: 0.0
Poni2: 0.0
Rot1: 0.0
Rot2: 0.0
Rot3: 0.0
Wavelength: 1.0e-10
"""
    with open(poni_path, 'w') as f:
        f.write(poni_content)
    
    yield poni_path
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_mask_file():
    """Create a mock mask file."""
    temp_dir = tempfile.mkdtemp()
    mask_path = os.path.join(temp_dir, "test.mask")
    
    # Create a simple mask image (all zeros)
    mask = np.zeros((100, 100), dtype=np.uint8)
    # Save as TIFF since .mask is not a recognized format
    Image.fromarray(mask).save(mask_path, format='TIFF')
    
    yield mask_path
    shutil.rmtree(temp_dir) 