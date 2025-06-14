# EL-LTP-Tools

This repository contains tools for data processing and analysis for the Extreme-Light Long-Term Project at P02.2, Petra III. The tools are designed to handle scientific image processing, cosmic ray removal, and diffraction data integration from multiple detector positions.

## Installation

```bash
poetry install
```

## Available Tools

The following command-line tools are available after installation:

### Image Processing Tools

1. **el-ltp-remove-cosmic**

   - Command-line tool for removing cosmic rays from scientific images
   - Uses statistical analysis to identify and remove cosmic ray artifacts
   - Features:
     - Configurable detection sensitivity (sigma threshold)
     - Adjustable window size for local statistics
     - Multiple iteration support for thorough detection
     - Minimum intensity threshold for noise filtering
   - Usage: `el-ltp-remove-cosmic --help`
   - Example:

     ```bash
     # Basic usage
     el-ltp-remove-cosmic input.tif output.tif

     # More sensitive detection
     el-ltp-remove-cosmic input.tif output.tif --sigma 3.0 --window-size 3

     # Conservative detection for noisy images
     el-ltp-remove-cosmic input.tif output.tif --sigma 7.0 --window-size 7 --iterations 2
     ```

2. **el-ltp-combine-images-gui**

   - Graphical interface for combining multiple images
   - Features:
     - Interactive file selection
     - Real-time preview
     - Configurable cosmic ray removal
     - Progress tracking
   - Usage: `el-ltp-combine-images-gui`

3. **el-ltp-combine-images**
   - Command-line tool for combining multiple images
   - Features:
     - Support for multiple image groups
     - Configurable directory patterns
     - Automatic cosmic ray removal
     - Progress tracking and cancellation support
   - Usage: `el-ltp-combine-images --help`

### Diffraction Data Processing Tools

1. **el-ltp-integrate-multi-gui**

   - Graphical interface for integrating diffraction data from multiple detector positions
   - Features:
     - Interactive detector configuration
     - Real-time preview of integration
     - Progress tracking
     - Support for multiple detector positions
   - Usage: `el-ltp-integrate-multi-gui`

2. **el-ltp-integrate-multi**
   - Command-line tool for integrating diffraction data from multiple detector positions
   - Features:
     - Support for multiple detector positions with individual calibrations
     - Automatic mask application
     - Polarization correction
     - Progress tracking
   - Usage: `el-ltp-integrate-multi --help`

## Detailed Usage Examples

### Image Combination

The image combination tools support multi-group processing. For multi-group processing, you can specify different groups of images to be combined separately.

Example directory structure:

```
/path/to/images/
|-- g1/              # First group
|   |-- image_0001.tif
|   |-- image_0002.tif
|   |-- image_0003.tif
|   |-- image_0004.tif
|-- g2/              # Second group
|   |-- image_0001.tif
|   |-- image_0002.tif
|   |-- image_0003.tif
|   |-- image_0004.tif
|-- g3/              # Third group
|   |-- image_0001.tif
|   |-- image_0002.tif
|   |-- image_0003.tif
|   |-- image_0004.tif
|-- g4/              # Fourth group
|   |-- image_0001.tif
|   |-- image_0002.tif
|   |-- image_0003.tif
|   |-- image_0004.tif
...
```

Example configuration for multi-group processing:

```json
[
    {
        "center": 2,  # Combine 2 directories for center group
        "side": 2     # Combine 2 directories for side group
    }
]
```

This will combine the images in the first 2 directories in the center group and the images in the next 2 directories in the side group. The output will be saved in the output directory with the name of the group.

Example output, for 8 folders (g1 to g8) with n images each and the above configuration:

```
/path/to/output/
|   |-- image_center_00001.tif
|   |-- image_center_00002.tif
|   |-- image_side_00001.tif
|   |-- image_side_00002.tif
```

### Multi-Detector Integration

The diffraction integration tool supports both command-line and GUI interfaces. Here's an example using the command-line interface:

```bash
# Using individual detector configurations:
el-ltp-integrate-multi --input-dir /path/to/images --output-dir /path/to/output \
    --detector detector1 calibration1.json mask1.npy \
    --detector detector2 calibration2.json mask2.npy

# Using JSON configuration:
el-ltp-integrate-multi --input-dir /path/to/images --output-dir /path/to/output \
    --config-json '{"detector1": {"calibration": "cal1.json", "mask": "mask1.npy"}}'
```

The tool expects input images to be named like this:

```
<file_prefix>_<detector_name>_<pattern_number>.tif
```

Example input directory structure:

```
/path/to/images/
|-- CaSiO3_2_detector1_00001.tif
|-- CaSiO3_2_detector1_00002.tif
|-- CaSiO3_2_detector2_00001.tif
|-- CaSiO3_2_detector2_00002.tif
...
```

Output will be saved as:

```
/path/to/output/
|-- CaSiO3_2_00001.xy
|-- CaSiO3_2_00002.xy
...
```

## Project Structure

```
el-ltp-tools/
├── el_ltp_tools/          # Core package code
│   ├── remove_cosmic/     # Cosmic ray removal script
│   ├── integrate_multi/   # Diffraction integration script
│   └── combine_images/    # Image combination utilities
├── scripts/               # Command-line tools
│   ├── examples/          # Example Shell Scripts
└── tests/                 # Test suite
```

## Dependencies

- Python >= 3.12, < 3.14
- fabio >= 2024.9.0
- numpy >= 2.3.0
- scipy >= 1.15.3
- pyqt6 >= 6.9.1
- pyfai >= 2025.3.0
- matplotlib >= 3.10.3
