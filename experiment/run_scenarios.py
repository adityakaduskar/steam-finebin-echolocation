#!/usr/bin/env python3
"""Run the single-wall Steam Audio experiment over a battery of scenarios.
Each scenario -> results/<name>.f32 (IR, deinterleaved float32), results/<name>.json (metadata) and results/<name>.log (stdout)."""
import subprocess, sys, os, json, time
HERE = os.path.dirname(os.path.abspath(__file__))
EXE = os.path.join(HERE, "wall_experiment")
OUT = os.path.join(HERE, "results")
argv = sys.argv[1:]
if "--results" in argv:
    i = argv.index("--results"); OUT = os.path.join(HERE, argv[i+1]); del argv[i:i+2]
os.makedirs(OUT, exist_ok=True)

DEFAULT_RAYS = "65536"
if "--rays-default" in argv:
    i = argv.index("--rays-default"); DEFAULT_RAYS = argv[i+1]; del argv[i:i+2]
COMMON = ["--rays", DEFAULT_RAYS, "--bounces", "1", "--order", "1", "--duration", "1.0", "--sr", "48000", "--frame", "512"]

def S(name, *args):
    return (name, [str(a) for a in args])

scen = []
# A. timing sweep: listener at origin, source 2 m ahead (-z); wall x = w
for w in [1, 1.5, 2, 2.5, 3, 4, 5, 6, 7, 8, 10, 12, 15]:
    scen.append(S(f"A_time_w{w}", "--src", 0, 0, -2, "--lis", 0, 0, 0, "--wall-axis", "x", "--wall-pos", w, "--absorption", 0, 0, 0))
# A2. same wall, different source distances: tests IR origin = direct arrival
for d in [0, 2, 6, 10, 20]:
    scen.append(S(f"A2_origin_d{d}", "--src", 0, 0, -d, "--lis", 0, 0, 0, "--wall-axis", "x", "--wall-pos", 3, "--absorption", 0, 0, 0))
# A3. speed-of-sound discrimination: co-located, path 2w chosen so the 10 ms bin index differs for c=340 vs c=343
for path in [34.15, 68.3, 102.45, 33.85, 34.6]:
    scen.append(S(f"A3_sos_p{path}", "--src", 0, 0, 0, "--lis", 0, 0, 0, "--wall-axis", "x", "--wall-pos", path/2, "--absorption", 0, 0, 0))
# A4. same as A3 with 16x more rays (long-range sample-resolution arrivals need dense ray sampling)
for path in [34.15, 68.3, 102.45]:
    scen.append(S(f"A4_sos_hires_p{path}", "--src", 0, 0, 0, "--lis", 0, 0, 0, "--wall-axis", "x", "--wall-pos", path/2, "--absorption", 0, 0, 0, "--rays", 1048576))
# B. absorption sweep (co-located, wall at x=3, path 6 m)
for a in [0.0, 0.2, 0.4, 0.6, 0.8, 0.95]:
    scen.append(S(f"B_abs_{a}", "--src", 0, 0, 0, "--lis", 0, 0, 0, "--wall-axis", "x", "--wall-pos", 3, "--absorption", a, a, a))
scen.append(S("B_abs_low", "--src", 0, 0, 0, "--lis", 0, 0, 0, "--wall-axis", "x", "--wall-pos", 3, "--absorption", 0.9, 0, 0))
scen.append(S("B_abs_mid", "--src", 0, 0, 0, "--lis", 0, 0, 0, "--wall-axis", "x", "--wall-pos", 3, "--absorption", 0, 0.9, 0))
scen.append(S("B_abs_high", "--src", 0, 0, 0, "--lis", 0, 0, 0, "--wall-axis", "x", "--wall-pos", 3, "--absorption", 0, 0, 0.9))
# C. distance sweep (co-located): path = 2w
for w in [1.5, 2, 3, 4, 6, 8, 12, 16, 25]:
    scen.append(S(f"C_dist_w{w}", "--src", 0, 0, 0, "--lis", 0, 0, 0, "--wall-axis", "x", "--wall-pos", w, "--absorption", 0, 0, 0))
# C2. decouple listener-wall and source-wall distance (wall x=3): source on wall normal at x=xs
for xs in [-9, -6, -3, 0, 1.5]:
    scen.append(S(f"C2_split_xs{xs}", "--src", xs, 0, 0, "--lis", 0, 0, 0, "--wall-axis", "x", "--wall-pos", 3, "--absorption", 0, 0, 0))
# C3. distance sweep with air absorption disabled (clean 1/r^2 test); C4 = same with default air absorption at large distance
for w in [1.5, 2, 3, 4, 6, 8, 12, 16, 25, 40]:
    scen.append(S(f"C3_noair_w{w}", "--src", 0, 0, 0, "--lis", 0, 0, 0, "--wall-axis", "x", "--wall-pos", w, "--absorption", 0, 0, 0, "--no-air"))
for w in [25, 40]:
    scen.append(S(f"C_dist_w{w}", "--src", 0, 0, 0, "--lis", 0, 0, 0, "--wall-axis", "x", "--wall-pos", w, "--absorption", 0, 0, 0))
# E2. scattering with air absorption disabled
for s in [0.0, 0.5, 1.0]:
    scen.append(S(f"E2_scat_noair_{s}", "--src", 0, 0, 0, "--lis", 0, 0, 0, "--wall-axis", "x", "--wall-pos", 3, "--absorption", 0, 0, 0, "--scattering", s, "--no-air"))
