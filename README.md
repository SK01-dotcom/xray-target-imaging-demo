# xray-target-imaging-demo
Simulated X-ray radiography of a fusion target shell with a documented analysis pipeline in Python
## Observations
- **Smoothing trade-off:** stronger Gaussian smoothing (sigma 0.5 → 5) pushed both
  detected edges outward and changed the measured shell thickness from 9.5 to
  11.0 µm. Smoothing suppresses noise but blurs sharp boundaries, so sigma has
  to be chosen with the feature size in mind.
- **Resolution limit:** shells down to about 2 µm were measured within 0.5 µm.
  A 1 µm shell was measured as 2 µm, because at 0.5 µm per pixel it spans only
  two pixels.
- **Low-dose failure and fix:** the original pipeline crashed at 10 photons per
  pixel, because pixels with no counts in the flat field caused division by
  zero. I masked those pixels, replaced them with the mean before smoothing, and
  used a NaN-safe average in the radial profile. The pipeline now works down to
  about 3 photons per pixel (15% invalid pixels) and fails at 1 photon per pixel
  (38% invalid).
- **Why noise matters less than expected:** between 30 and 10000 photons per
  pixel the measured radii did not change, because the azimuthal average
  combines thousands of pixels at each radius. The remaining 0.5 µm error comes
  from smoothing, not from noise.
