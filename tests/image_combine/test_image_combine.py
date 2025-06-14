import os
import json
import numpy as np
import pytest
from el_ltp_tools.image_combine import (
    get_tiff_filenames,
    combine_images_in_directory,
    get_directory_groups,
    process_measurements,
)


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory with test data."""
    # Create test directories
    test_dirs = ["g2", "g3", "g4", "g5"]
    for dir_name in test_dirs:
        (tmp_path / dir_name).mkdir()

    # Create test images
    for dir_name in test_dirs:
        dir_path = tmp_path / dir_name
        # Create center and side images
        for img_type in ["center", "side"]:
            for i in range(1, 3):  # Create 2 images of each type
                img_path = dir_path / f"{img_type}_{i}.tif"
                # Create a simple test image with some cosmic rays
                img_data = np.ones((100, 100), dtype=np.float32)
                # Add some cosmic rays
                if i == 1:
                    img_data[50, 50] = 1000  # Cosmic ray
                    img_data[25, 75] = 1000  # Cosmic ray
                # Save as tiff
                from PIL import Image

                Image.fromarray(img_data).save(img_path)

    return tmp_path


def test_get_tiff_filenames(temp_dir):
    """Test getting tiff filenames from a directory."""
    # Test with a directory containing tiff files
    filenames = get_tiff_filenames(str(temp_dir / "g2"))
    assert len(filenames) == 4  # 2 center + 2 side images
    assert all(f.endswith((".tif", ".tiff")) for f in filenames)

    # Test with empty directory
    empty_dir = temp_dir / "empty"
    empty_dir.mkdir()
    filenames = get_tiff_filenames(str(empty_dir))
    assert len(filenames) == 0


def test_combine_images_in_directory(temp_dir):
    """Test combining images in a directory with cosmic ray detection."""
    # Test combining images
    combined = combine_images_in_directory(
        str(temp_dir / "g2"),
        cosmic_sigma=6.0,
        cosmic_window=10,
        cosmic_iterations=3,
        cosmic_min=50.0,
    )

    # Check that cosmic rays were removed
    assert combined[50, 50] < 1000  # Cosmic ray should be removed
    assert combined[25, 75] < 1000  # Cosmic ray should be removed

    # Check that the rest of the image is correct
    assert np.all(
        combined[~((combined == combined[50, 50]) | (combined == combined[25, 75]))]
        == 2.0
    )


def test_get_directory_groups(temp_dir):
    """Test grouping directories based on configuration."""
    config = [{"center": 2, "side": 2}]
    groups, current_index = get_directory_groups(2, config, str(temp_dir))

    # Check that we got the expected groups
    assert len(groups) == 2  # center and side
    assert groups[0]["name"] == "center"
    assert groups[1]["name"] == "side"
    assert len(groups[0]["directories"]) == 2
    assert len(groups[1]["directories"]) == 2

    # Check that the directories are in order
    assert groups[0]["directories"] == ["g2", "g3"]
    assert groups[1]["directories"] == ["g4", "g5"]

    # Check that current_index is correct
    assert current_index == 6  # Started at 2, processed 4 directories


def test_process_measurements(temp_dir):
    """Test the full measurement processing workflow."""
    # Create output directory
    output_dir = temp_dir / "output"
    output_dir.mkdir()

    # Process measurements
    config = json.dumps([{"center": 2, "side": 2}])
    process_measurements(
        input_directory=str(temp_dir),
        output_directory=str(output_dir),
        config=config,
        start_index=2,
        end_index=5,
        cosmic_sigma=6.0,
        cosmic_window=10,
        cosmic_iterations=3,
        cosmic_min=50.0,
        prefix="test",
    )

    # Check that output files were created
    assert (output_dir / "test_center_0001.tif").exists()
    assert (output_dir / "test_side_0001.tif").exists()


def test_invalid_configuration():
    """Test handling of invalid configurations."""
    with pytest.raises(ValueError):
        # Empty configuration
        get_directory_groups(1, [], "dummy_dir")

    with pytest.raises(ValueError):
        # Invalid configuration format
        get_directory_groups(1, [{"invalid": "format"}], "dummy_dir")


def test_missing_directories(temp_dir):
    """Test handling of missing directories."""
    config = [{"center": 2, "side": 2}]
    groups, current_index = get_directory_groups(10, config, str(temp_dir))

    # Should return empty groups when no directories are found
    assert len(groups) == 0
    assert current_index == 14  # Started at 10, checked 4 directories