# C4. same-bin distance sweep (no air): wall x=3, listener origin, source on wall normal at xs<=0 -> delay always 2a/c = 17.6 ms (bin 1), r_refl = 6 - xs
for xs in [1.5, 0, -3, -6, -9, -17, -27, -47, -77, -97]:
    scen.append(S(f"C4_samebin_xs{xs}", "--src", xs, 0, 0, "--lis", 0, 0, 0, "--wall-axis", "x", "--wall-pos", 3, "--absorption", 0, 0, 0, "--no-air"))
# E3. 2x2 m panel at 3 m, co-located, scattering sweep (all reflected energy lands in one 10 ms bin), no air
for s in [0.0, 0.25, 0.5, 0.75, 1.0]:
    scen.append(S(f"E3_panel_scat_{s}", "--src", 0, 0, 0, "--lis", 0, 0, 0, "--wall-axis", "x", "--wall-pos", 3, "--wall-size", 2, "--absorption", 0, 0, 0, "--scattering", s, "--no-air"))
# D. direction tests (co-located): wall on each axis side
for ax in "xyz":
    for p in [3, -3]:
        scen.append(S(f"D_dir_{ax}{p}", "--src", 0, 0, 0, "--lis", 0, 0, 0, "--wall-axis", ax, "--wall-pos", p, "--absorption", 0, 0, 0))
scen.append(S("D_dir_diag", "--src", 0, 0, -6, "--lis", 0, 0, 0, "--wall-axis", "x", "--wall-pos", 3, "--absorption", 0, 0, 0))
# E. scattering
for s in [0.0, 0.25, 0.5, 0.75, 1.0]:
    scen.append(S(f"E_scat_{s}", "--src", 0, 0, 0, "--lis", 0, 0, 0, "--wall-axis", "x", "--wall-pos", 3, "--absorption", 0, 0, 0, "--scattering", s))
# F. finite wall (2 m x 2 m) : specular point on / off the panel
scen.append(S("F_finite_on", "--src", 0, 0, 0, "--lis", 0, 0, 0, "--wall-axis", "x", "--wall-pos", 3, "--wall-size", 2, "--absorption", 0, 0, 0))
scen.append(S("F_finite_off", "--src", 0, 0, -10, "--lis", 0, 0, 0, "--wall-axis", "x", "--wall-pos", 3, "--wall-size", 2, "--absorption", 0, 0, 0))
scen.append(S("F_finite_off_diffuse", "--src", 0, 0, -10, "--lis", 0, 0, 0, "--wall-axis", "x", "--wall-pos", 3, "--wall-size", 2, "--absorption", 0, 0, 0, "--scattering", 1.0))
# G. direct path: occlusion / transmission / distance attenuation / air absorption
scen.append(S("G_occluded", "--src", 6, 0, 0, "--lis", 0, 0, 0, "--wall-axis", "x", "--wall-pos", 3, "--absorption", 0, 0, 0, "--transmission", 0.5, 0.3, 0.1))
scen.append(S("G_unoccluded", "--src", 0, 0, -6, "--lis", 0, 0, 0, "--wall-axis", "x", "--wall-pos", 3, "--absorption", 0, 0, 0, "--transmission", 0.5, 0.3, 0.1))
scen.append(S("G_unoccluded_far", "--src", 0, 0, -100, "--lis", 0, 0, 0, "--wall-axis", "x", "--wall-pos", 3, "--absorption", 0, 0, 0))
scen.append(S("G_near", "--src", 0, 0, -0.5, "--lis", 0, 0, 0, "--wall-axis", "x", "--wall-pos", 3, "--absorption", 0, 0, 0))
# H. one-sided geometry: flipped winding
scen.append(S("H_flipped", "--src", 0, 0, 0, "--lis", 0, 0, 0, "--wall-axis", "x", "--wall-pos", 3, "--absorption", 0, 0, 0, "--flip"))
# I. empty scene
scen.append(S("I_nowall", "--src", 0, 0, -2, "--lis", 0, 0, 0, "--no-wall"))
# J. ray-count convergence
for n in [1024, 4096, 16384, 65536, 262144]:
    scen.append(S(f"J_rays_{n}", "--src", 0, 0, 0, "--lis", 0, 0, 0, "--wall-axis", "x", "--wall-pos", 3, "--absorption", 0, 0, 0, "--rays", n))

only = argv
t0 = time.time()
for name, args in scen:
    if only and not any(name.startswith(o) for o in only):
        continue
    cmd = [EXE] + COMMON + args + ["--out", os.path.join(OUT, name)]
    # later args override earlier ones (e.g. --rays in J)
    t = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True)
    with open(os.path.join(OUT, name + ".log"), "w") as f:
        f.write(" ".join(cmd) + "\n" + r.stdout + r.stderr)
    status = "ok" if r.returncode == 0 else f"FAIL({r.returncode})"
    print(f"{name:28s} {status} {time.time()-t:5.1f}s", flush=True)
print(f"done in {time.time()-t0:.1f}s -> {OUT}; env STEAMAUDIO_BIN_DURATION={os.environ.get('STEAMAUDIO_BIN_DURATION')} STEAMAUDIO_RECONSTRUCTION={os.environ.get('STEAMAUDIO_RECONSTRUCTION')}")
