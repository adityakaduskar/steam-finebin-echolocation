# Steam Audio single-wall validation -- stock libphonon 4.8.1

Baseline: source=listener at origin, wall x=+3 m (path 6 m), absorption 0, 65536 rays, order 1, 48000 Hz
IR energy per 10 ms bin (W channel), first 5 bins: [4.716e-16 5.066e-03 6.147e-03 1.182e-08 4.823e-16]
onset bin = 1  (predicted floor((6 m / 340 m/s)/10 ms) = 1);  energy centroid = 20.12 ms

## A. Reflection arrival time vs wall distance (listener origin, source 2 m ahead, wall x=w)
| w [m] | path diff [m] | predicted delay [ms] | predicted bin | measured onset bin | centroid [ms] |
|---|---|---|---|---|---|
| 1 | 0.828 | 2.44 | 0 | 0 | 6.7 |
| 1.5 | 1.606 | 4.72 | 0 | 0 | 6.7 |
| 2 | 2.472 | 7.27 | 0 | 0 | 6.7 |
| 2.5 | 3.385 | 9.96 | 0 | 0 | 12.7 |
| 3 | 4.325 | 12.72 | 1 | 1 | 20.1 |
| 4 | 6.246 | 18.37 | 1 | 1 | 20.2 |
| 5 | 8.198 | 24.11 | 2 | 2 | 30.0 |
| 6 | 10.166 | 29.90 | 2 | 2 | 36.4 |
| 7 | 12.142 | 35.71 | 3 | 3 | 40.0 |
| 8 | 14.125 | 41.54 | 4 | 4 | 50.1 |
| 10 | 18.100 | 53.23 | 5 | 5 | 59.8 |
| 12 | 22.083 | 64.95 | 6 | 6 | 70.0 |
| 15 | 28.067 | 82.55 | 8 | 8 | 89.9 |
  [PASS] arrival bin == floor(((r_refl - r_direct)/340)/10ms) for all 13 wall distances: 13/13 match
  [PASS] linear fit centroid vs predicted delay (arrivals >= 10 ms): slope ~1 (c = 340 m/s): slope=1.024, intercept=4.9 ms (expected ~+5..10 ms from 10 ms binning; bin-0 arrivals use a flat ramp and are excluded)

## A2. IR time origin (wall x=3, source at distance d ahead)
| d [m] | r_refl [m] | bin if origin=direct arrival | bin if origin=emission | measured |
|---|---|---|---|---|
| 0 | 6.000 | 1 | 1 | 1 |
| 2 | 6.325 | 1 | 1 | 1 |
| 6 | 8.485 | 0 | 2 | 0 |
| 10 | 11.662 | 0 | 3 | 0 |
| 20 | 20.881 | 0 | 6 | 0 |
  [PASS] IR time zero is the direct-path arrival (reflection delay = (r_refl - r_direct)/c): all 5 source distances match the direct-relative prediction

## A3. Speed of sound discrimination (co-located, path = 2w, bin index differs for c=340 vs c=343)
| path [m] | bin @340 m/s | bin @343 m/s | measured |
|---|---|---|---|
| 102.45 | 30 | 29 | 30 |
| 33.85 | 9 | 9 | 9 |
| 34.15 | 10 | 9 | 10 |
| 34.6 | 10 | 10 | 10 |
| 68.3 | 20 | 19 | 20 |
  [PASS] speed of sound = 340 m/s (not 343): 340 m/s predicts 5/5 bins, 343 m/s predicts 2/5

## B. Reflected energy vs wall absorption (co-located, wall 3 m)
| alpha | E_W | E/E(0) | expected 1-alpha |
|---|---|---|---|
| 0.0 | 1.1213e-02 | 1.0000 | 1.00 |
| 0.2 | 8.9703e-03 | 0.8000 | 0.80 |
| 0.4 | 6.7277e-03 | 0.6000 | 0.60 |
| 0.6 | 4.4851e-03 | 0.4000 | 0.40 |
| 0.8 | 2.2426e-03 | 0.2000 | 0.20 |
| 0.95 | 5.6064e-04 | 0.0500 | 0.05 |
  [PASS] E(alpha)/E(0) == 1 - alpha (energy absorption coefficient): max deviation 0.0000

