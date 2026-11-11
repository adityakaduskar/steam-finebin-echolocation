# apartment_1.glb: env created in 2.1 s; mesh frame Rx(-90), 381673 triangles, navmesh bounds [[-0.9599999785423279, -1.7999999523162842, -2.5999999046325684], [6.940000057220459, 2.740000009536743, 8.140000343322754]]
observation space: Dict(rgb:Box(0, 255, (64, 64, 3), uint8), spectrogram:Box(0.0, inf, (65, 26, 2), float32))

## Oracle (shortest-path follower) episodes
| episode | geodesic start [m] | steps | success | SPL | final distance [m] | occluded steps | steps/s |
|---|---|---|---|---|---|---|---|
| 0 | 1.19 | 5 | True | 1.00 | 0.94 | 0 | 21.3 |
| 1 | 6.13 | 32 | True | 1.00 | 0.89 | 0 | 27.5 |
| 2 | 9.23 | 69 | True | 1.00 | 0.76 | 29 | 22.6 |
| 3 | 6.22 | 51 | True | 1.00 | 0.91 | 19 | 20.7 |
| 4 | 4.33 | 29 | True | 1.00 | 0.84 | 0 | 18.1 |
  [PASS] oracle reaches the goal in every episode: 5/5 successes, mean SPL 1.00
  [PASS] environment runs at >= 5 steps/s with audio (16384 rays, 12 bounces, 0.5 s IR): mean 22.0 steps/s
  [PASS] received energy decreases with distance (Spearman rho over unoccluded steps < -0.6): rho = -0.93 over 138 steps
  [PASS] early-window (5 ms) interaural level difference sign matches the source side (|azimuth| 25-155 deg, unoccluded): 100 % of 48 steps (whole-RIR energy ILD: 75 %, diluted by reverberation)
occluded steps: 48; median energy 2-6 m occluded / unoccluded = 0.18
  [PASS] turning in place next to an unoccluded source: early ILD follows sin(azimuth) (correlation > 0.8): corr = 0.98, early ILD range -5.8..5.4 dB (whole-RIR ILD corr 0.92, range -0.5..0.7 dB); source 1.6 m

## Random agent (5 episodes)
successes 0/5, mean return 0.33, mean length 25

## Summary
5/5 checks passed
