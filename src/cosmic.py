import numpy as np
from scipy import ndimage


def detect_cosmic_rays(data, sigma, window_size, min_intensity):
    """Detect cosmic rays in image data by comparing pixel values to local statistics.

    This function identifies cosmic rays by looking for pixels that are significantly
    brighter than their local neighborhood. It uses a combination of statistical
    analysis (z-scores) and intensity thresholds to identify potential cosmic ray hits.

    Parameters
    ----------
    data : numpy.ndarray
        Input image data array. Should be a 2D array of pixel values.
    sigma : float
        Number of standard deviations above the local mean to consider a pixel
        as a potential cosmic ray. Higher values are more conservative.
    window_size : int
        Size of the local neighborhood window used to calculate statistics.
        Should be an odd number to have a well-defined center pixel.
    min_intensity : float
        Minimum pixel intensity threshold. Only pixels above this value will be
        considered as potential cosmic rays.

    Returns
    -------
    numpy.ndarray
        Boolean mask where True indicates pixels identified as cosmic rays.
    """
    # Create a mask for positive values
    positive_mask = data > 0

    # Create a copy of data where negative values are set to 0
    data_positive = np.where(positive_mask, data, 0)

    # Calculate local mean and standard deviation using only positive values
    # First, calculate the sum and count of positive values in each window
    sum_positive = ndimage.uniform_filter(data_positive, size=window_size)
    count_positive = ndimage.uniform_filter(
        positive_mask.astype(float), size=window_size
    )

    # Calculate mean (avoiding division by zero)
    local_mean = np.where(count_positive > 0, sum_positive / count_positive, 0)

    # Calculate variance for positive values
    sum_squares = ndimage.uniform_filter(data_positive**2, size=window_size)
    local_var = np.where(
        count_positive > 0, (sum_squares / count_positive) - local_mean**2, 0
    )

    local_std = np.sqrt(np.maximum(local_var, 0))

    # Calculate z-scores only for positive values
    z_scores = np.zeros_like(data)
    valid_mask = np.logical_and(positive_mask, local_std > 0)
    z_scores[valid_mask] = (data[valid_mask] - local_mean[valid_mask]) / (
        local_std[valid_mask] + 1e-10
    )

    # Create mask for cosmic rays (pixels that are significantly above local mean)
    cosmic_mask = np.logical_and(z_scores > sigma, positive_mask)

    # Also mask pixels that are more than 2x the local mean
    intensity_mask = np.logical_and(data > (2 * local_mean), positive_mask)

    # Combine masks
    combined_mask = np.logical_or(cosmic_mask, intensity_mask)

    # Apply minimum intensity threshold
    combined_mask = np.logical_and(combined_mask, data > min_intensity)

    return combined_mask


def remove_cosmic_rays(image, sigma, window_size, iterations, min_intensity):
    """Apply cosmic ray detection and removal through multiple iterations.

    This function iteratively detects and removes cosmic rays from the input data.
    It uses the detect_cosmic_rays function in a loop, replacing detected cosmic
    ray pixels with NaN values. The process is repeated multiple times to catch
    cosmic rays that might be revealed after removing the most obvious ones.

    Parameters
    ----------
    image : numpy.ndarray
        Input image data array to be processed.
    sigma : float or None
        Number of standard deviations above the local mean to consider a pixel
        as a cosmic ray. If None, no cosmic ray detection is performed.
    window_size : int
        Size of the local neighborhood window for statistics calculation.
    iterations : int
        Number of times to repeat the cosmic ray detection process.
    min_intensity : float
        Minimum pixel intensity threshold for cosmic ray detection. Values below this
        threshold are not considered as cosmic rays.

    Returns
    -------
    numpy.ndarray
        Processed data array with cosmic ray pixels replaced by NaN values.
    """
    if sigma is not None:
        # Convert to float before any operations
        image = image.astype(np.float64)

        # Store counts for each iteration
        cosmic_counts = []

        # Iterate multiple times to catch all cosmic rays
        for i in range(iterations):
            # Detect cosmic rays
            cosmic_mask = detect_cosmic_rays(image, sigma, window_size, min_intensity)

            # Set cosmic ray pixels to NaN
            image[cosmic_mask] = np.nan

            # Store the count
            cosmic_counts.append(np.sum(cosmic_mask))

        # Print all counts in one line
        print(f"        Found cosmic rays: {', '.join(map(str, cosmic_counts))}")

    return image