Per-band absorption (alpha=0.9 in one band only). Measured: IR power-spectrum ratio to the alpha=0 run, averaged over a region inside each band.
Predicted: |sum_b sqrt(1-alpha_b) H_b(f)|^2 / |sum_b H_b(f)|^2 with Steam Audio's 2nd-order RBJ band filters (LP 800 Hz, BP 800-8000 Hz, HP 8 kHz); all bands share one noise sequence so the sum is coherent.
| case | region | measured | predicted |
|---|---|---|---|
| B_abs_low | low 100-400 Hz | 0.155 | 0.150 |
| B_abs_low | mid 1500-4000 Hz | 1.148 | 1.166 |
| B_abs_low | high 12000-20000 Hz | 1.002 | 1.001 |
| B_abs_mid | low 100-400 Hz | 1.004 | 1.004 |
| B_abs_mid | mid 1500-4000 Hz | 0.029 | 0.027 |
| B_abs_mid | high 12000-20000 Hz | 1.021 | 1.022 |
| B_abs_high | low 100-400 Hz | 1.001 | 1.001 |
| B_abs_high | mid 1500-4000 Hz | 1.173 | 1.177 |
| B_abs_high | high 12000-20000 Hz | 0.160 | 0.147 |
  [PASS] absorption is applied per frequency band and matches the 2nd-order band-filter model: max |measured - predicted| spectral ratio = 0.018

## C. Reflected energy vs path length (co-located, path = 2w, air absorption disabled)
| w [m] | r_refl [m] | E_W | E*r^2 | E / [(1+2/n)/(4 pi r^2)] |
|---|---|---|---|---|
| 1.5 | 3.0 | 1.0020e-01 | 9.0178e-01 | 11.110 | (bin 0, excluded from fit)
| 2 | 4.0 | 2.7928e-02 | 4.4684e-01 | 5.505 |
| 3 | 6.0 | 1.2391e-02 | 4.4609e-01 | 5.496 |
| 4 | 8.0 | 6.9960e-03 | 4.4775e-01 | 5.516 |
| 6 | 12.0 | 3.1427e-03 | 4.5255e-01 | 5.575 |
| 8 | 16.0 | 1.9009e-03 | 4.8663e-01 | 5.995 |
| 12 | 24.0 | 8.2670e-04 | 4.7618e-01 | 5.866 |
| 16 | 32.0 | 4.4645e-04 | 4.5717e-01 | 5.632 |
| 25 | 50.0 | 2.3870e-04 | 5.9675e-01 | 7.352 |
| 40 | 80.0 | 8.5114e-05 | 5.4473e-01 | 6.711 |

Co-located sweep: log-log slope = -1.918, E*r^2 spread = 10.3 %. Each distance lands in a different 10 ms bin, and the IR uses one fixed
noise sequence, so each bin has its own noise gain (+-10 %). r=4 m and r=6 m share bin 1 and agree to 0.2 %.
  [PASS] stock quirk: an arrival inside the first 10 ms bin is rendered at ~2x energy (bin 0 uses a flat ramp instead of a ramp-up): E*r^2 at 8.8 ms (bin 0) / E*r^2 in bin 1 = 2.02

Same-bin sweep (wall x=3, listener origin, source on the wall normal at xs<=0: delay is always 2a/c = 17.6 ms, r_refl = 6 - xs), no air.
(xs=+1.5 puts the source between listener and wall: delay 8.8 ms, bin 0, so it is listed but excluded from the same-bin fit)
| xs [m] | r_refl [m] | E_W | E*r^2 |
|---|---|---|---|
| 1.5 | 4.5 | 4.4857e-02 | 9.0835e-01 |
| 0 | 6.0 | 1.2391e-02 | 4.4609e-01 |
| -3 | 9.0 | 5.4823e-03 | 4.4407e-01 |
| -6 | 12.0 | 3.0836e-03 | 4.4404e-01 |
| -9 | 15.0 | 1.9748e-03 | 4.4432e-01 |
| -17 | 23.0 | 8.4134e-04 | 4.4507e-01 |
| -27 | 33.0 | 4.0925e-04 | 4.4568e-01 |
| -47 | 53.0 | 1.5888e-04 | 4.4629e-01 |
| -77 | 83.0 | 6.4843e-05 | 4.4670e-01 |
| -97 | 103.0 | 4.2120e-05 | 4.4685e-01 |
  [PASS] E proportional to 1/r_refl^2 (same-bin sweep, r = 6..103 m): log-log slope = -1.9982; E*r^2 spread = 0.24 %
  [PASS] E proportional to 1/r_refl^2 (co-located sweep, r = 3..80 m): slope = -1.918; E*r^2 spread = 10.3 %
  [PASS] absolute IR level matches the analytic reconstruction model: measured E_W / [(1+2/n)/(4 pi r^2)] = 5.63; predicted (noise var 1/3) x (320 ramp samples) / (4 pi) x coherent filter gain 0.698 = 5.93

