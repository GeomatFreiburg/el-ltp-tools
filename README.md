# EL-LTP-Tools

This repository contains tools for data processing and analysis for the Extreme-Light Long-Term Project at P02.2, Petra III.

## Installation

```bash
poetry install
```

## Available Scripts

The following command-line tools are available after installation:

### Image Processing Tools

1. **el-ltp-remove-cosmic**
   - Command-line tool for removing cosmic rays from scientific images
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
   - Usage: `el-ltp-combine-images-gui`

3. **el-ltp-combine-images**
   - Command-line tool for combining multiple images
   - Usage: `el-ltp-combine-images --help`

### Diffraction Data Processing Tools

1. **el-ltp-integrate-multi-gui**
   - Graphical interface for integrating diffraction data from multiple detector positions
   - Usage: `el-ltp-integrate-multi-gui`

2. **el-ltp-integrate-multi**
   - Command-line tool for integrating diffraction data from multiple detector positions
   - Usage: `el-ltp-integrate-multi --help`

## Example Usage

### Cosmic Ray Removal

The cosmic ray removal tool uses a statistical approach to identify and remove cosmic ray artifacts from scientific images. It works by:
1. Analyzing local pixel neighborhoods to compute mean and standard deviation
2. Identifying pixels that deviate significantly from their local statistics
3. Iteratively refining the detection to catch both strong and weak cosmic rays
4. Replacing detected cosmic ray pixels with NaN values

Example usage:
```bash
# Basic usage with default parameters
el-ltp-remove-cosmic input.tif output.tif

# More sensitive detection (lower sigma, smaller window)
el-ltp-remove-cosmic input.tif output.tif --sigma 3.0 --window-size 3

# More aggressive detection with more iterations
el-ltp-remove-cosmic input.tif output.tif --iterations 5 --min-intensity 100

# Conservative detection for noisy images
el-ltp-remove-cosmic input.tif output.tif --sigma 7.0 --window-size 7 --iterations 2
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
│   ├── cosmic/           # Cosmic ray detection algorithms
│   ├── diffraction/      # Diffraction data processing
│   └── image_combine/    # Image combination utilities
├── scripts/              # Command-line tools
│   ├── cosmic/          # Cosmic ray removal script
│   ├── diffraction/     # Diffraction processing scripts
│   └── image_combine/   # Image combination scripts
├── examples/            # Example scripts and usage
└── tests/              # Test suite
```

## Dependencies

- Python >= 3.12, < 3.14
- fabio >= 2024.9.0
- numpy >= 2.3.0
- scipy >= 1.15.3
- pyqt6 >= 6.9.1
- pyfai >= 2025.3.0
- matplotlib >= 3.10.3