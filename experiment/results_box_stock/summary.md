# Shoebox room 6.0 x 4.0 m floor, 3.0 m high (V = 72 m^3, S = 108 m^2, mean free path 2.67 m); source [1.7, 1.2, 1.1], listener [4.1, 1.6, 2.6]
library: /home/adityakaduskar/steamaudio/sdk/lib/stock/libphonon.so  mode: stock linear (10 ms bins)  rays: 262144

## Part 1: early reflections, alpha = 0.1, specular, 3 bounces (0.0 s simulation)
direct path: distance 2.858 m, distanceAttenuation 0.3499 (1/r = 0.3499), occlusion 1.0

First-order (single-wall) echoes. Predicted onset = floor((r - r_direct - k cm)/c * fs). Window = [onset-2, onset + 4 tau], tau = 2r/(n+1).
The room is small, so other images (orders 1-3) overlap every window; the model energy for a window therefore sums every image whose
exponential lobe tail falls inside it: E_model = sum_i E_i cos(theta_i) [exp(-max(0,lo-t_i)/tau_i) - exp(-(hi-t_i)/tau_i)], tau_i = 2 r_i/(n+1) (1+cos^2 theta_i)/2.
'rise' = energy in the 4 samples from the predicted onset / energy in the 4 samples before it (an echo starts there if >> 1).
| r [m] | onset | rise at onset | E window / model (cos theta) | E window / mirror model | model dir vector (energy-weighted mean of all images in window) | measured dir vector |
|---|---|---|---|---|---|---|
| 3.981 | 157 | 0.7 | 0.351 | 0.247 | (-0.60,-0.70,-0.38) | (-0.55,-0.03,-0.20) |
| 4.272 | 198 | 0.7 | 0.227 | 0.178 | (-0.55,+0.36,-0.57) | (-0.55,-0.03,-0.20) |
| 4.428 | 220 | 1.0 | 0.433 | 0.358 | (-0.54,-0.00,-0.79) | (-0.55,-0.03,-0.20) |
| 4.941 | 292 | 1.1 | 0.251 | 0.204 | (-0.48,-0.22,+0.40) | (-0.55,-0.03,-0.20) |
| 6.004 | 442 | 8.5 | 0.445 | 0.404 | (-0.40,+0.25,-0.19) | (-0.55,-0.03,-0.20) |
| 6.391 | 497 | 0.2 | 0.420 | 0.382 | (-0.09,+0.05,-0.24) | (-0.51,-0.03,-0.17) |

Energy decay curve 0-45 ms, 3-bounce image-source models vs simulation. Total early energy: sim / mirror model = 0.550, sim / cos(theta) model = 0.727
| t [ms] | EDC mirror model [dB] | EDC cos(theta) model [dB] | EDC simulated [dB] |
|---|---|---|---|
| 5 | -0.83 | -0.83 | -0.82 |
| 10 | -2.15 | -2.12 | -1.72 |
| 15 | -6.25 | -6.08 | -2.96 |
| 20 | -9.45 | -8.70 | -4.85 |
| 25 | -14.77 | -14.03 | -8.39 |
| 30 | -16.54 | -16.01 | -11.98 |
| 35 | -18.57 | -18.46 | -16.16 |
| 40 | -25.82 | -24.62 | -21.32 |

## Part 2: reverberation time (no air absorption)
Eyring: T60 = 55.26 V / (c S (-ln(1-alpha))), Sabine: 55.26 V / (c S alpha), c = 340 m/s. Measured: Schroeder backward integration of the W channel, slope fit -5..-25 dB.
| alpha | scattering | T60 Eyring [s] | Sabine [s] | measured T60 [s] | ratio meas/Eyring | Steam Audio parametric RT60 (3 bands) [s] | sim time [s] |
|---|---|---|---|---|---|---|---|
| 0.1 | 0.0 | 1.028 | 1.084 | 1.058 | 1.029 | [1.075, 1.075, 1.075] | 0.1 + 0.2 |
| 0.1 | 1.0 | 1.028 | 1.084 | 0.921 | 0.895 | [0.934, 0.934, 0.934] | 0.2 + 0.2 |
| 0.3 | 0.0 | 0.304 | 0.361 | 0.358 | 1.178 | [0.354, 0.354, 0.354] | 0.1 + 0.1 |
| 0.3 | 1.0 | 0.304 | 0.361 | 0.317 | 1.044 | [0.315, 0.315, 0.315] | 0.2 + 0.2 |
| 0.5 | 0.0 | 0.156 | 0.217 | 0.190 | 1.215 | [0.197, 0.197, 0.197] | 0.1 + 0.1 |
| 0.5 | 1.0 | 0.156 | 0.217 | 0.174 | 1.115 | [0.173, 0.173, 0.173] | 0.1 + 0.1 |
  [PASS] diffuse walls (s=1): measured T60 within 15 % of Eyring: ratios [np.float64(0.895), np.float64(1.044), np.float64(1.115)]
specular walls (s=0): measured/Eyring ratios [np.float64(1.029), np.float64(1.178), np.float64(1.215)] (a specular shoebox is not a diffuse field; axial/tangential image families decay at their own rates)
  [PASS] Steam Audio parametric RT60 estimate within 25 % of Eyring for diffuse walls: relative deviations [np.float64(0.092), np.float64(0.036), np.float64(0.108)]

## Summary
2/2 checks passed
