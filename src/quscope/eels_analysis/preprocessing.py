"""Preprocessing utilities for EELS data analysis."""

import numpy as np


def preprocess_eels_data(spectrum_data, normalize=True, background_subtract=False):
    """Preprocess EELS spectrum data for quantum analysis.

    Args:
        spectrum_data (numpy.ndarray): Raw EELS spectrum data.
        normalize (bool): Whether to normalize the data.
        background_subtract (bool): Whether to perform background subtraction.

    Returns:
        numpy.ndarray: Preprocessed EELS data.
    """
    # Make a copy to avoid modifying the original data
    processed_data = spectrum_data.copy()

    # Background subtraction if requested
    if background_subtract:
        # Simple background subtraction method (can be improved)
        background = np.min(processed_data)
        processed_data = processed_data - background

    # Normalize if requested
    if normalize:
        # Normalize to [0, 1] range
        data_min = np.min(processed_data)
        data_max = np.max(processed_data)
        if data_max > data_min:  # Avoid division by zero
            processed_data = (processed_data - data_min) / (data_max - data_min)

    return processed_data


def extract_eels_features(spectrum_data, energy_axis, peak_positions=None):
    """Extract relevant features from EELS spectrum for quantum processing.

    Args:
        spectrum_data (numpy.ndarray): Preprocessed EELS spectrum data.
        energy_axis (numpy.ndarray): Energy values corresponding to spectrum data.
        peak_positions (list): Optional list of known peak positions to extract.

    Returns:
        dict: Dictionary of extracted features.
    """
    features = {}

    # Basic statistical features
    features["mean"] = np.mean(spectrum_data)
    features["std"] = np.std(spectrum_data)
    features["max"] = np.max(spectrum_data)
    features["max_position"] = energy_axis[np.argmax(spectrum_data)]

    # Extract specific peaks if provided
    if peak_positions is not None:
        peak_intensities = {}
        for peak in peak_positions:
            # Find the closest point in the energy axis
            idx = np.abs(energy_axis - peak).argmin()
            peak_intensities[peak] = spectrum_data[idx]
        features["peak_intensities"] = peak_intensities

    return features
