# Steam Audio single-wall validation -- PATCHED core: sample-resolution bins + sparse reconstruction

Baseline: source=listener at origin, wall x=+3 m (path 6 m), absorption 0, 65536 rays, order 1, 48000 Hz
IR energy per 10 ms bin (W channel), first 5 bins: [6.616e-27 2.744e-02 1.334e-13 4.451e-17 5.939e-31]
onset sample = 845, peak sample = 847; image-source prediction 6 m / 340 m/s = 847.06 samples, minus the 1 cm hit-surface offset = 845.65 samples
energy centroid = 853.47 samples, i.e. 7.8 samples after the arrival: the Phong lobe's exponential tail, predicted mean excess path 2w/(n+1) = 5.9 cm = 8.4 samples

## A. Reflection arrival time vs wall distance (listener origin, source 2 m ahead, wall x=w)
| w [m] | path diff [m] | predicted delay [ms] | predicted onset sample (incl. 1 cm offset) | measured onset | error [samples] |
|---|---|---|---|---|---|
| 1 | 0.828 | 2.437 | 115 | 116 | +1 |
| 1.5 | 1.606 | 4.722 | 225 | 225 | +0 |
| 2 | 2.472 | 7.271 | 347 | 347 | +0 |
| 2.5 | 3.385 | 9.956 | 476 | 476 | +0 |
| 3 | 4.325 | 12.719 | 609 | 609 | +0 |
| 4 | 6.246 | 18.371 | 880 | 880 | +0 |
| 5 | 8.198 | 24.112 | 1155 | 1156 | +1 |
| 6 | 10.166 | 29.899 | 1433 | 1433 | +0 |
| 7 | 12.142 | 35.712 | 1712 | 1712 | +0 |
| 8 | 14.125 | 41.543 | 1992 | 1992 | +0 |
| 10 | 18.100 | 53.235 | 2553 | 2553 | +0 |
| 12 | 22.083 | 64.951 | 3116 | 3116 | +0 |
| 15 | 28.067 | 82.549 | 3960 | 3961 | +1 |
  [PASS] reflection onset sample == floor((r_refl - 1 cm - r_direct)/c * sr) within 1 sample: max |error| = 1 samples (0.021 ms)
  [PASS] speed of sound from arrival-time fit = 340 m/s: fit over 13 distances: c = 340.01 m/s, intercept = -6.2 us

## A2. IR time origin (wall x=3, source at distance d ahead)
| d [m] | r_refl [m] | onset if origin=direct arrival | onset if origin=emission | measured onset |
|---|---|---|---|---|
| 0 | 6.000 | 845 | 845 | 845 |
| 2 | 6.325 | 609 | 891 | 609 |
| 6 | 8.485 | 349 | 1196 | 349 |
| 10 | 11.662 | 233 | 1644 | 233 |
| 20 | 20.881 | 122 | 2946 | 124 |
  [PASS] IR time zero is the direct-path arrival (reflection delay = (r_refl - r_direct)/c): all 5 source distances match the direct-relative prediction within 2 samples (42 us); the emission-time hypothesis is off by hundreds to thousands of samples

## A3. Speed of sound (co-located, long paths): arrival sample vs path / c
| path [m] | predicted onset @340 m/s | @343 m/s | measured onset |
|---|---|---|---|
| 102.45 | 14462.1 | 14335.6 | 14462 |
| 33.85 | 4777.4 | 4735.6 | 4777 |
| 34.15 | 4819.8 | 4777.6 | 4819 |
| 34.6 | 4883.3 | 4840.6 | 4883 |
| 68.3 | 9640.9 | 9556.6 | 9641 |
At the default ray count the onset is off by up to 0.8 samples at 34-102 m: few listener rays land in each sample-wide annulus of the specular spot that far away.
Same geometry with 1048576 rays:
| path [m] | predicted onset @340 m/s | @343 m/s | measured onset |
|---|---|---|---|
| 102.45 | 14462.1 | 14335.6 | 14462 |
| 34.15 | 4819.8 | 4777.6 | 4819 |
| 68.3 | 9640.9 | 9556.6 | 9641 |
  [PASS] speed of sound = 340 m/s (not 343) at 34-102 m paths (1M rays): max |error| vs 340 m/s = 0.76 samples; 343 m/s would be off by 42-127 samples

