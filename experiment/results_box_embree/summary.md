# Shoebox room 6.0 x 4.0 m floor, 3.0 m high (V = 72 m^3, S = 108 m^2, mean free path 2.67 m); source [1.7, 1.2, 1.1], listener [4.1, 1.6, 2.6]
library: /home/adityakaduskar/steamaudio/sdk/lib/patched_embree/libphonon.so  mode: sparse (sample bins)  rays: 262144

## Part 1: early reflections, alpha = 0.1, specular, 3 bounces (0.0 s simulation)
direct path: distance 2.858 m, distanceAttenuation 0.3499 (1/r = 0.3499), occlusion 1.0

First-order (single-wall) echoes. Predicted onset = floor((r - r_direct - k cm)/c * fs). Window = [onset-2, onset + 4 tau], tau = 2r/(n+1).
The room is small, so other images (orders 1-3) overlap every window; the model energy for a window therefore sums every image whose
exponential lobe tail falls inside it: E_model = sum_i E_i cos(theta_i) [exp(-max(0,lo-t_i)/tau_i) - exp(-(hi-t_i)/tau_i)], tau_i = 2 r_i/(n+1) (1+cos^2 theta_i)/2.
'rise' = energy in the 4 samples from the predicted onset / energy in the 4 samples before it (an echo starts there if >> 1).
| r [m] | onset | rise at onset | E window / model (cos theta) | E window / mirror model | model dir vector (energy-weighted mean of all images in window) | measured dir vector |
|---|---|---|---|---|---|---|
| 3.981 | 157 | 1370886785879557.2 | 0.999 | 0.703 | (-0.60,-0.70,-0.38) | (-0.59,-0.71,-0.37) |
| 4.272 | 198 | 2974.1 | 1.089 | 0.855 | (-0.55,+0.36,-0.57) | (-0.54,+0.32,-0.59) |
| 4.428 | 220 | 47.1 | 0.915 | 0.755 | (-0.54,-0.00,-0.79) | (-0.53,-0.08,-0.83) |
| 4.941 | 292 | 169930.8 | 1.086 | 0.885 | (-0.48,-0.22,+0.40) | (-0.47,-0.24,+0.30) |
| 6.004 | 442 | 24.4 | 1.150 | 1.044 | (-0.40,+0.25,-0.19) | (-0.24,+0.24,-0.23) |
| 6.391 | 497 | 10.3 | 0.949 | 0.863 | (-0.09,+0.05,-0.24) | (-0.12,-0.00,-0.24) |
  [PASS] first-order echoes start at the image-source sample (energy rise > 3x at the predicted onset): 6/6 echoes with an unambiguous onset
  [PASS] energy in each first-order echo window matches the cos(theta) image-source model within 15 %: ratios [0.999, 1.089, 0.915, 1.086, 1.15, 0.949]
  [PASS] direction vector of each first-order echo window matches the model (|err| < 0.2; windows contain several overlapping images): max |err| 0.154

Energy decay curve 0-45 ms, 3-bounce image-source models vs simulation. Total early energy: sim / mirror model = 0.709, sim / cos(theta) model = 0.938
| t [ms] | EDC mirror model [dB] | EDC cos(theta) model [dB] | EDC simulated [dB] |
|---|---|---|---|
| 5 | -0.83 | -0.83 | -0.87 |
| 10 | -2.15 | -2.12 | -2.02 |
| 15 | -6.25 | -6.08 | -6.00 |
| 20 | -9.45 | -8.70 | -8.51 |
| 25 | -14.77 | -14.03 | -13.49 |
| 30 | -16.54 | -16.01 | -16.02 |
| 35 | -18.57 | -18.46 | -17.40 |
| 40 | -25.82 | -24.62 | -24.50 |
  [PASS] energy decay curve matches the cos(theta) image-source model within 1.5 dB over 0-40 ms: max deviation 1.05 dB (mirror model: 1.32 dB)
  [PASS] total early energy (0-45 ms, orders 1-3) matches the cos(theta) image-source model within 10 %: ratio 0.938; vs mirror model 0.709

## Part 2: reverberation time (no air absorption)
Eyring: T60 = 55.26 V / (c S (-ln(1-alpha))), Sabine: 55.26 V / (c S alpha), c = 340 m/s. Measured: Schroeder backward integration of the W channel, slope fit -5..-25 dB.
| alpha | scattering | T60 Eyring [s] | Sabine [s] | measured T60 [s] | ratio meas/Eyring | Steam Audio parametric RT60 (3 bands) [s] | sim time [s] |
|---|---|---|---|---|---|---|---|
| 0.1 | 0.0 | 1.028 | 1.084 | 1.077 | 1.047 | [1.078, 1.078, 1.078] | 0.1 + 0.1 |
| 0.1 | 1.0 | 1.028 | 1.084 | 0.934 | 0.908 | [0.938, 0.938, 0.938] | 0.2 + 0.2 |
| 0.3 | 0.0 | 0.304 | 0.361 | 0.355 | 1.169 | [0.356, 0.356, 0.356] | 0.1 + 0.1 |
| 0.3 | 1.0 | 0.304 | 0.361 | 0.315 | 1.037 | [0.315, 0.315, 0.315] | 0.1 + 0.1 |
| 0.5 | 0.0 | 0.156 | 0.217 | 0.194 | 1.243 | [0.195, 0.195, 0.195] | 0.1 + 0.1 |
| 0.5 | 1.0 | 0.156 | 0.217 | 0.173 | 1.106 | [0.174, 0.174, 0.174] | 0.1 + 0.1 |
  [PASS] diffuse walls (s=1): measured T60 within 15 % of Eyring: ratios [0.908, 1.037, 1.106]
specular walls (s=0): measured/Eyring ratios [1.047, 1.169, 1.243] (a specular shoebox is not a diffuse field; axial/tangential image families decay at their own rates)
  [PASS] Steam Audio parametric RT60 estimate within 25 % of Eyring for diffuse walls: relative deviations [0.088, 0.038, 0.112]

## Summary
7/7 checks passed
