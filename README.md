# EL-LTP-Tools

This repository contains tools for data processing and analysis for the Extreme-Light Long-Term Project at P02.2, Petra III.

## Installation

```bash
poetry install
```

## Available Scripts

The following command-line tools are available after installation:

### Image Combination Tools

1. **el-ltp-combine-images-gui**
   - Graphical interface for combining multiple images
   - Usage: `el-ltp-combine-images-gui`

2. **el-ltp-combine-images**
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

## Dependencies

- Python >= 3.12, < 3.14
- fabio >= 2024.9.0
- numpy >= 2.3.0
- scipy >= 1.15.3
- pyqt6 >= 6.9.1
- pyfai >= 2025.3.0
- matplotlib >= 3.10.3