Air absorption inside the IR (default model, k = 0.0002/0.0017/0.0182 per m, applied per 10 ms bin at distance c*t_bin):
| w [m] | r_refl [m] | E(default air)/E(no air) measured | predicted |
|---|---|---|---|
| 1.5 | 3.0 | 0.9657 | 0.9540 |
| 2 | 4 | 0.9049 | 0.9106 |
| 3 | 6 | 0.9049 | 0.9106 |
| 4 | 8 | 0.8720 | 0.8700 |
| 6 | 12 | 0.8338 | 0.8320 |
| 8 | 16 | 0.7959 | 0.7964 |
| 12 | 24 | 0.7005 | 0.7029 |
| 16 | 32 | 0.6599 | 0.6503 |
| 25 | 50 | 0.5271 | 0.5456 |
| 40 | 80 | 0.4282 | 0.4264 |
  [PASS] air absorption in reflections = exp(-k d) per band at the bin distance: max |measured - predicted| = 0.0185

## C2. Listener-wall vs source-wall distance (wall x=3, listener origin, source on the wall normal at x=xs)
| xs [m] | source-wall b [m] | listener-wall a [m] | r_refl=a+b | E_W | E*(a+b)^2 | E*b^2 |
|---|---|---|---|---|---|---|
| -9 | 12 | 3.0 | 15.0 | 1.7870e-03 | 4.0207e-01 | 2.5732e-01 |
| -6 | 9 | 3.0 | 12.0 | 2.7903e-03 | 4.0181e-01 | 2.2602e-01 |
| -3 | 6 | 3.0 | 9.0 | 4.9609e-03 | 4.0183e-01 | 1.7859e-01 |
| 0 | 3 | 3.0 | 6.0 | 1.1213e-02 | 4.0366e-01 | 1.0092e-01 |
| 1.5 | 1.5 | 3.0 | 4.5 | 4.3317e-02 | 8.7717e-01 | 9.7463e-02 | (bin 0, excluded)
  [PASS] energy follows image-source distance (a+b), not source-wall distance b: spread of E*(a+b)^2 = 0.2 %, spread of E*b^2 = 30.9 %

## D. Reflection direction (first-order Ambisonics, ACN order, N3D). Ratio <ch*W>/<W*W>; expected sqrt(3) * (Y=-x, Z=+y, X=-z) component of image direction
| case | image dir (x,y,z) | expected (Y,Z,X) | measured ch1,ch2,ch3 |
|---|---|---|---|
| D_dir_x3 | (+1.00,+0.00,+0.00) | (-1.732,+0.000,-0.000) | (-1.715,+0.000,+0.000) |
| D_dir_x-3 | (-1.00,+0.00,+0.00) | (+1.732,+0.000,-0.000) | (+1.715,+0.000,+0.000) |
| D_dir_y3 | (+0.00,+1.00,+0.00) | (-0.000,+1.732,-0.000) | (+0.000,+1.715,+0.000) |
| D_dir_y-3 | (+0.00,-1.00,+0.00) | (-0.000,-1.732,-0.000) | (+0.000,-1.715,+0.000) |
| D_dir_z3 | (+0.00,+0.00,+1.00) | (-0.000,+0.000,-1.732) | (+0.000,+0.000,-1.715) |
| D_dir_z-3 | (+0.00,+0.00,-1.00) | (-0.000,+0.000,+1.732) | (+0.000,+0.000,+1.715) |
| D_dir_diag | (+0.71,+0.00,-0.71) | (-1.225,+0.000,+1.225) | (-1.237,-0.000,+1.194) |
  [PASS] reflection arrives from the image-source direction (ambisonic Y/Z/X channels): max |error| = 0.031 (N3D gain sqrt(3)=1.732)

