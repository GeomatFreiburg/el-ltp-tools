import os
import tempfile
import shutil
import numpy as np
import pytest
from PIL import Image
from el_ltp_tools.diffraction import get_sorted_files, integrate_multi, DetectorConfig


@pytest.fixture
def temp_dir():
    """Create a temporary directory with test files."""
    temp_dir = tempfile.mkdtemp()
    # Create test files with different indices
    for i in range(1, 4):
        # Create center files with proper shape and data
        center_data = np.ones((100, 100), dtype=np.uint16) * i
        Image.fromarray(center_data).save(os.path.join(temp_dir, f'test_center_{i}.tif'))
        # Create side files with proper shape and data
        side_data = np.ones((100, 100), dtype=np.uint16) * (i + 10)
        Image.fromarray(side_data).save(os.path.join(temp_dir, f'test_side_{i}.tif'))
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_config(mock_poni_file, mock_mask_file):
    """Create a mock configuration for testing."""
    return {
        "center": {
            "calibration": mock_poni_file,
            "mask": mock_mask_file
        },
        "side": {
            "calibration": mock_poni_file,
            "mask": mock_mask_file
        }
    }


def test_get_sorted_files(temp_dir):
    """Test that files are correctly sorted by their index number."""
    # Test center files
    center_files = get_sorted_files(temp_dir, "center")
    assert len(center_files) == 3
    assert all("center" in f for f in center_files)
    # Verify sorting
    indices = [int(f.split("_")[-1].split(".")[0]) for f in center_files]
    assert indices == sorted(indices)

    # Test side files
    side_files = get_sorted_files(temp_dir, "side")
    assert len(side_files) == 3
    assert all("side" in f for f in side_files)
    # Verify sorting
    indices = [int(f.split("_")[-1].split(".")[0]) for f in side_files]
    assert indices == sorted(indices)


def test_get_sorted_files_no_matches(temp_dir):
    """Test behavior when no files match the keyword."""
    files = get_sorted_files(temp_dir, "nonexistent")
    assert len(files) == 0


def test_integrate_multi_missing_files(temp_dir, mock_config):
    """Test that integrate_multi raises an error when files are missing."""
    # Create output directory
    output_dir = os.path.join(temp_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    # Remove one file to create mismatch
    os.remove(os.path.join(temp_dir, "test_side_1.tif"))

    # Test with missing files
    with pytest.raises(ValueError, match="Number of files don't match"):
        integrate_multi(temp_dir, output_dir, mock_config)


def test_integrate_multi_invalid_config():
    """Test that integrate_multi raises an error with invalid config."""
    with pytest.raises(KeyError, match="mask"):
        integrate_multi("input", "output", {"invalid": {"no_calibration": "test"}})


def test_detector_config_typing():
    """Test that DetectorConfig has the correct structure."""
    # Valid config
    valid_config: DetectorConfig = {
        "calibration": "test.poni",
        "mask": "test.mask"
    }
    assert isinstance(valid_config, dict)
    assert "calibration" in valid_config
    assert "mask" in valid_config
    assert isinstance(valid_config["calibration"], str)
    assert isinstance(valid_config["mask"], str)

    # Invalid config (missing required fields)
    invalid_config = {
        "calibration": "test.poni"
        # Missing mask field
    }
    assert not all(key in invalid_config for key in ["calibration", "mask"])


def test_integrate_multi_output_files(temp_dir, mock_config):
    """Test that integrate_multi creates output files correctly."""
    # Create output directory
    output_dir = os.path.join(temp_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    # Run integration
    integrated_patterns, output_filenames = integrate_multi(temp_dir, output_dir, mock_config)

    # Check that output files were created
    output_files = os.listdir(output_dir)
    assert len(output_files) == 3  # One file per measurement
    assert all(f.endswith('.xy') for f in output_files)
    assert set(output_files) == set(os.path.basename(f) for f in output_filenames)

    # Check that integrated patterns were returned
    assert len(integrated_patterns) == 3
    for q, I in integrated_patterns:
        assert isinstance(q, np.ndarray)
        assert isinstance(I, np.ndarray)
        assert len(q) == len(I)


def test_integrate_multi_empty_directory(temp_dir, mock_config):
    """Test that integrate_multi handles empty directory correctly."""
    # Create empty output directory
    output_dir = os.path.join(temp_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    # Remove all test files (but not directories)
    for f in os.listdir(temp_dir):
        f_path = os.path.join(temp_dir, f)
        if os.path.isfile(f_path):
            os.remove(f_path)

    # Test with empty directory
    with pytest.raises(ValueError):
        integrate_multi(temp_dir, output_dir, mock_config) 