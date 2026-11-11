"""Sonar-image check in a shoebox: the first-order wall reflections of a click (source = listener) must appear at range = wall distance
and at the wall's azimuth in the body frame (ahead = -z, + azimuth = left = -x). Floor/ceiling show up in the elevation channel."""
import os, sys, numpy as np
sys.path.insert(0, os.path.expanduser("~/steamaudio"))
from habitat_audio.audio_nav_env import compute_sonar, AUDIO_SR, SONAR_BINS, ECHO_SECONDS
from pysteamaudio import steamaudio as sa
SIZE = (6.0, 3.0, 8.0); LIS = np.array([1.5, 1.0, -2.5]); AHEAD = np.array([0, 0, -1.0]); UP = np.array([0, 1.0, 0])
V, T, F = sa.box_room(SIZE, origin=(0, 0, -8.0))       # x in [0,6], y in [0,3], z in [-8,0]
ctx = sa.Context(); scene = sa.Scene(ctx); scene.add_mesh(V, T, [sa.Material.of((0.1, 0.2, 0.3), 0.05, (0.1, 0.05, 0.03))]); scene.commit()
sim = sa.Simulator(ctx, scene, max_rays=16384, max_duration=0.3, max_order=1, sampling_rate=AUDIO_SR, frame_size=256, threads=8, max_sources=1)
src = sim.add_source(); sim.commit()
sim.set_listener(LIS, ahead=AHEAD, up=UP, num_rays=16384, bounces=1, duration=0.3, order=1, irradiance_min=0.1)
src.set_inputs(LIS, ahead=AHEAD, up=UP, air_absorption=False); sim.run_direct(); sim.run_reflections()
ir = sim.extract_ir(src, 0.3, 1); img = compute_sonar(ir, AHEAD, UP)
nr, na = SONAR_BINS; m_per_bin = ECHO_SECONDS * 340.0 / 2 / nr
def col(az_deg): return int(np.floor((np.radians(az_deg) + np.pi) / (2 * np.pi) * na)) % na
# walls: (name, distance, azimuth deg in body frame)
walls = [("ahead  (z=-8)", 8.0 - 2.5, 0.0), ("behind (z=0)", 2.5, 180.0), ("left   (x=0)", 1.5, 90.0), ("right  (x=6)", 4.5, -90.0)]
print("| wall | distance m | expected (range bin, az col) | strongest cell near that column | range error m |"); print("|---|---|---|---|---|"); ok = True
for name, d, az in walls:
    c = col(az); cols = [(c - 1) % na, c, (c + 1) % na]; sub = img[:, cols, 0]; r, k = np.unravel_index(np.argmax(sub), sub.shape)
    err = (r + 0.5) * m_per_bin - d; ok &= abs(err) <= 2 * m_per_bin and sub.max() > 0.5 * img[:, :, 0].max() * 0.2
    print(f"| {name} | {d:.2f} | ({d / m_per_bin:.1f}, {c}) | ({r}, {cols[k]}) value {sub.max():.2f} | {err:+.2f} |")
el = img[:, :, 1]; rf, rc = int(1.0 / m_per_bin), int(2.0 / m_per_bin)
floor_v, ceil_v = el[rf-1:rf+2].sum(), el[rc-1:rc+2].sum(); ok &= floor_v < -0.5 and ceil_v > 0.5
print(f"elevation channel: floor (1.0 m below) sum {floor_v:+.2f} (expect < 0), ceiling (2.0 m above) sum {ceil_v:+.2f} (expect > 0)")
print(f"image max {img[:,:,0].max():.2f}, mean {img[:,:,0].mean():.3f}, nonzero cells {(img[:,:,0]>0).mean()*100:.0f}%")
print("SONAR GEOMETRY", "OK" if ok else "FAILED")
for o in (src, sim, scene, ctx):
    try: o.release()
    except Exception: pass