## E. Scattering coefficient (co-located, wall 3 m, no air absorption)
Analytic: infinite Lambertian wall lit by a point source at height h gives irradiance 1/(8 pi h^2) at the source position;
specular (Phong n=100) gives (1+2/n)/(4 pi (2h)^2), ratio 1.961, so E(s)/E(0) = 1 + 0.961 s in the energy-field domain.
Raw IR energy over-weights time-spread energy by up to 1.5x (linear amplitude ramps), so energies are first deconvolved back to per-bin energy-field values.
| s | raw IR E/E(0) | deconvolved E/E(0) | expected 1+0.961 s | energy centroid [ms] | energy after 40 ms [%] |
|---|---|---|---|---|---|
| 0.0 | 1.000 | 1.000 | 1.000 | 20.2 | 0.0 |
| 0.5 | 2.003 | 1.726 | 1.480 | 26.3 | 5.8 |
| 1.0 | 2.774 | 2.301 | 1.961 | 28.7 | 8.5 |
(deconvolution is only approximate because each bin carries a different noise gain; used here qualitatively)

Exact test: 2 m x 2 m panel at 3 m, co-located source/listener, no air. All reflected paths (6.0-6.6 m) fall in one 10 ms bin, so IR energy ratios are exact.
Analytic: Lambertian panel irradiance = h^2/(4 pi^2) * integral dA / r^6 = 1.0208e-03; specular = 2.2547e-03; ratio R = 0.4527; expected E(s)/E(0) = 1 + s (R - 1)
| s | measured E/E(0) | expected |
|---|---|---|
| 0.0 | 1.0000 | 1.0000 |
| 0.25 | 0.8669 | 0.8632 |
| 0.5 | 0.7337 | 0.7264 |
| 0.75 | 0.6006 | 0.5896 |
| 1.0 | 0.4674 | 0.4527 |
  [PASS] scattering blends specular (Phong) and Lambertian diffuse reflection linearly: E(s)/E(0) = 1 + s (R - 1): max deviation 0.0147

## F-I. Geometry, occlusion, transmission, sidedness
  [PASS] 2x2 m panel: specular point on panel -> same energy as infinite wall: E_panel/E_infinite = 0.998
  [PASS] 2x2 m panel: specular point 5 m off the panel -> no specular reflection: E_off/E_on = 4.30e-12
  [PASS] same off-axis panel with scattering=1 -> diffuse reflection present: E_off_diffuse/E_on = 2.241e-02
  [PASS] direct occlusion: wall between source and listener -> occlusion 0, transmission = material: occlusion=0, transmission=[0.5, 0.3, 0.1]
  [PASS] direct occlusion: clear line of sight -> occlusion 1, transmission 1: occlusion=1
  [PASS] direct distance attenuation = 1/max(r, 1 m): r=6: 0.1667, r=100: 0.0100, r=0.5: 1.000
  [PASS] direct air absorption = exp(-k r), k = (0.0002, 0.0017, 0.0182) /m: r=100 m: measured [0.9802 0.8437 0.162 ], expected [0.9802 0.8437 0.162 ]
  [PASS] source behind the wall -> no reflection energy: E/E_baseline = 4.29e-12
  [PASS] wall triangles are two-sided (flipped winding gives same reflection): E_flipped/E = 1.000
  [PASS] empty scene -> IR is zero: E = 4.81e-14

## J. Ray-count convergence (co-located, wall 3 m)
| rays | E_W | E/E(262144) |
|---|---|---|
| 1024 | 1.1641e-02 | 1.0382 |
| 4096 | 1.1237e-02 | 1.0022 |
| 16384 | 1.1214e-02 | 1.0001 |
| 65536 | 1.1213e-02 | 1.0000 |
| 262144 | 1.1213e-02 | 1.0000 |
  [PASS] Monte Carlo estimate converged at 65536 rays: |E(65536)/E(262144) - 1| = 0.0000; at 1024 rays: 0.038

## Summary
25/25 checks passed
