# Research log: Steam Audio install, validation, patched core and embodied echolocation experiments

Chronological record of every experiment, in the order it was run. Paths are relative to the repository root. The top-level README.md summarises it.

## Layout

| Path | What |
|---|---|
| `sdk/include/phonon.h` (+ `phonon_version.h`, `phonon_interfaces.h`) | Steam Audio **4.8.1** C API headers |
| `sdk/lib/libphonon.so` | Linux x64 runtime (byte-identical to the one shipped inside the Unreal plugin) |
| `sdk/doc/` | SDK HTML docs (`sdk/doc_text.txt` = plain-text dump) |
| `unreal_plugin/SteamAudio/` | Steam Audio **Unreal Engine plugin 4.8.1** (drop into `<Project>/Plugins/`) |
| `experiment/wall_experiment.c` | C program: one wall + one source + one listener, direct + reflection simulation, writes the Ambisonic IR |
| `experiment/run_scenarios.py` | runs ~100 scenarios (timing, absorption, distance, direction, scattering, occlusion, ...) |
| `experiment/analyze.py` | validates the results against image-source acoustics, writes `results/summary.md`, `results/checks.json`, `results/fig*.png` |
| `downloads/` | original zips, extracted archives and the Steam Audio core source files consulted (`downloads/src`) |
| `sdk/lib/stock/libphonon.so` | unmodified Valve binary 4.8.1 |
| `sdk/lib/patched/libphonon.so` | core rebuilt from source with the sample-accurate reconstruction patch (see below) |
| `core_src/steam-audio/` | clone of the v4.8.1 core with the patch applied; `core_src/steam-audio-4.8.1-sparse-reconstruction.patch` is the diff |
| `experiment/env_stock.sh`, `experiment/env_patched.sh` | `source` one of these to pick the library and mode |
| `experiment/results/`, `experiment/results_sparse/` | stock-mode and patched-mode results (`summary.md`, `checks.json`, `fig*.png`) |
| `pysteamaudio/` | ctypes Python binding (`README.md` there; layouts verified by `check_layout.c`) |
| `experiment/test_binding.py` | binding reproduces the C harness IR to 1e-8 |
| `experiment/incidence_sweep.py` | single wall at oblique incidence (result: `results_sparse/incidence_sweep.md`) |
| `experiment/box_room.py` | shoebox room: image-source early reflections + Eyring/Sabine reverberation (`results_box/`, `results_box_stock/`) |
| `habitat_audio/` | gym environment: Habitat-sim scene/navmesh/agent + Steam Audio acoustics per step (`README.md` there; `python -m habitat_audio.validate_env` in the `ss` conda env) |

## Unreal Engine compatibility

* The installed engine is **UE 5.1.0** (`~/unreal_engine/Engine/Build/Build.version`). Its bundled
  `Engine/Plugins/Runtime/Steam/SteamAudio` is the legacy **2.0-beta.17** plugin (Win64/Android only, old C API).
* Valve's current plugin, `steamaudio_unreal_4.8.1.zip`, requires **UE 4.27 or later** and ships Linux x64 binaries, so it is
  the one to use with UE 5.1. It embeds exactly this SDK (`Source/SteamAudioSDK/include/phonon.h`, same `libphonon.so`).
  The C API validated here is therefore the one the UE plugin calls.
* UE coordinates (cm, +X forward, +Y right, +Z up, left-handed) are converted by the plugin to Steam Audio's
  metres, +x right, +y up, -z forward, right-handed frame. The experiment uses Steam Audio's frame directly.

## Build and run

```bash
cd ~/steamaudio/experiment
make                                      # gcc -I../sdk/include ... -lphonon
source env_stock.sh                       # or: source env_patched.sh
./wall_experiment --src 0 0 0 --lis 0 0 0 --wall-axis x --wall-pos 3 --absorption 0.1 0.1 0.1 --out results/demo
python3 run_scenarios.py --results results                       # stock: ~100 scenarios in ~3 s
python3 analyze.py --mode linear --results results               # -> results/summary.md
source env_patched.sh
python3 run_scenarios.py --rays-default 262144 --results results_sparse
python3 analyze.py --mode sparse --results results_sparse        # -> results_sparse/summary.md
```

`wall_experiment` options: `--wall-axis x|y|z --wall-pos W --wall-size S --flip --no-wall --src x y z --lis x y z
--absorption a b c --transmission a b c --scattering s --no-air --rays N --bounces B --order O --duration D --sr R --frame F --out PREFIX`.
Output: `PREFIX.f32` (deinterleaved float32, (order+1)^2 Ambisonic channels, ACN/N3D) and `PREFIX.json` (settings + direct-path outputs).

How the IR is obtained: `iplSimulatorRunReflections` -> `iplSourceGetOutputs` gives an opaque `IPLReflectionEffectIR`; a unit impulse is
pushed through `iplReflectionEffectApply` (convolution type) and the output frames are concatenated. Measured convolution latency: 0 samples.

## What the simulator does (from Valve's core sources, confirmed by measurement)

* Speed of sound **340 m/s** (`propagation_medium.h`), not 343.
* Reflections are traced **from the listener**; at each hit the source irradiance is `1/(4 pi d^2)` times a BRDF: Phong lobe
  `(n+2)/(8 pi) (h.N)^n`, n = 100, weighted `(1 - scattering)`, plus Lambertian `scattering/pi cos(theta_i)`; times `(1 - absorption[band])`.
* Energy is histogrammed into **10 ms bins** (3.4 m of path) per band and Ambisonic channel; time zero of the IR is the **direct-path
  arrival**, i.e. a reflection appears at `(r_refl - r_direct)/c`, never at `r_refl/c`.
* The IR is reconstructed per bin as linearly ramped amplitude `sqrt(energy)` times a fixed uniform(-1,1) noise sequence, band-limited with
  2nd-order RBJ filters (LP 800 Hz, BP 800–8000 Hz, HP 8 kHz). The same noise sequence is used for all three bands (identical default seeds),
  so the bands add coherently.
* Air absorption in the IR is `exp(-k d)` with k = 0.0002/0.0017/0.0182 per metre, evaluated at the bin's distance `c t_bin`
  (so relative to the direct path, not the absolute reflected path length).

## Validation results, stock library (25/25 checks pass; details and tables in `experiment/results/summary.md`)

| Physics | Result |
|---|---|
| Reflection delay = (r_refl − r_direct)/c | correct 10 ms bin for 13 wall distances and 5 source distances; staircase slope 1.018 |
| Speed of sound | bin indices discriminate 340 from 343 m/s: 340 m/s predicted 5/5, 343 m/s 2/5 |
| Energy vs absorption | E(α)/E(0) = 1 − α to 4 decimals; per-band absorption matches the band-filter model to 0.02 in spectral ratio |
| Energy vs distance | E ∝ 1/r_refl² with log-log slope −1.998 and 0.24 % spread over r = 6..103 m (same-bin sweep). Energy follows the image-source path a+b, not the source-to-wall distance |
| Absolute level | E_IR / [(1+2/n)/(4π r²)] = 5.60 measured vs 5.93 predicted from the reconstruction constants (noise var 1/3 × 320 ramp samples / 4π × coherent filter gain 0.70) |
| Direction | first-order channels give the image-source direction with N3D gain √3 (measured 1.715 vs 1.732; ACN order, +Y = left, +Z = up, +X = ahead) |
| Scattering | 2×2 m panel: E(s)/E(0) = 1 + s(R − 1) with R = Lambertian/Phong = 0.453 analytic, measured within 0.015 |
| Finite panel | specular point on panel: 0.998 of infinite wall; 5 m off the panel: 4e-12 (zero); diffuse panel still reflects |
| Direct path | occlusion 0 behind the wall with transmission = material (0.5/0.3/0.1), 1 otherwise; attenuation 1/max(r, 1 m); air absorption exp(−k r) exact |
| Geometry | triangles are two-sided (flipped winding gives identical reflection); source behind wall gives no reflection; empty scene gives zero IR |
| Convergence | 65536 rays within 1e-4 of 262144 rays; 1024 rays within 4 % |

