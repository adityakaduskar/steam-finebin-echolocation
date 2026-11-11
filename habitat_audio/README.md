# habitat_audio — Steam Audio acoustics inside a Habitat gym environment

`SteamAudioNavEnv` is a `gym.Env` (gym 0.23 API, as used by habitat-lab 0.2.2 / SoundSpaces) for audio-goal navigation:

* **Habitat-sim** loads the scene, navmesh and agent; actions are `0 stop, 1 move_forward (0.25 m), 2 turn_left (10°), 3 turn_right`
  (SoundSpaces order). Optional `rgb` / `depth` observations from Habitat's sensors.
* **Steam Audio** (patched core, sample-accurate sparse reconstruction) computes the acoustics at every step on the *actual* scene
  mesh: direct path (distance attenuation, air absorption, raycast occlusion, transmission) and ray-traced reflections
  (`rays`, `bounces`, `ir_duration` configurable), giving a first-order Ambisonic room impulse response which is decoded binaurally
  with Steam Audio's HRTF at 24 kHz, resampled to 16 kHz and convolved with a 1 s SoundSpaces source clip.
* **Observation** `spectrogram`: SoundSpaces' AudioGoalSensor features exactly (|STFT| 512/160/400, 4×4 mean pooling, log1p),
  shape (65, 26, 2). Also exposed per step: `env.last_ir` (Ambisonic RIR, world frame, direct path included at t = 0),
  `env.last_rir` (binaural RIR at 16 kHz), `env.last_direct` (occlusion etc.).
* **Reward** (SoundSpaces AudioNav): −0.01 per step + geodesic distance reduction + 10 on `stop` within `success_distance` (1 m).
  `info` carries geodesic and euclidean distance, success, SPL, occlusion.
* `env.oracle_action()` is Habitat's greedy geodesic follower (scripted expert); `env.source_bearing_deg()` gives the ground-truth
  azimuth/elevation of the source in the listener frame for analysis.

```bash
conda activate ss          # habitat-sim 0.2.2 + sound-spaces; LD_PRELOAD of the system libstdc++ is set in this env
cd ~/steamaudio && python -m habitat_audio.validate_env [scene.glb]     # oracle + random episodes, cue checks, figure
```

```python
import sys; sys.path.insert(0, "/home/adityakaduskar/steamaudio")
from habitat_audio import SteamAudioNavEnv
env = SteamAudioNavEnv("~/sound-spaces/data/versioned_data/habitat_test_scenes_1.0/apartment_1.glb", rgb=True, image_size=128)
obs = env.reset()
obs, reward, done, info = env.step(env.oracle_action())
```

Scene meshes come from the GLB through trimesh and are placed in Habitat's frame automatically (`scene_mesh.py` tests the candidate
rotations against the navmesh: the frame under which navmesh vertices rest on a mesh floor wins; apartment_1 needs Rx(−90°)).
Converted meshes are cached in `habitat_audio/cache/`. Any Habitat scene with a navmesh works (MP3D, Replica, HM3D, your own GLBs);
materials are one "generic" Steam Audio material for the whole scene unless you pass `material=`.

Things to know:
* Steam Audio's default HRTF only initialises at 24, 44.1 or 48 kHz, hence the 24 kHz simulation and the resample to 16 kHz.
* Both the convolution effect and the Ambisonics decoder interpolate from a default state over their first frame; the binding feeds a
  silent warm-up frame to each so early arrivals and lateralisation are correct.
* The reflections IR is world-frame Ambisonics with t = 0 at the direct arrival and no direct sound; the env adds the direct spike
  (encoded ACN/N3D: W = a, Y = −√3·a·dx, Z = √3·a·dy, X = −√3·a·dz) before decoding.
* Speed: ~18–25 env steps/s on apartment_1 (382 k triangles) with 16384 rays × 12 bounces × 0.5 s IR on 8 threads; lower `rays`
  or `bounces` for faster RL, raise them for cleaner late reverberation.
