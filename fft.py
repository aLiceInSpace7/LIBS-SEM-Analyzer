import numpy as np
from scipy import fftpack
from scipy.stats import entropy
import matplotlib.pyplot as plt
import cv2
from gui.msg import show_msg
from qtpy.QtWidgets import QMessageBox

def analyze_fft(image, scale_nm_per_px=10.87):
    """Main analysis: Period, Orientation, Modulation"""
    if image.size < 100:
        return 0.0, 0.0, 0.0
    
    fft_img = fftpack.fft2(image)
    fft_shift = fftpack.fftshift(fft_img)
    power_raw = np.abs(fft_shift)**2
    power_log = np.log1p(power_raw) # For display
    
    # 4. Calculate Spectral Entropy
    h, w = power_raw.shape
    cy, cx = h // 2, w // 2
    ps_no_dc = power_raw.copy()
    ps_no_dc[cy, cx] = 0 

    with plt.style.context('dark_background'):
        fig, ax = plt.subplots()
        ax.imshow(ps_no_dc, cmap='inferno')
        ax.set_title("2D-FFT Power Spectrum")
        plt.show()
    
    # Normalize power spectrum to form a probability distribution
    ps_flat = ps_no_dc.flatten()
    ps_sum = np.sum(ps_flat)
    
    if ps_sum > 0:
        ps_prob = ps_flat / ps_sum
        spec_entropy = entropy(ps_prob)
        # Normalize by maximum possible entropy for this resolution
        max_entropy = np.log(len(ps_prob))
        norm_regularity_entropy = 1.0 - (spec_entropy / max_entropy)
    else:
        norm_regularity_entropy = 0.0

    # 5. Calculate Peak-to-Background Ratio (PBR)
    # Exclude central low frequencies by creating a central mask
    y, x = np.ogrid[:h, :w]
    dist_from_center = np.sqrt((x - cx)**2 + (y - cy)**2)
    
    # High-pass filter mask (ignore inner 5-pixel radius)
    hpf_mask = dist_from_center > 5
    filtered_ps = power_raw * hpf_mask
    
    if np.any(filtered_ps > 0):
        peak_val = np.max(filtered_ps)
        mean_background = np.mean(filtered_ps[filtered_ps > 0])
        pbr = peak_val / mean_background
    else:
        pbr = 0.0

    print(f"Spectral Entropy Regularity (0 to 1): {norm_regularity_entropy}, Peak-to-Background Ratio (PBR): {pbr}")
    show_msg("Results",
             "Results",
             f"Spectral Entropy Regularity (0 to 1): {norm_regularity_entropy}, Peak-to-Background Ratio (PBR): {pbr}",
             QMessageBox.Icon.Information
             )

# Example Usage:
# metrics = compute_dft_regularity('your_image.png')
# print(metrics)

    
    with plt.style.context('dark_background'):
        fig, ax = plt.subplots()
        ax.imshow(power_log, cmap='inferno')
        ax.set_title("2D-FFT Power Spectrum")
        plt.show()

    cy, cx = power_raw.shape[0]//2, power_raw.shape[1]//2
    mask = np.ones_like(power_raw)
    mask[cy-10:cy+10, cx-10:cx+10] = 0
    
    y_peak, x_peak = np.unravel_index(np.argmax(power_raw * mask), power_raw.shape)

    freq_y = (y_peak - cy) / image.shape[0]
    freq_x = (x_peak - cx) / image.shape[1]
    period_px = 1 / np.sqrt(freq_y**2 + freq_x**2) if (freq_y or freq_x) else 0
    period_nm = period_px * scale_nm_per_px
    orientation = np.degrees(np.arctan2(freq_y, freq_x)) + 90

    orientation = (orientation + 180) % 180
    if orientation > 90:
        orientation = 180 - orientation
    
    return period_nm, orientation