## Patched core: sample-accurate reflections (Level 2 reconstruction swap)

The core was rebuilt from the v4.8.1 source (`core_src/steam-audio`, built with `python3 build/get_dependencies.py --platform linux`
then CMake with the `--minimal` option set; no IPP, PFFFT for FFTs). Changes, all behind environment variables so the stock behaviour is the default:

| File | Change |
|---|---|
| `energy_field.cpp` | `kBinDuration` read from `STEAMAUDIO_BIN_DURATION` (seconds; default 0.01). `2.0833333e-5` gives one bin per sample at 48 kHz |
| `reconstructor.h/.cpp` | new `ReconstructionType::Sparse` selected by `STEAMAUDIO_RECONSTRUCTION=sparse`: one impulse per bin at amplitude `Y_ch(d)·sqrt(4π E)` (so a mirror reflection at path r has energy 1/r², the same scale as the direct effect's 1/r gain); energy threshold scaled with the bin duration; polarity positive for peaked arrivals and pseudo-random for spread (reverberant) energy; zero-phase, exactly complementary 3-band split (low = LP², high = HP², mid = 1 − low − high) so a frequency-independent reflection is reproduced as an exact impulse train |
| `simulation_manager.cpp`, `api_simulator.cpp`, `api_reconstructor.cpp` | use the environment-selected reconstruction type |
| `array_math.cpp` | **upstream bug fix**: the unaligned branch of the complex multiply-accumulate used an aligned SSE load on the output and segfaulted in the non-IPP build (multi-channel convolution with 513 spectrum bins) |
| `CMakeLists.txt` | dropped `-fabi-version=6`, which breaks `std::unique_ptr` with GCC ≥ 10 headers |

Experiment-side fix: the convolution effect cross-fades from its previous (empty) IR over the first frame it processes, so the IR extraction now
feeds one frame of silence before the impulse. Without it, anything arriving in the first 512 samples was ramped.

### Patched-mode results (26/26 checks, `results_sparse/summary.md`)

| Physics | Result |
|---|---|
| Arrival time | onset sample = floor((r_refl − 1 cm − r_direct)/c · fs) within 1 sample for 13 wall distances (the 1 cm is Valve's `kHitSurfaceOffset`); speed of sound fitted from arrivals: 340.01 m/s |
| Long range | 34–102 m paths: onset within 0.8 sample of 340 m/s with 1M rays (343 m/s would be 42–127 samples off). At 65536 rays only 1–2 listener rays fall in each sample-wide annulus of the far specular spot, so onsets jitter by a few samples |
| Glossy tail | the Phong lobe gives an exponential tail of excess path with mean 2w/(n+1) (6 cm at 3 m); measured centroid − arrival is 0.87–0.98 of that for w = 1.5–40 m |
| Energy vs distance | E·r² constant to 0.3 % over 3–80 m co-located and 0.26 % over 6–103 m split-distance, slope −2.003 / −1.998 |
| Absolute level | E_IR / [(1+2/n)/(4π r²)] = 12.2 vs 4π = 12.57 (Monte-Carlo lobe integral 3 % under the small-angle estimate) |
| Absorption | 1 − α to 4 decimals; per-band spectral ratios within 0.024 of the complementary-band model; air absorption per band within 0.018 of exp(−k d) at the sample's distance |
| Scattering | infinite diffuse wall raw energy ratio 2.02 vs 1.96 analytic (s = 1); 2×2 m panel within 0.016 of 1 + s(R − 1) |
| Direction, occlusion, transmission, two-sidedness, empty scene | identical conclusions to the stock run |

### Remaining caveats of the patched mode

1. Still a glossy reflection: the n = 100 lobe smears each echo over an exponential tail of ~2 % of the path length. A true mirror needs n → ∞ in `reflection_simulator.cpp` (and then more rays).
2. Still no diffraction, no reflection phase, no direct path in the IR (add a spike at t = 0 with the direct-effect gains if you need a complete IR).
3. Sample-resolution bins need dense ray sampling at long range; budget rays ∝ r² for sharp onsets.
4. Baked (probe) data written by the stock library is incompatible with a different bin duration; the parametric reverb estimator has not been re-validated with 1-sample bins.

## Python binding and box room (2026-11-04)

`pysteamaudio/steamaudio.py` wraps the C API with ctypes: scenes from any triangle mesh (`box_room`, `load_mesh` with OBJ built in
and trimesh for other formats), instanced meshes with per-frame transforms, simulator / source / listener setup, direct and reflection
runs, Ambisonic IR extraction (with the warm-up frame) and a binaural decode. All 29 struct layouts match the C compiler and the
single-wall IR through the binding equals the C harness output to 1e-8.

### Oblique incidence (new finding, `results_sparse/incidence_sweep.md`)

With source and listener at equal height above the wall and separated laterally, the reflected energy times r² is
0.995, 0.962, 0.864, 0.707, 0.502, 0.346, 0.183 at θ = 0, 15, 30, 45, 60, 70, 80° — exactly cos θ. Steam Audio's specular
term `(n+2)/(8π)(h·N)^n` lacks the 1/cos θ Jacobian that makes a Blinn-Phong lobe behave like a mirror, so **grazing reflections are
too weak by cos θ relative to the image-source model** (half the energy at 60°). The onset timing is unaffected.

### Box room 6 × 4 × 3 m (`results_box/summary.md`, patched sparse mode, 262144 rays; 7/7 checks)

| Test | Result |
|---|---|
| First-order echoes | all 6 start exactly at the image-source sample (energy rise 10× to 10¹⁵ at the predicted onset) |
| Echo energies | window energies within 15 % of the image-source model once cos θ at the last wall is included (0.92–1.15); against a mirror model 0.70–1.04 |
| Echo directions | energy-weighted direction vectors of each window within 0.15 of the model |
| Energy decay 0–40 ms | within 1.05 dB of the 3-bounce cos θ image-source model; total early energy 0.94 of it, 0.71 of the mirror model |
| Reverberation, diffuse walls (s = 1) | Schroeder T60 / Eyring = 0.91, 1.04, 1.11 for α = 0.1, 0.3, 0.5 |
| Reverberation, specular walls (s = 0) | T60 / Eyring = 1.05, 1.17, 1.24 (a specular shoebox is not a diffuse field) |
| Steam Audio's parametric RT60 estimator | agrees with the Schroeder measurement of its own IR to 1 %, both on the patched and the stock library (`results_box_stock/`) |

Each room simulation (65536–262144 rays, up to 190 bounces, 16 threads) takes 0.1–0.3 s, so on-policy RL at a few hundred
environment steps per second is realistic.

## Habitat audio-navigation environment (2026-11-04)

`habitat_audio/SteamAudioNavEnv` runs in the `ss` conda env (habitat-sim 0.2.2, sound-spaces). Habitat supplies the scene,
navmesh and agent motion; Steam Audio computes direct path + reflections on the real scene mesh every step and the observation is
SoundSpaces' binaural spectrogram (65 × 26 × 2) of a 1 s clip convolved with the binaural RIR. Validation on apartment_1
(382 k triangles), `habitat_audio/results/summary.md`, 5/5 checks:

| Test | Result |
|---|---|
| Scripted shortest-path oracle | 5/5 episodes succeed, SPL 1.00 |
| Throughput | 19 env steps/s including audio (16384 rays, 12 bounces, 0.5 s IR, 8 threads); env creation 2 s with cached mesh |
| Distance cue | received RIR energy vs distance: Spearman ρ = −0.93 over 138 unoccluded steps; occluded steps carry 0.17× the energy at equal distance |
| Lateral cue | early-window (5 ms) ILD sign agrees with the source side on 100 % of lateral steps; turning in place next to a source, ILD follows sin(azimuth) with r = 0.98 (−5.8 to +5.4 dB) |
| Reverberation dilution | whole-RIR energy ILD agrees only 77 % and spans ±0.7 dB: a learning agent must use onsets, as humans do |

Found and fixed on the way: the Ambisonics decoder, like the convolution effect, interpolates from a default state over its first
frame, so a silent warm-up frame is fed before every render (otherwise lateralisation is wrong for sounds in the first 10 ms).

## PPO audio-navigation agent (2026-11-04)

`habitat_audio/ppo_train.py` is a self-contained recurrent PPO (SoundSpaces-style AudioCNN on the 2 × 65 × 26 spectrogram, previous-action
embedding, GRU-512, actor/critic; 8 spawn-process environments, 128-step rollouts, 4 epochs × 4 env-minibatches, lr 2.5e-4, entropy 0.02).
Training settings: apartment_1, telephone clip, geodesic start distance 1–8 m, 200-step episodes, 2048 rays × 4 bounces × 0.3 s IR per
step (100 env steps/s per process, ~230 steps/s aggregate; 1M steps in 75 min). Launch with `bash habitat_audio/launch_train.sh <out> --steps 1000000 --envs 8`.
Curves: `habitat_audio/runs/ppo_apartment1/learning_curves.png`; evaluation `python -m habitat_audio.ppo_eval`.

| Agent (100 unseen start/goal pairs, 1–8 m) | success | SPL | mean length |
|---|---|---|---|
| random | 0.02 | 0.01 | 24 |
| PPO, greedy | 0.75 | 0.67 | 81 |
| PPO, sampled | 0.79 | 0.66 | 74 |
| oracle (geodesic follower) | 1.00 | 1.00 | 33 |
| PPO, sampled, 8–15 m (outside the training range, 50 pairs) | 0.34 | 0.27 | 159 |

The training curve rises from 0 (the untrained policy stops immediately) through 25 % at 120k steps, 60 % at 290k and plateaus
around 85 % after 500k steps; policy entropy settles near 0.5 nats.

## Echolocation experiments (2026-11-05)

Added to the environment: a self-emitted click each step (`self_click=True`) whose binaural echo response, with the HRTF decoder's
3.25 ms latency removed, puts the first echo at 2d/c of the nearest surface within 0.7 ms (`habitat_audio/validate_echo.py`); an
`echo` observation (65 × 64 × 2 log-STFT of the first 128 ms); a head-scan mode (`scan_angles=(-45, 0, 45)`, cardioid click steered
with the head, three decodes, 65 × 64 × 6); a point-goal observation; `sliding=False` so a collision stops the agent; and a
`collision_penalty`. Task: point-goal in the dark (no goal sound), 1–8 m, apartment_1. Ablation at test time replaces the echoes with
ones recorded at random other poses ("shuffled") or zeros. All numbers on 100 held-out episodes (`habitat_audio/runs/queue_results.md`).

| agent | steps | seed | success greedy / sampled | SPL (sampled) | collisions / episode (sampled) | shuffled echoes: success, collisions | zero echoes: success, collisions |
|---|---|---|---|---|---|---|---|
| echo, no penalty | 600k | 1 | 0.15 / 0.30 | 0.22 | 37 | 0.26 / 0.27, 59 | 0.15 / 0.33, 70 |
| blind, no penalty | 600k | 1 | 0.25 / 0.28 | 0.25 | 10 | – | – |
| echo, penalty 0.1 | 600k | 1 | 0.20 / 0.17 | 0.16 | 2.7 | 0.31 / 0.17, 5.3 | 0.19 / 0.23, 22 |
| echo, penalty 0.1 | 600k | 2 | 0.35 / 0.32 | 0.25 | 8.0 | 0.35 / 0.35, 20 | 0.35 / 0.32, 24 |
| head-scan echo, penalty | 600k | 1 | 0.23 / 0.24 | 0.21 | 2.4 | 0.26 / 0.17, 9.0 | 0.23 / 0.30, 53 |
| head-scan echo, penalty | 600k | 2 | 0.22 / 0.27 | 0.22 | 11.5 | 0.23 / 0.29, 27 | 0.21 / 0.24, 40 |
| blind, penalty | 600k | 1 | 0.24 / 0.18 | 0.17 | 1.4 | – | – |
| blind, penalty | 600k | 2 | 0.01 / 0.12 | 0.10 | 0.9 | – | – |
| echo, penalty | 1.5M | 1 | 0.41 / 0.44 | 0.38 | 9.7 | 0.26 / 0.27, 19.5 | 0.22 / 0.25, 46 |
| **head-scan echo, penalty** | **1.5M** | 1 | **0.51 / 0.64** | **0.49** | 12.2 | 0.40 / 0.36, 50 | 0.24 / 0.37, 64 |
| blind, penalty | 1.5M | 1 | 0.27 / 0.20 | 0.19 | 1.8 | – | – |

Learning curves for the 1.5M runs and the no-penalty pair: `habitat_audio/runs/echolocation_curves.png`.

Reading:
1. Without a collision cost the agent ignores its echoes: the ablation changes nothing.
2. With the cost (0.1 per collided step) it reads them first for wall avoidance: at 600k, removing the echoes multiplies collisions 4–20×
   while success is unchanged, in both seeds. Seed variance at 600k is about ±8 points, so the 600k success numbers alone separate nothing.
3. Given 1.5M steps the echoes are used for navigation: the blind agent plateaus near 20 % from 400k steps on, the single-pose echo
   agent reaches 44 % and the head-scan agent 64 % (SPL 0.49), three times blind. Shuffling their echoes returns both to the blind level.
4. Head scanning (a cardioid click steered to −45/0/+45° with three binaural decodes per step) is worth +20 points over a single pose
   at 1.5M, at 3× the acoustic cost per step. The blind agent's low collision counts come from stopping early (11–21-step episodes).
5. Caveat: one scene, one seed at 1.5M; the 600k seeds show the spread to expect.

## Exploration in the dark (queue 2, option 1; 2026-11-05)

No goal: 300-step episodes, +1 per newly visited 0.5 m cell, −0.01 slack, −0.1 per collision, walls stop the agent, every agent has a
bump sensor. 1M steps each on apartment_1; 100 held-out episodes (`habitat_audio/runs/queue2_results.md`):

| explorer | coverage (0.5 m cells) greedy / sampled | path [m] | collisions / episode | collisions / m | shuffled echoes |
|---|---|---|---|---|---|
| blind (bump sensor only) | 54.1 / 54.2 | 36.8 / 35.9 | 25.7 / 31.6 | 0.70 / 0.88 | – |
| single-pose echo | 39.5 / 46.0 | 23.9 / 25.8 | 17.0 / 25.2 | 0.71 / 0.98 | 31.0 / 33.4 cells, 24 / 33 collisions |
| head-scan echo | 48.7 / 49.2 | 34.9 / 33.3 | 14.6 / 17.1 | 0.42 / 0.51 | 37 / 36 cells, 52 / 55 collisions |
| scripted bump-and-turn | 49.5 | 33.2 | 25.0 | 0.75 | – |
| random | 9 | 4 | 135 | 33 | – |

Reading: with this reward a blind agent that keeps driving and absorbs bumps covers the most area; the head-scan echolocator matches
the scripted baseline's coverage at 40 % fewer collisions per metre and its collisions triple without real echoes. Echoes buy cleaner
movement before they buy coverage. Queue 3 (three scenes, auxiliary distance loss, 2M steps) tests whether both come with more training.

## Audio-goal with walls that stop the agent (queue 2, option 2; 2026-11-06)

The original audio-goal task (telephone emits, 1–8 m) with `sliding=False`, a bump sensor and the 0.1 collision penalty, 1M steps,
100 held-out episodes. Sliding off halves success relative to the SoundSpaces-style task (0.75–0.79).

| agent | success greedy / sampled | SPL (sampled) | length (sampled) | collisions / episode | shuffled echoes | zero echoes |
|---|---|---|---|---|---|---|
| hears goal, no echoes | 0.19 / 0.39 | 0.34 | 86 | 5.3 | – | – |
| hears goal + single-pose echoes | 0.27 / 0.35 | 0.33 | 58 | 4.5 | 0.29 / 0.36, collisions 9–10 | 0.31 / 0.35, collisions 4–9 |

A wash on success at 1M steps; echoes shorten successful episodes and halve collisions, the same "obstacle avoidance first" signature as
the point-goal and exploration agents at this budget.

## Three scenes + auxiliary distance loss, 2M steps (queue 3, stage 1; 2026-11-06)

Point-goal in the dark trained on apartment_1, van-gogh-room and skokloster-castle (one scene per environment process), 2M steps, head-scan
echo with an auxiliary loss predicting log(1 + distance to the nearest surface) at −90/−45/0/45/90° from the GRU state (weight 0.5,
labels from ray casts, never observed), versus the blind agent with the same scenes and budget. 100 held-out episodes per scene;
17DRP5sb8fy is an unseen MP3D house. Trained on CPU (GPU wedged by a driver fault), ~80 steps/s.

| scene | head-scan echo + aux, greedy / sampled (SPL sampled) | blind, greedy / sampled | head-scan collisions / episode (sampled) | blind collisions |
|---|---|---|---|---|
| apartment_1 (train) | 0.35 / 0.46 (0.40) | 0.29 / 0.29 | 4.4 | 7.3 |
| van-gogh-room (train) | 0.93 / 0.91 (0.89) | 0.85 / 0.84 | 1.2 | 2.0 |
| skokloster-castle (train) | 0.88 / 0.88 (0.83) | 0.73 / 0.67 | 1.8 | 3.9 |
| **17DRP5sb8fy (held out)** | 0.18 / 0.21 (0.17); shuffled echoes 0.31 / 0.23 | 0.21 / 0.24 | 3.6 | 6.4 |

Reading: on the training buildings the echo agent beats blind everywhere (15–20 points on the two harder ones, a third of the
collisions) and the aux loss made the greedy policy usable from 140k steps on. On the unseen house it sits at the blind level and the
shuffled-echo ablation changes nothing, so the navigation skill learned from echoes did not transfer with three training scenes; only the
collision reduction did. The interim checkpoint at 1.0M scored 0.36 / 0.26 on the held-out house, i.e. the second million steps improved
training-scene scores without improving transfer: more buildings, not more steps, is the next lever.

## Three scenes + auxiliary loss, exploration (queue 3, stage 2; 2026-11-06)

Same recipe for exploration in the dark (30 episodes per scene):

| scene | head-scan echo + aux, cells greedy / sampled (collisions / episode) | blind, cells (collisions) | bump-and-turn, cells (collisions) |
|---|---|---|---|
| apartment_1 (train) | 38.8 / 43.2 (7.8 / 17.1) | 34.7 / 34.6 (23.9 / 57.7) | 43.6 (26.3) |
| van-gogh-room (train) | 30.3 / 32.3 (8.3 / 19.9) | 28.5 / 26.5 (24.6 / 58.4) | 30.0 (29.3) |
| skokloster-castle (train) | 121.8 / 119.0 (1.6 / 1.1) | 93.7 / 90.1 (11.5 / 30.9) | 94.2 (17.1) |
| **17DRP5sb8fy (held out)** | 12.6 / 16.4 (13.2 / 20.6), path 9–14 m | 26.3 / 26.1 (26.3 / 60.6) | 32.6 (30.6) |

In the training buildings the echo explorer is the best agent (castle: +30 % area at a tenth of the collisions); in the unseen house it
barely moves and covers half of what touch alone does, and its ablation inverts: shuffled echoes 20.4 / 22.9 cells, zeroed echoes 29.1 / 25.7,
real echoes 12.6 / 16.4, i.e. in an unfamiliar building the genuine echoes suppress movement. Together with stage 1 this says the recipe works, but generalisation needs many
more buildings than three (the SoundSpaces practice is dozens of Matterport houses).

## Queue 3 stage 3 and overall summary (2026-11-06)

Single-pose echo + aux loss, point-goal, three scenes, 2M steps: apartment_1 0.27 / 0.28, van-gogh-room 0.94 / 0.96, castle 0.82 / 0.83,
held-out house 0.21 / 0.18 (shuffled echoes 0.17 / 0.16, zeroed 0.17 / 0.20 with 39–122 collisions). Its 1.1M interim checkpoint scored
0.34 / 0.39 on apartment_1 and 0.32 / 0.23 on the held-out house, so, as for the head-scan agent, the second million steps traded transfer for
training-scene fit. Curves: `habitat_audio/runs/queue3_curves.png`.

**What the whole study says** (all on Steam Audio 4.8.1 with the fine-bin patch, validated against image-source acoustics):

1. Agents navigate to a sounding goal from binaural spectrograms alone (75–79 % on apartment_1).
2. Self-emitted clicks give usable echoes: first-echo timing matches the nearest surface to < 1 ms, and a collision cost is what makes a
   policy read them. Without it the echoes are ignored.
3. On a single building, echolocation triples point-goal success in the dark at 1.5M steps (head scan 64 % vs blind 20 %), and the
   shuffled-echo ablation returns the agent to the blind level.
4. Head scanning with a steerable click is worth about +20 points over a single pose on one building; with the auxiliary distance loss the
   gap shrinks to a few points, and the aux loss makes greedy policies usable from ~140k steps.
5. On three training buildings the echo agents are the best agents everywhere (castle: point-goal 0.88 vs 0.67 blind; exploration 121 vs 94
   cells at a tenth of the collisions). On an unseen MP3D house they fall to the blind level, peaking near 1M steps and then overfitting;
   only the collision-avoidance benefit transfers. Three buildings are too few; dozens are the norm for this kind of generalisation.
6. Practical notes: Embree halves tracing cost for scan tasks; the GPU is used only by the policy; a wedged CUDA driver (Xid during an
   evaluation) cost a day of CPU-only training until a reboot; evaluations should not share the GPU with other CUDA jobs.

## Replica experiment (queue 4, launched 2026-11-06 evening)

The full Replica dataset (18 scenes, 74 GB, Habitat meshes + navmeshes) was already at
`~/sound-spaces/data/scene_datasets/Replica-Dataset`; all 18 load through the environment (scene names `replica/<name>` in the trainer).
Queue 4 (`habitat_audio/queue4.sh`, results in `runs/queue4_results.md`): 14 training scenes with one environment process per scene,
held out office_2, frl_apartment_4, hotel_0 and room_2; head-scan echo + aux loss vs blind; point-goal in the dark then exploration;
2M steps each at ~100 steps/s (14 workers, 1 Steam Audio thread each, BLAS pinned to 1 thread per worker). Each run is evaluated on the
four held-out scenes and three training scenes, echo runs also with shuffled/zeroed echoes on two held-out scenes and with their
500k/1M/1.5M checkpoints on the held-out scenes, to separate training-scene fit from transfer.

## Embree build (2026-11-05)

`sdk/lib/patched_embree/libphonon.so` is the same patched core built with `STEAMAUDIO_ENABLE_EMBREE=TRUE` (build dir
`core_src/steam-audio/core/build/linux-x64-embree`). Steam Audio routes Embree scenes through ISPC kernels
(`embree_reflection_simulator.ispc`) that had their own hard-coded 10 ms bin constant, so every reflection landed in bin 0/1 with
fine bins; the patch passes `EnergyField::kBinDuration` into the kernel. With that fix the Embree tracer reproduces the default
tracer exactly: single-wall onset, energy and direction identical to 4 digits, box room 7/7 with the same ratios
(`experiment/results_box_embree/`). Speed: 262144 rays on one wall 6 ms vs 9 ms; apartment_1 env step 91 vs 82 steps/s
(single-pose click) and 34 vs 18 steps/s (head-scan, where tracing dominates). Select it with `Context(embree=True)` or
`STEAMAUDIO_EMBREE=1` plus `STEAMAUDIO_LIB` pointing at the Embree build; `habitat_audio/launch_train.sh` now does so.
The GPU cannot help here: Steam Audio's GPU paths (Radeon Rays, TrueAudio Next) are AMD OpenCL only.

## Episode videos with sound (2026-11-05)

`python -m habitat_audio.make_video --ckpt <checkpoint> --episodes N --fps 4 [--greedy] [--seed S]` renders held-out episodes of any
trained policy to `habitat_audio/videos/<run>_ep<i>.mp4` (H.264 + AAC) and a `.wav`. Panels: first-person RGB from a Habitat camera
attached only at playback (no policy sees images), habitat-lab top-down navmesh map with the trajectory (orange), heading (green),
scan directions and the source (blue), the agent's own observation (goal-sound spectrogram per ear and/or echo panels per head angle,
left | right, 0–128 ms), and a HUD (step, action, distance, geodesic, collisions, coverage). The soundtrack is what the agent hears:
the goal clip played continuously through the room response at the current pose, and/or a short click convolved with the binaural
echo response at each head angle (the three scan angles play in sequence within each step).

## Caveats found in the stock library

1. **10 ms time quantisation.** A reflection's arrival is only resolved to the 10 ms bin (3.4 m). Early reflections of nearby walls
   (< 3.4 m path difference) merge with bin 0 and smear across 0–20 ms; the IR does not reproduce a discrete echo.
2. **Fixed noise sequence.** Energy in different bins is rendered with different noise segments, so the IR energy for the *same* physical
   reflection varies ±10 % depending on which bin it lands in (see co-located distance sweep). Comparisons within one bin are exact.
3. **Linear amplitude ramps** over-weight time-spread energy by up to 1.5× relative to a single-bin spike, so raw IR energy ratios between a
   specular and a diffuse infinite wall exceed the energy-field ratio (2.8 raw vs 1.96 analytic).
4. **Air absorption in reflections** is evaluated at the delay relative to the direct sound, so for a source far from the listener the
   reflected path is under-attenuated by exp(−k r_direct).
5. The Phong lobe (n = 100) makes the reflection 2 % stronger than a perfect mirror and gives a glossy (slightly blurred) image source.
6. **First-bin doubling.** A reflection arriving within 10 ms of the direct sound lands in bin 0, which the linear reconstruction fills with a
   flat ramp instead of a ramp-up, so it is rendered at 2.0× the energy of the same reflection one bin later.
7. **Hit-surface offset.** Hit points are pushed 1 cm off the surface, shortening every reflected path by 1 cm per bounce (1.4 samples at 48 kHz).

### Queue 4 results (finished 2026-11-07 10:45; `runs/queue4_results.md`, curves `runs/queue4_curves.png`)

Two bugs surfaced and were fixed while the queue ran: the queue's eval helper passed its log name through to `ppo_eval` (every
evaluation failed, fixed and resumed as `queue4b.sh`), and periodic checkpoints were only written on every tenth update (the first run
has 500k and 2M checkpoints only). The oracle baseline hit a habitat-sim `GreedyFollowerError` on office_0; such episodes now count as
failures instead of aborting the evaluation.