## B. Reflected energy vs wall absorption (co-located, wall 3 m)
| alpha | E_W | E/E(0) | expected 1-alpha |
|---|---|---|---|
| 0.0 | 2.7436e-02 | 1.0000 | 1.00 |
| 0.2 | 2.1949e-02 | 0.8000 | 0.80 |
| 0.4 | 1.6461e-02 | 0.6000 | 0.60 |
| 0.6 | 1.0974e-02 | 0.4000 | 0.40 |
| 0.8 | 5.4871e-03 | 0.2000 | 0.20 |
| 0.95 | 1.3717e-03 | 0.0500 | 0.05 |
  [PASS] E(alpha)/E(0) == 1 - alpha (energy absorption coefficient): max deviation 0.0000

Per-band absorption (alpha=0.9 in one band only). Measured: IR power-spectrum ratio to the alpha=0 run, averaged over a region inside each band.
Predicted: |sum_b sqrt(1-alpha_b) H_b(f)|^2 / |sum_b H_b(f)|^2 with Steam Audio's 2nd-order RBJ band filters (LP 800 Hz, BP 800-8000 Hz, HP 8 kHz); all bands share one noise sequence so the sum is coherent.
| case | region | measured | predicted |
|---|---|---|---|
| B_abs_low | low 100-400 Hz | 0.107 | 0.107 |
| B_abs_low | mid 1500-4000 Hz | 0.968 | 0.980 |
| B_abs_low | high 12000-20000 Hz | 1.000 | 1.000 |
| B_abs_mid | low 100-400 Hz | 0.982 | 0.978 |
| B_abs_mid | mid 1500-4000 Hz | 0.114 | 0.113 |
| B_abs_mid | high 12000-20000 Hz | 0.943 | 0.968 |
| B_abs_high | low 100-400 Hz | 1.000 | 1.000 |
| B_abs_high | mid 1500-4000 Hz | 0.989 | 0.981 |
| B_abs_high | high 12000-20000 Hz | 0.120 | 0.111 |
  [PASS] absorption is applied per frequency band and matches the 2nd-order band-filter model: max |measured - predicted| spectral ratio = 0.024

## C. Reflected energy vs path length (co-located, path = 2w, air absorption disabled)
| w [m] | r_refl [m] | E_W | E*r^2 | E / [(1+2/n)/(4 pi r^2)] |
|---|---|---|---|---|
| 1.5 | 3.0 | 1.1078e-01 | 9.9699e-01 | 12.283 |
| 2 | 4.0 | 6.2207e-02 | 9.9531e-01 | 12.262 |
| 3 | 6.0 | 2.7601e-02 | 9.9363e-01 | 12.241 |
| 4 | 8.0 | 1.5512e-02 | 9.9279e-01 | 12.231 |
| 6 | 12.0 | 6.8884e-03 | 9.9194e-01 | 12.221 |
| 8 | 16.0 | 3.8730e-03 | 9.9149e-01 | 12.215 |
| 12 | 24.0 | 1.7204e-03 | 9.9094e-01 | 12.208 |
| 16 | 32.0 | 9.6725e-04 | 9.9047e-01 | 12.203 |
| 25 | 50.0 | 3.9560e-04 | 9.8901e-01 | 12.185 |
| 40 | 80.0 | 1.5373e-04 | 9.8389e-01 | 12.122 |

Co-located sweep: log-log slope = -2.003, E*r^2 spread = 0.34 % (no noise sequence in the patched reconstruction).

