import matplotlib.pyplot as plt
from typing import Dict
from . import DetectorConfig, integrate_multi


def main():
    # Example configuration
    file_configs: Dict[str, DetectorConfig] = {
        "center": {
            "calibration": "../../Data/calibration/20241015_01_after_collision/ceo2_x668y-400_20241015_pily0_00002.poni",
            "mask": "../../Data/masks/CaSiO3_2/base_CaSiO3_2_center.mask",
        },
        "side": {
            "calibration": "../../Data/calibration/20241015_01_after_collision/ceo2_x668y-400_20241015_pily5_00002.poni",
            "mask": "../../Data/masks/CaSiO3_2/base_CaSiO3_2_side.mask",
        },
    }
    
    # Example paths
    input_dir = "../../Data/BX90_13_empty_2_combined"
    output_dir = "../../Data/BX90_13_empty_2_integrated"
    # input_dir = "../../Data/CaSiO3_2_combined"
    # output_dir = "../../Data/CaSiO3_2_integrated"
    
    # Process the data
    integrated_patterns = integrate_multi(input_dir, output_dir, file_configs)
    
    # Plot the results
    plt.figure(figsize=(10, 5))
    for q, I in integrated_patterns:
        plt.plot(q, I)
    plt.xlabel("q (Å⁻¹)")
    plt.ylabel("Intensity (a.u.)")
    plt.show()


if __name__ == "__main__":
    main() 