Point-goal in the dark, 100 episodes per scene, greedy policy (success / SPL / collisions per episode; random ≈ 0.01–0.12):

| held-out scene | head-scan echo + aux | blind |
|---|---|---|
| office_2 | 0.34 / 0.31 / 6.1 | 0.39 / 0.38 / 3.8 |
| frl_apartment_4 | 0.43 / 0.38 / 6.9 | 0.28 / 0.28 / 3.0 |
| hotel_0 | 0.37 / 0.30 / 5.2 | 0.45 / 0.44 / 3.0 |
| room_2 | 0.39 / 0.35 / 4.2 | 0.44 / 0.43 / 4.0 |
| train scenes apartment_0 / office_0 / room_0 | 0.14 / 0.28 / 0.29 | 0.20 / 0.41 / 0.29 |

In training the echo agent is ahead (smoothed success ~0.47 vs ~0.35 for blind, `runs/queue4_curves.png`), but that lead does not survive evaluation: success is a wash on the held-out buildings (mean 0.38 vs 0.39), the blind agent has higher SPL,
episodes half as long and fewer collisions. Zeroing or shuffling the echo input of the echo agent does not reduce its success
(office_2 0.44, hotel_0 0.38) but roughly doubles its collisions (9.6–11.0): with a goal vector the echoes are only used for wall
avoidance, and a blind agent learns the same caution from the bump sensor. The 500k checkpoint already transfers as well as the 2M one.
Blind runs train about ten times faster (no acoustics; 2M steps in 45 min vs 7 h).