Glossy-lobe tail: the Phong lobe (n=100) spreads the reflection over an exponential tail of excess path. Weighting cos^(n+1)(theta)/r^4 over the wall gives a mean excess path of 2w/(n+1) for a=b=w.
| w [m] | arrival sample (2w - 1 cm)/c | energy centroid | centroid - arrival [samples] | predicted 2w/(n+1) -> samples | ratio |
|---|---|---|---|---|---|
| 1.5 | 422.1 | 425.8 | 3.6 | 4.2 | 0.87 |
| 2 | 563.3 | 568.3 | 5.0 | 5.6 | 0.90 |
| 3 | 845.6 | 853.4 | 7.8 | 8.4 | 0.93 |
| 4 | 1128.0 | 1138.6 | 10.6 | 11.2 | 0.94 |
| 6 | 1692.7 | 1708.8 | 16.1 | 16.8 | 0.96 |
| 8 | 2257.4 | 2279.0 | 21.6 | 22.4 | 0.97 |
| 12 | 3386.8 | 3419.5 | 32.7 | 33.5 | 0.97 |
| 16 | 4516.2 | 4559.9 | 43.6 | 44.7 | 0.98 |
| 25 | 7057.4 | 7125.3 | 67.9 | 69.9 | 0.97 |
| 40 | 11292.7 | 11399.2 | 106.5 | 111.8 | 0.95 |
  [PASS] Phong-lobe tail length (centroid - arrival) matches 2w/(n+1) within 15 %: ratio range 0.87..0.98

Same-bin sweep (wall x=3, listener origin, source on the wall normal at xs<=0: delay is always 2a/c = 17.6 ms, r_refl = 6 - xs), no air.
(xs=+1.5 puts the source between listener and wall: delay 8.8 ms, bin 0, so it is listed but excluded from the same-bin fit)
| xs [m] | r_refl [m] | E_W | E*r^2 |
|---|---|---|---|
| 1.5 | 4.5 | 4.9594e-02 | 1.0043e+00 |
| 0 | 6.0 | 2.7601e-02 | 9.9363e-01 |
| -3 | 9.0 | 1.2212e-02 | 9.8919e-01 |
| -6 | 12.0 | 6.8698e-03 | 9.8925e-01 |
| -9 | 15.0 | 4.4002e-03 | 9.9005e-01 |
| -17 | 23.0 | 1.8755e-03 | 9.9216e-01 |
| -27 | 33.0 | 9.1261e-04 | 9.9383e-01 |
| -47 | 53.0 | 3.5437e-04 | 9.9544e-01 |
| -77 | 83.0 | 1.4455e-04 | 9.9583e-01 |
| -97 | 103.0 | 9.3849e-05 | 9.9564e-01 |
  [PASS] E proportional to 1/r_refl^2 (same-bin sweep, r = 6..103 m): log-log slope = -1.9979; E*r^2 spread = 0.26 %
  [PASS] E proportional to 1/r_refl^2 (co-located sweep, r = 3..80 m): slope = -2.003; E*r^2 spread = 0.3 %
  [PASS] absolute IR level: mirror reflection energy = 1/r_refl^2 (same scale as the direct effect) x filter gain: measured E_W / [(1+2/n)/(4 pi r^2)] = 12.218; predicted 4 pi x zero-phase filter-bank gain 1.000 = 12.566

