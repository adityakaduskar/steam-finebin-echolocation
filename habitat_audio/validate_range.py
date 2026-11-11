"""Forward-beam range sensor check in a shoebox: with a cardioid^8 click aimed at a wall, the strongest early return of the
range-only profile must come from that wall, and the wall behind the agent (2.5 m) must stay weak for every forward beam."""
import os, sys, numpy as np
sys.path.insert(0, os.path.expanduser("~/steamaudio"))
from habitat_audio.audio_nav_env import compute_range, AUDIO_SR, SONAR_BINS, ECHO_SECONDS, SteamAudioNavEnv
from pysteamaudio import steamaudio as sa
SIZE = (6.0, 3.0, 8.0); LIS = np.array([1.5, 1.0, -2.5]); AHEAD = np.array([0, 0, -1.0]); UP = np.array([0, 1.0, 0])
V, T, F = sa.box_room(SIZE, origin=(0, 0, -8.0))
ctx = sa.Context(); scene = sa.Scene(ctx); scene.add_mesh(V, T, [sa.Material.of((0.1, 0.2, 0.3), 0.05, (0.1, 0.05, 0.03))]); scene.commit()
sim = sa.Simulator(ctx, scene, max_rays=16384, max_duration=0.3, max_order=1, sampling_rate=AUDIO_SR, frame_size=256, threads=8, max_sources=1)
src = sim.add_source(); sim.commit(); m = ECHO_SECONDS * 340.0 / 2 / SONAR_BINS[0]
walls = {"left90": 1.5, "left45": None, "ahead": 5.5, "right45": None, "right90": 4.5}; behind = 2.5; ok = True
print("| beam | strongest return [m] | expected wall [m] | behind-wall level / peak |"); print("|---|---|---|---|")
for name, yaw in [("left90", 90), ("left45", 45), ("ahead", 0), ("right45", -45), ("right90", -90)]:
    a = SteamAudioNavEnv.rotated(AHEAD, UP, yaw)
    sim.set_listener(LIS, ahead=AHEAD, up=UP, num_rays=16384, bounces=1, duration=0.3, order=1, irradiance_min=0.1)
    src.set_inputs(LIS, ahead=a, up=UP, air_absorption=False, dipole_weight=0.5, dipole_power=8.0); sim.run_direct(); sim.run_reflections()
    r = compute_range(sim.extract_ir(src, 0.3, 1)); pk = int(np.argmax(r)); b = int(behind / m)
    rel = r[b - 1:b + 2].max() / r.max(); exp = walls[name]
    if exp is not None: ok &= abs((pk + 0.5) * m - exp) <= 2 * m
    ok &= rel < 0.5
    print(f"| {name} | {(pk + 0.5) * m:.2f} | {exp if exp else '-'} | {rel:.2f} |")
print("RANGE BEAMS", "OK" if ok else "FAILED")