Exploration in the dark, 30 episodes of 300 steps per scene (coverage in 0.5 m cells / collisions per episode):

| held-out scene | echo greedy | echo sample | blind greedy | blind sample | bump-and-turn |
|---|---|---|---|---|---|
| office_2 | 12.4 / 10.1 | 25.7 / 21.5 | 19.9 / 16.1 | 25.6 / 24.9 | 26.7 / 32.2 |
| frl_apartment_4 | 36.6 / 10.0 | 39.3 / 20.4 | 24.1 / 16.2 | 34.6 / 23.2 | 34.0 / 29.9 |
| hotel_0 | 17.1 / 8.7 | 25.3 / 24.0 | 18.8 / 17.3 | 20.6 / 26.5 | 22.7 / 33.4 |
| room_2 | 27.6 / 5.8 | 37.5 / 14.1 | 19.1 / 15.5 | 30.4 / 23.8 | 31.3 / 29.9 |

Random walking covers 5–8 cells. The sampled echo explorer covers the most on every held-out building (mean 32 cells vs 28 blind and
29 bump-and-turn) with fewer collisions than either; the greedy echo explorer collides about half as often as the greedy blind one
(9 vs 16 per episode) at similar coverage. Here the ablation goes the other way from point-goal: with zeroed echoes the explorer barely
moves (9–10 cells, 5 m path) and with shuffled echoes it covers ~16, so the explorer depends on hearing the room, and that dependence
transfers to buildings it never trained in. Interim checkpoints show the collision penalty (0.1) steadily trading coverage for caution:
the 500k checkpoint covered twice as much of office_2/hotel_0 as the 2M policy at three times the collisions, so a smaller penalty or a
larger coverage reward is the obvious next knob for exploration.