Air absorption inside the IR (default model, k = 0.0002/0.0017/0.0182 per m, applied per sample at distance c*t). Measured as the power-spectrum ratio
of the default-air IR to the no-air IR inside each band region; predicted |sum_b exp(-k_b d/2) w_b(f)|^2 with the complementary band weights, i.e. ~exp(-k_b d) per band.
| w [m] | d = 2w [m] | low 100-400 Hz meas / pred | mid 1.5-4 kHz meas / pred | high 12-20 kHz meas / pred |
|---|---|---|---|---|
| 1.5 | 3.0 | 0.999 / 0.999 | 0.995 / 0.994 | 0.948 / 0.948 |
| 2 | 4 | 0.999 / 0.999 | 0.993 / 0.992 | 0.932 / 0.931 |
| 3 | 6 | 0.999 / 0.999 | 0.989 / 0.989 | 0.900 / 0.899 |
| 4 | 8 | 0.998 / 0.998 | 0.986 / 0.985 | 0.867 / 0.867 |
| 6 | 12 | 0.997 / 0.997 | 0.979 / 0.977 | 0.808 / 0.808 |
| 8 | 16 | 0.997 / 0.996 | 0.972 / 0.970 | 0.753 / 0.752 |
| 12 | 24 | 0.995 / 0.995 | 0.958 / 0.956 | 0.651 / 0.653 |
| 16 | 32 | 0.993 / 0.993 | 0.946 / 0.942 | 0.579 / 0.567 |
| 25 | 50 | 0.989 / 0.989 | 0.907 / 0.911 | 0.428 / 0.412 |
| 40 | 80 | 0.982 / 0.982 | 0.861 / 0.863 | 0.262 / 0.244 |
  [PASS] air absorption in reflections = exp(-k d) per band at the sample's distance: max |measured - predicted| spectral ratio = 0.018

## C2. Listener-wall vs source-wall distance (wall x=3, listener origin, source on the wall normal at x=xs)
| xs [m] | source-wall b [m] | listener-wall a [m] | r_refl=a+b | E_W | E*(a+b)^2 | E*b^2 |
|---|---|---|---|---|---|---|
| -9 | 12 | 3.0 | 15.0 | 4.3811e-03 | 9.8574e-01 | 6.3087e-01 |
| -6 | 9 | 3.0 | 12.0 | 6.8390e-03 | 9.8482e-01 | 5.5396e-01 |
| -3 | 6 | 3.0 | 9.0 | 1.2153e-02 | 9.8441e-01 | 4.3752e-01 |
| 0 | 3 | 3.0 | 6.0 | 2.7436e-02 | 9.8769e-01 | 2.4692e-01 |
| 1.5 | 1.5 | 3.0 | 4.5 | 4.9344e-02 | 9.9922e-01 | 1.1102e-01 |
  [PASS] energy follows image-source distance (a+b), not source-wall distance b: spread of E*(a+b)^2 = 0.6 %, spread of E*b^2 = 48.6 %

## D. Reflection direction (first-order Ambisonics, ACN order, N3D). Ratio <ch*W>/<W*W>; expected sqrt(3) * (Y=-x, Z=+y, X=-z) component of image direction
| case | image dir (x,y,z) | expected (Y,Z,X) | measured ch1,ch2,ch3 |
|---|---|---|---|
| D_dir_x3 | (+1.00,+0.00,+0.00) | (-1.732,+0.000,-0.000) | (-1.715,-0.000,-0.000) |
| D_dir_x-3 | (-1.00,+0.00,+0.00) | (+1.732,+0.000,-0.000) | (+1.715,-0.000,+0.000) |
| D_dir_y3 | (+0.00,+1.00,+0.00) | (-0.000,+1.732,-0.000) | (+0.000,+1.715,-0.000) |
| D_dir_y-3 | (+0.00,-1.00,+0.00) | (-0.000,-1.732,-0.000) | (+0.000,-1.715,-0.000) |
| D_dir_z3 | (+0.00,+0.00,+1.00) | (-0.000,+0.000,-1.732) | (+0.000,+0.000,-1.715) |
| D_dir_z-3 | (+0.00,+0.00,-1.00) | (-0.000,+0.000,+1.732) | (-0.000,-0.000,+1.715) |
| D_dir_diag | (+0.71,+0.00,-0.71) | (-1.225,+0.000,+1.225) | (-1.237,+0.000,+1.194) |
  [PASS] reflection arrives from the image-source direction (ambisonic Y/Z/X channels): max |error| = 0.031 (N3D gain sqrt(3)=1.732)

