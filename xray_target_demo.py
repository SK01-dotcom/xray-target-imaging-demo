# -*- coding: utf-8 -*-
"""
X-ray imaging analysis of a simulated fusion target shell
Author: Savan Kanani

Simulates an X-ray radiograph of a hollow spherical shell (similar to an
inertial fusion capsule), adds realistic detector effects, then recovers
the shell geometry with a documented analysis pipeline.
"""

# %% 0. Imports and settings
import numpy as np
import matplotlib.pyplot as plt
from scipy import ndimage

rng = np.random.default_rng(seed=1)   # fixed seed: results are reproducible

N = 512          # image size in pixels
PX = 0.5         # pixel size in micrometres
R_OUT = 80.0     # true outer radius of the shell (um)
R_IN = 70.0      # true inner radius of the shell (um)
MU = 0.02        # linear attenuation coefficient (1/um)

# %% 1. Simulate the target
# Coordinate grid in micrometres, centred on the target
y, x = np.mgrid[-N // 2:N // 2, -N // 2:N // 2] * PX
r = np.hypot(x, y)


def chord(R):
    """Path length of a straight X-ray through a solid sphere of radius R."""
    return 2 * np.sqrt(np.clip(R**2 - r**2, 0, None))


# Material path length through the shell = outer sphere minus inner hollow
thickness_true = chord(R_OUT) - chord(R_IN)

# %% 2. Add detector effects (what real data looks like)
# Uneven beam profile (flat field), dark offset and photon (Poisson) noise
flat = 1000 * (1 + 0.2 * np.exp(-(x**2 + y**2) / (2 * 150**2)))
dark = 50.0

raw = rng.poisson(flat * np.exp(-MU * thickness_true)) + dark   # sample image
flat_meas = rng.poisson(flat) + dark                            # image without target
dark_meas = rng.poisson(np.full_like(flat, 5)) + dark - 5       # detector with beam off

# %% 3. Flat- and dark-field correction
# Removes the uneven beam and the detector offset
denominator = flat_meas - dark_meas
transmission = np.where(denominator > 0, (raw - dark_meas) / np.maximum(denominator, 1), np.nan)
print("invalid pixels: %.1f%%" % (100 * np.isnan(transmission).mean()))
# Fill invalid pixels with the mean so the Gaussian filter does not spread NaN
transmission = np.where(np.isnan(transmission), np.nanmean(transmission), transmission)

# %% 4. Noise reduction and thickness recovery (Beer-Lambert law)
transmission_smooth = ndimage.gaussian_filter(transmission, sigma=1.5)
thickness_meas = -np.log(np.clip(transmission_smooth, 1e-6, None)) / MU

# %% 5. Edge detection (where the shell boundaries are)
# Gradient magnitude with Sobel filters after extra smoothing
smooth = ndimage.gaussian_filter(thickness_meas, sigma=3)
gradient = np.hypot(ndimage.sobel(smooth, axis=0), ndimage.sobel(smooth, axis=1))
# Only keep the strongest edges (top 2% of gradients) so noise is ignored
edges = gradient > np.percentile(gradient, 98)

# %% 6. Measure the shell from the azimuthally averaged radial profile
r_bins = np.arange(0, R_OUT * 1.5, PX)
idx = np.digitize(r.ravel(), r_bins)
profile = np.array([np.nanmean(thickness_meas.ravel()[idx == i]) for i in range(1, len(r_bins))])
r_centres = r_bins[:-1] + PX / 2

# Inner radius: thickness is largest where the X-ray grazes the inner surface
r_in_meas = r_centres[np.argmax(profile)]
# Outer radius: last point where thickness is clearly above the noise floor
peak = profile.max()
r_out_meas = r_centres[np.where(profile > 0.05 * peak)[0].max()]

print(f"Inner radius: measured {r_in_meas:.1f} um, true {R_IN:.1f} um")
print(f"Outer radius: measured {r_out_meas:.1f} um, true {R_OUT:.1f} um")
print(f"Shell thickness: measured {r_out_meas - r_in_meas:.1f} um, "
      f"true {R_OUT - R_IN:.1f} um")

# %% 7. Figures
fig, ax = plt.subplots(2, 2, figsize=(10, 9))
ext = [x.min(), x.max(), y.min(), y.max()]

ax[0, 0].imshow(raw, cmap="gray", extent=ext)
ax[0, 0].set_title("1. Raw detector image")

ax[0, 1].imshow(transmission, cmap="gray", extent=ext)
ax[0, 1].set_title("2. After flat/dark correction")

ax[1, 0].imshow(thickness_meas, cmap="viridis", extent=ext)
ax[1, 0].contour(x, y, edges, levels=[0.5], colors="red", linewidths=0.5)
ax[1, 0].set_title("3. Recovered thickness + detected edges")

ax[1, 1].plot(r_centres, profile, label="measured")
ax[1, 1].plot(r[N // 2, N // 2:], thickness_true[N // 2, N // 2:], "--", label="true")
ax[1, 1].axvline(r_in_meas, color="gray", ls=":")
ax[1, 1].axvline(r_out_meas, color="gray", ls=":")
ax[1, 1].set_xlim(0, R_OUT * 1.3)
ax[1, 1].set_xlabel("radius (um)")
ax[1, 1].set_ylabel("material path length (um)")
ax[1, 1].set_title("4. Radial profile")
ax[1, 1].legend()

for a in ax.flat[:3]:
    a.set_xlabel("x (um)")
    a.set_ylabel("y (um)")

plt.tight_layout()
plt.savefig("results.png", dpi=150)
plt.show()