Overall: with 14 training buildings, echoes do not help goal-directed navigation when a goal vector is available, but they are the
sensor the agent relies on when there is no goal vector and it must map the space by itself.

## Active sensing: sonar image + learned click beam (queue 5, launched 2026-11-07 midday)

Two changes to the echolocating agent (`habitat_audio/audio_nav_env.py`, `ppo_train.py`), motivated by the queue 4 ablations:

* **Sonar-image observation** (`echo_obs="sonar"`, key `sonar`, shape 64 x 32 x 2). The first-order ambisonic click response is used
  directly instead of its binaural render: in the sparse reconstruction every sample is one arrival with amplitude |W| and direction
  (X, Y, Z) / (sqrt(3) W) (an acoustic intensity vector), so each arrival is binned by range (64 bins of 17 cm, 0–10.9 m) and azimuth in the
  body frame (32 bins of 11.25 deg over the full circle, ahead in the centre column). Channel 0 is the horizontal amplitude, channel 1 the
  signed vertical amplitude (floor and ceiling returns), both log-compressed (`compute_sonar`). `validate_sonar.py` checks it in a
  shoebox: the four walls appear at their distances within one range bin (errors 3–11 cm) and in the right azimuth columns, the floor
  below is negative and the ceiling above positive in channel 1.