## E. Scattering coefficient (co-located, wall 3 m, no air absorption)
Analytic: infinite Lambertian wall lit by a point source at height h gives irradiance 1/(8 pi h^2) at the source position;
specular (Phong n=100) gives (1+2/n)/(4 pi (2h)^2), ratio 1.961, so E(s)/E(0) = 1 + 0.961 s in the energy-field domain.
In the patched sparse mode the IR energy equals the energy-field energy directly, so the raw ratio is the test.
| s | raw IR E/E(0) | deconvolved E/E(0) | expected 1+0.961 s | energy centroid [ms] | energy after 40 ms [%] |
|---|---|---|---|---|---|
| 0.0 | 1.000 | 1.000 | 1.000 | 17.8 | 0.0 |
| 0.5 | 1.509 | 0.994 | 1.480 | 21.6 | 2.5 |
| 1.0 | 2.019 | 0.940 | 1.961 | 23.4 | 3.7 |
  [PASS] infinite diffuse wall: raw IR energy ratio E(s)/E(0) = 1 + 0.961 s (no reconstruction artefacts): raw ratios 1.509, 2.019 vs 1.480, 1.961

Exact test: 2 m x 2 m panel at 3 m, co-located source/listener, no air. All reflected paths (6.0-6.6 m) fall in one 10 ms bin, so IR energy ratios are exact.
Analytic: Lambertian panel irradiance = h^2/(4 pi^2) * integral dA / r^6 = 1.0208e-03; specular = 2.2547e-03; ratio R = 0.4527; expected E(s)/E(0) = 1 + s (R - 1)
| s | measured E/E(0) | expected |
|---|---|---|
| 0.0 | 1.0000 | 1.0000 |
| 0.25 | 0.8670 | 0.8632 |
| 0.5 | 0.7341 | 0.7264 |
| 0.75 | 0.6011 | 0.5896 |
| 1.0 | 0.4682 | 0.4527 |
  [PASS] scattering blends specular (Phong) and Lambertian diffuse reflection linearly: E(s)/E(0) = 1 + s (R - 1): max deviation 0.0155

## F-I. Geometry, occlusion, transmission, sidedness
  [PASS] 2x2 m panel: specular point on panel -> same energy as infinite wall: E_panel/E_infinite = 0.998
  [PASS] 2x2 m panel: specular point 5 m off the panel -> no specular reflection: E_off/E_on = 1.96e-27
  [PASS] same off-axis panel with scattering=1 -> diffuse reflection present: E_off_diffuse/E_on = 1.170e-02
  [PASS] direct occlusion: wall between source and listener -> occlusion 0, transmission = material: occlusion=0, transmission=[0.5, 0.3, 0.1]
  [PASS] direct occlusion: clear line of sight -> occlusion 1, transmission 1: occlusion=1
  [PASS] direct distance attenuation = 1/max(r, 1 m): r=6: 0.1667, r=100: 0.0100, r=0.5: 1.000
  [PASS] direct air absorption = exp(-k r), k = (0.0002, 0.0017, 0.0182) /m: r=100 m: measured [0.9802 0.8437 0.162 ], expected [0.9802 0.8437 0.162 ]
  [PASS] source behind the wall -> no reflection energy: E/E_baseline = 1.96e-27
  [PASS] wall triangles are two-sided (flipped winding gives same reflection): E_flipped/E = 1.000
  [PASS] empty scene -> IR is zero: E = 5.37e-29

## J. Ray-count convergence (co-located, wall 3 m)
| rays | E_W | E/E(262144) |
|---|---|---|
| 1024 | 2.7241e-02 | 0.9929 |
| 4096 | 2.7030e-02 | 0.9852 |
| 16384 | 2.7242e-02 | 0.9929 |
| 65536 | 2.7432e-02 | 0.9999 |
| 262144 | 2.7436e-02 | 1.0000 |
  [PASS] Monte Carlo estimate converged at 65536 rays: |E(65536)/E(262144) - 1| = 0.0001; at 1024 rays: 0.007

## Summary
26/26 checks passed