* **Learned click beam** (`beams=BEAMS`, `click_cost`). The action becomes (navigation, beam) with five beams: none (no click, zero
  observation, no cost), omni, and a narrow cos^4 beam (dipole weight 1, power 4) steered 45 deg left, ahead or 45 deg right. Each emitted
  click costs 0.01 reward (the slack reward is −0.01). The policy has a second actor head (`JointDist`) and an embedding of the previous
  beam so it knows which click produced the current image. Integer actions still work (first emitting beam), so the scripted baselines
  are unchanged; the evaluator reports clicks per step and the beam histogram.

One click per step at sample resolution with no HRTF render runs at ~380 steps/s with 14 workers, against ~67 for the three-click
head scan. Queue 5 (`queue5.sh`, results in `runs/queue5_results.md`): exploration in the dark on the 14 Replica training buildings with
the collision penalty lowered to 0.02; runs: sonar + learned beam, sonar with a fixed omni click, blind, and the queue 4 head-scan
spectrogram explorer, all evaluated like queue 4 (held-out buildings, ablations, interim checkpoints).

### Queue 5 results (finished 2026-11-08 06:38; `runs/queue5_results.md`, curves `runs/queue5_curves.png`)

Exploration in the dark, 14 Replica training buildings, collision penalty 0.02, 2M steps each, one seed each. Held-out buildings
(office_2, frl_apartment_4, hotel_0, room_2), 30 episodes of 300 steps, mean over the four buildings:

| agent | greedy coverage (cells) | greedy collisions/ep | sampled coverage | sampled collisions/ep |
|---|---|---|---|---|
| sonar image, fixed omni click | **41.9** | 38.6 | **40.4** | 46.9 |
| head-scan binaural spectrogram | 36.7 | 18.6 | 35.2 | 36.0 |
| sonar image + learned beam | 25.6 | **8.6** | 32.2 | 19.6 |
| blind (bump sensor only) | 18.2 | 12.9 | 25.5 | 25.5 |
| bump-and-turn heuristic | 28.5 | 31.5 | | |
| queue 4 head-scan, penalty 0.1 | 23.4 | 8.6 | 31.9 | 20.0 |

* **The echo sensor is what drives exploration.** Under the identical reward the blind agent covers 18 cells (the same as at
  penalty 0.1); every echo agent covers more, and the fixed-click sonar agent covers 2.3 times as much and beats the heuristic on
  every held-out building (62 cells in frl_apartment_4). Lowering the penalty helped the echo agents only.
* **Sensor dependence.** Sonar fixed click: shuffled images cut office_2/hotel_0 coverage from 33/32 to 27/22, zeroed images
  freeze the greedy policy (never saw a blank image). Head-scan at penalty 0.02: shuffled or zeroed echoes cost only a few cells
  (27 to 21–26) but double collisions, i.e. at this penalty it uses echoes mostly for wall avoidance.
* **Coverage vs collisions is still the open knob.** The agents sit at different points of one tradeoff: the sonar fixed-click
  agent is bold (42 cells, 39 collisions), the learned-beam agent cautious (26 cells, 9 collisions), with the head-scan in between.
  With a single seed each, this spread is not attributable to beam control. In training the learned-beam agent had the best
  tradeoff (44 cells at 22 collisions vs 49 at 40 for the fixed click), but its greedy policy transferred more cautiously.
* **The learned beam did not become a strategy.** It clicks on 80–93 % of steps (the 0.01 cost barely bites) and its preferred
  beam drifts between checkpoints (omni at 500k, left at 1M, right at 2M). The sonar image already covers all azimuths, so steering
  a narrow beam only reweights it. Making beams matter needs a sensor that is directional or range-limited without them.
* **Compute.** Sonar runs train at ~380 steps/s against ~67 for the three-click binaural head scan, so 2M steps take 1.5 h instead
  of 8 h.

Next steps suggested by these runs: a collision penalty between 0.02 and 0.1 (or a per-step proximity cost from the aux distances)
for the sonar agent, 2–3 seeds per configuration before comparing sensors, and blank-image augmentation so a missing click is not
read as open space.

## Three seeds at collision penalty 0.05 (queue 6, finished 2026-11-10; `runs/queue6_results.md`, `runs/queue6_summary.png`)

Exploration in the dark on the 14 Replica training buildings, collision penalty 0.05, 2M steps, seeds 1–3 per agent. The three echo
agents were trained with 5 % blank echo observations (`--echo-dropout 0.05`) so that a missing echo is not read as open space; this
differs from queue 5 in two ways at once (penalty and augmentation). Evaluation: 30 episodes of 300 steps on each held-out building,
averaged over the four, then mean ± standard deviation across seeds (`summarize_seeds.py`):

| agent | greedy coverage (cells) | greedy collisions/ep | sampled coverage | sampled collisions/ep |
|---|---|---|---|---|
| sonar image, fixed omni click | **37.0 ± 1.5** | 17.5 ± 6.7 | **38.4 ± 0.8** | 26.4 ± 7.4 |
| sonar image + learned beam | 33.6 ± 4.7 | **13.2 ± 2.4** | 36.6 ± 2.2 | **24.0 ± 4.0** |
| head-scan binaural spectrogram | 26.6 ± 3.3 | 17.4 ± 3.6 | 31.1 ± 1.9 | 32.5 ± 5.1 |
| blind (bump sensor) | 24.5 ± 3.9 | 20.6 ± 5.3 | 27.8 ± 1.4 | 31.3 ± 4.6 |
| bump-and-turn heuristic | 28.1 | 31.8 | | |

* **The sonar image is the better echo sensor.** Both sonar agents beat blind by 9–12 cells (2–3 blind standard deviations) and beat
  the heuristic on coverage with about half its collisions. The head-scan binaural agent, at five times the compute per step, is only
  level with blind; its three seeds disagree on whether real echoes help (seed 1 moved more with blanked echoes, seeds 2–3 less).
* **Penalty 0.05 is a better operating point than 0.02.** The fixed-click sonar agent kept almost all its coverage (41.9 single seed at
  0.02 vs 37.0 ± 1.5) at half the collisions (38.6 vs 17.5). Blind also improved (18.2 vs 24.5).
* **Learned beam control is within seed noise of a fixed click.** Each seed settled on a different habit (one skips 46 % of clicks and
  aims left or ahead, one always clicks left or ahead, one aims mostly right) at similar scores, consistent with the sonar image
  already covering all azimuths.
* **Blank-echo augmentation only partly works.** With echoes blanked at test time no agent freezes completely any more, but most
  seeds collapse to 8–20 cells, so the policies still depend heavily on the echoes; shuffled echoes hurt every echo agent.
* **Seeds matter.** Per-building rankings change from seed to seed and collisions vary by a factor of 2–3 between seeds, so the
  single-seed conclusions of queues 3–5 about specific buildings or small gaps should be treated as provisional.

## Map-building probe of the queue 6 explorers (queue 7 part A, 2026-11-10; `habitat_audio/probe_map.py`, `runs/probe/probe_summary.md`)

Question: does an explorer's recurrent state hold a map? Each of the 12 queue 6 agents (4 sensors × 3 seeds) was rolled out with
sampled actions in the 14 training buildings (3000 steps × 14 workers) and the 4 held-out buildings (6000 steps × 4). At every step the
GRU state h_t (512), a pooled copy of the current observation, and two labels on an 11 × 11 egocentric grid of 0.5 m cells were stored:
**local geometry** (navmesh walkable or not) and **visited** (that cell visited earlier in the episode). Linear and one-hidden-layer
(256) decoders were trained on the training buildings and scored on the held-out buildings; per-cell AUROC averaged over the 120
non-centre cells (0.5 = chance). Because visited cells are always walkable, a decoder can partly infer "visited" from visible geometry,
so the clean memory score is **visited among walkable cells**.

MLP decoders, held-out buildings, mean ± s.d. over three seeds:

| agent | geometry from h_t | geometry from current obs | visited (walkable cells) from h_t | visited (walkable cells) from current obs |
|---|---|---|---|---|
| sonar image, fixed click | 0.803 ± 0.007 | 0.832 ± 0.002 | 0.762 ± 0.006 | 0.625 ± 0.009 |
| sonar image + learned beam | 0.789 ± 0.016 | 0.779 ± 0.019 | 0.755 ± 0.010 | 0.579 ± 0.005 |
| head-scan binaural | 0.755 ± 0.016 | 0.761 ± 0.018 | 0.757 ± 0.009 | 0.594 ± 0.011 |
| blind (bump sensor) | 0.614 ± 0.002 | 0.503 ± 0.003 | **0.830 ± 0.011** | 0.515 ± 0.013 |

* **Every explorer keeps an episodic record of its own path**, readable in buildings it never trained in: visited-cell AUROC 0.76–0.83
  from the memory state against 0.52–0.63 from the current observation.
* **The blind agents remember their path best** (0.83 vs ≈0.76 for all echo agents). Without perception of the walls, tracking its own
  trajectory is the only way to avoid re-covering ground; agents that hear the room rely on it more.
* **Geometry is mostly perceived, not remembered.** For the echo agents the current observation decodes local walkable space as well as or
  slightly better than the memory state (sonar fixed click 0.83 vs 0.80), so the GRU keeps only part of what it hears. Blind agents
  hold a weak wall map built from bumps alone (0.61, current bump bit 0.50).
* Linear decoders give the same ordering at lower values (visited among walkable: blind 0.76, sonar 0.68, head-scan 0.71).

## Range-only echo sensor: does learned aiming help? (queue 7 part B, finished 2026-11-11; `runs/queue7_results.md`, `runs/queue7_summary.png`)

The sonar image already shows every direction, which made the queue 5/6 beam choice nearly irrelevant (and those beams, dipole
weight 1, power 4, were |cos θ|⁴ figure-eights that also fired backwards). Here the echo observation is a **range-only profile**
(`echo_obs="range"`: 64 bins of 17 cm, summed over all arrival directions, like a single-transducer ultrasonic aid), so direction can come
only from where the click is aimed. Beams are forward-only cardioid⁸ lobes ((1 + cos θ)/2)⁸ at 90°/45° left, ahead, 45°/90° right;
`validate_range.py` confirms in a shoebox that each beam's strongest return is the wall it points at. Four configurations, 3 seeds,
same training as queue 6 (14 Replica buildings, penalty 0.05, 5 % blank echoes, aux loss): the agent chooses the beam or no click
each step (click cost 0.01); a scripted sweep cycling through the five beams; a fixed ahead beam; an omnidirectional click.

Held-out buildings, greedy policy, mean ± s.d. over seeds:

| agent | coverage (cells) | collisions / episode | clicks / step |
|---|---|---|---|
| sonar image, fixed click (queue 6) | **37.0 ± 1.5** | 17.5 ± 6.7 | 1 |
| range + learned beam | 27.7 ± 1.4 | **15.4 ± 2.0** | 0.2–1.0 by seed (≈0.4, ≈0.95, ≈0.75) |
| range + scripted scan | 30.4 ± 0.3 | 24.4 ± 3.3 | 1 |
| range + fixed ahead beam | 32.0 ± 3.2 | 29.3 ± 11.5 | 1 |
| range + omni click | 28.5 ± 8.1 | 29.3 ± 14.4 | 1 |
| blind (queue 6) | 24.5 ± 3.9 | 20.6 ± 5.3 | 0 |
| bump-and-turn | 27.8 | 31.9 | |

* **Direction in the echo is worth about 5–9 cells.** Every range-only agent sits between blind (24.5) and the sonar image (37.0).
* **Learned aiming did not raise coverage** (27.7, below the scripted sweep and the fixed beam), **but it gave the safest explorer of
  all**: 15.4 ± 2.0 collisions, fewer than the sonar agent, with the smallest seed spread, while the fixed and omni configurations range
  from 9 to 41 collisions between seeds. The learned agents trade ground covered for caution.
* **The learned agents ration their clicks.** One seed clicks on only 20–46 % of steps; the others on 73–99 %. Preferred beams differ
  by seed (left 45° and right 90°; ahead; left 45° and 90°), with almost no use of right 45°. Zeroing the range input cuts the learned
  agents' coverage by roughly a third to a half, so the beam they choose is used, not ignored.
* **Scripted sweep vs fixed ahead:** similar coverage, but the sweep is far more consistent across seeds (± 0.3 cells) with fewer collisions.
* Overall: aiming a click is a genuine active-sensing behaviour when it is the only source of direction, and RL agents find it, but in
  this task it buys safety and sensing economy rather than coverage; a sensor that resolves direction by itself (the sonar image) remains
  clearly better.

## Memory wipe (queue 8 part A, 2026-11-11; `runs/queue8_results.md`, paper Experiment 4)

Trained explorers re-evaluated on office_2 + hotel_0 (greedy, 30 episodes each, 3 seeds) with the GRU state zeroed every N steps
(`ppo_eval --reset-every N --greedy-only`). Coverage (cells) / collisions per episode:

| agent | memory intact | erased every 20 steps | erased every step |
|---|---|---|---|
| blind | 21.3 ± 3.2 / 22.2 ± 6.1 | 18.2 ± 2.4 / 17.6 ± 2.1 | 3.2 ± 0.0 / 1.0 ± 0.0 |
| sonar image, fixed click | 25.4 ± 0.8 / 22.7 ± 9.5 | 27.5 ± 1.0 / 20.8 ± 8.6 | 20.9 ± 2.4 / 71.4 ± 6.9 |
| sonar image + learned beam | 23.3 ± 3.7 / 15.1 ± 4.3 | 23.9 ± 1.8 / 17.9 ± 4.3 | 16.3 ± 2.8 / 89.3 ± 15.5 |
| range + learned beam | 21.8 ± 1.5 / 16.9 ± 3.2 | 24.2 ± 1.8 / 18.1 ± 2.8 | 22.8 ± 1.8 / 78.6 ± 8.0 |

Only the blind agents lose coverage with a 20-step memory (all three seeds); echo agents keep 70–100 % of their coverage with no memory
at all but collide 3–6 times more; a memoryless blind agent stops after 1 m. Blind re-evaluation reproduces exactly; echo agents'
re-evaluations differ by up to ~1 cell (acoustic simulation not bit-reproducible). A full paper draft is in `paper/` (TMLR template).

## CPU-only checks while queues 8–9 train (2026-11-11)

* **Grazing-angle deficit for the agent's own click** (`habitat_audio/nogpu_checks.py`, `results/nogpu_checks.json`). Evaluating the
  engine's specular lobe by ray casting on the four held-out Replica meshes (50 poses each, 100k rays): first-bounce energy is 0.990 of
  a mirror-correct lobe on average (minimum 0.976), 0.989 (minimum 0.952) in the first 2 ms; mean incidence angle of returned energy 8.0°.
* **Reproducibility.** Steam Audio redraws its random rays every run: with 1 thread and the same simulator two identical clicks differ
  by 1.2 % in energy and 1454 of 4096 sonar cells change (8 threads: 0.9 %, 1368). Sonar-image correlation between identical clicks
  0.942 (office_2) and 0.965 (frl_apartment_4), no better with 16384 rays (0.925, 0.959); range profile 0.999; strongest cell unchanged
  in 79 of 80 pairs. The agents' echo observations are therefore noisy at a fixed pose and evaluations are not bit-reproducible.
* **Probe detail** (`habitat_audio/probe_detail.py`, `runs/probe/probe_detail.json`). Path memory is equally decodable near/far and
  ahead/behind, highest directly behind the agent (0.84 echo agents, 0.90 blind), and fades during the episode (sonar 0.91 → 0.74 → 0.67
  for steps 0–49 / 50–149 / 150–299; blind 0.95 → 0.85 → 0.74). Blind agents' walkable-space knowledge is local (0.75 within 1 m, 0.58 beyond 2 m).
* **Literature search** (research agent): closest prior work is Zhu, Rahtu, Zhao, arXiv:2207.01136 (PointGoal with GPS + binaural echoes,
  echoes help: SPL 0.547 vs 0.491 on Replica), which reports the opposite of our single-seed point-goal result; also Hu et al. IROS 2023,
  Yu et al. Neural Computation 2023, Mohan & Vanderelst SSCI 2020, Nguyen & Vanderelst SSCI 2022. Paper novelty claims rewritten.
* **Prepared, needs the GPU:** `ppo_eval --log-collisions` + `collision_repeats.py`, queued as `queue10.sh` behind queue 9.

## Click-cost sweep (queue 8 part B, finished 2026-11-12 morning; `runs/queue8_results.md`)

Range + learned-beam explorer retrained with click cost 0, 0.03, 0.1 (3 seeds each; 0.01 = queue 7). Held-out, greedy:

| click cost | coverage (cells) | collisions / episode | clicks / step (seeds 1, 2, 3) |
|---|---|---|---|
| 0 | 29.4 ± 2.6 | 20.3 ± 4.4 | 0.81, 0.95, 0.96 |
| 0.01 | 27.7 ± 1.4 | 15.4 ± 2.0 | 0.38, 0.96, 0.76 |
| 0.03 | 26.8 ± 5.8 | 17.1 ± 6.6 | 0.95, 0.34, 0.38 |
| 0.1 | 31.9 ± 0.9 | 48.2 ± 13.9 | 0.19, 0.13, 0.00 |

Click rate falls with cost (0.91 → 0.70 → 0.56 → 0.11); coverage does not (within seed noise); collisions triple at cost 0.1 (the seed
that never clicks: 62.9 per episode, far above the blind agents' 20.6). Aimed range clicks buy collision avoidance, not coverage.

## Controls for two confounds (queue 9, finished 2026-11-12 ~12:45; `runs/queue9_results.md`)

Same training as queue 6 (penalty 0.05, 3 seeds). Held-out, greedy:

| agent | coverage (cells) | collisions / episode |
|---|---|---|
| blind + auxiliary wall-distance loss | 29.9 ± 1.8 (30.3, 27.5, 31.9) | 28.0 ± 7.1 |
| blind without auxiliary loss (queue 6) | 24.5 ± 3.9 | 20.6 ± 5.3 |
| sonar image + learned forward-only beams | 35.0 ± 0.5 (34.7, 34.6, 35.6) | 15.3 ± 6.4 |
| sonar image + learned figure-of-eight beams (queue 6) | 33.6 ± 4.7 | 13.2 ± 2.4 |
| sonar image, fixed click (queue 6) | 37.0 ± 1.5 | 17.5 ± 6.7 |

* **The auxiliary loss helps the blind agent** (+5.4 cells, more collisions). Against this fair baseline the sonar image's advantage is
  +7.1 cells (+24 %), not +51 %, with 37.5 % fewer collisions; all sonar seeds still exceed all blind seeds. The head-scan agent (26.6)
  and the range-only agents of queue 7 (27.7–32.0) are not better in coverage than the fair blind baseline. Paper corrected throughout.
* **Forward-only beams** do not change the conclusion about learned aiming with the sonar image (within seed noise of the fixed click;
  click rates 0.48, 0.95, 0.92). With zeroed echoes these agents drop to 8.9 cells, with shuffled echoes to 13.3.

## Are the memoryless agents' collisions repeats? (queue 10, 2026-11-12; `runs/queue10_results.md`)

`ppo_eval --log-collisions` + `collision_repeats.py`, office_2 + hotel_0, greedy, 3 seeds. Share of collisions within 5 cm and 5° of an
earlier collision in the same episode, memory intact → erased every step: sonar fixed click 14 ± 6 % → 47 ± 20 % (collisions 20.6 → 69.4);
sonar learned beam 13 ± 3 % → 52 ± 14 % (15.9 → 88.1); range learned beam 3 ± 1 % → 18 ± 7 % (17.0 → 79.0); blind with memory 6 ± 3 %.
No repeat happens on the very next step. So roughly half of the extra collisions of memoryless sonar agents are returns to an obstacle
already hit from the same direction; the rest are at new places.
