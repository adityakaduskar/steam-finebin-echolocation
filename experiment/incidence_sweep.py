"""Single wall, source and listener both at height h above the wall, separated laterally so the specular
reflection has incidence angle theta. Image-source physics: E = (1-alpha)/r^2 independent of theta."""
import sys, os, math
sys.path.insert(0, os.path.expanduser("~/steamaudio"))
from pysteamaudio import steamaudio as sa
import numpy as np
ctx = sa.Context(); H = 100.0
scene = sa.Scene(ctx); scene.add_mesh(np.array([[0,-H,-H],[0,-H,H],[0,H,H],[0,H,-H]]), np.array([[0,2,1],[0,3,2]]), [sa.Material.of(0.0, 0.0)]); scene.commit()
print("| theta [deg] | h [m] | lateral sep [m] | r_refl [m] | E*r^2 (expect ~0.99) | onset err [samples] |"); print("|---|---|---|---|---|---|")
for h in (2.0, 4.0):
    for theta in (0, 15, 30, 45, 60, 70, 80):
        sep = 2*h*math.tan(math.radians(theta)); r = 2*h/math.cos(math.radians(theta)); r_dir = sep
        sim = sa.Simulator(ctx, scene, max_rays=262144, max_duration=0.5, max_order=0, threads=16); src = sim.add_source(); sim.commit()
        lis = (-h, 0, 0); s = (-h, 0, -sep)
        sim.set_listener(lis, num_rays=262144, bounces=1, duration=0.5, order=0); src.set_inputs(s, air_absorption=False)
        sim.run_reflections(); ir = sim.extract_ir(src, 0.5, 0); e = ir[0]**2
        onset = int(np.flatnonzero(e >= 0.1*e.max())[0]); pred = math.floor((r - 0.01 - r_dir)/340*48000)
        print(f"| {theta} | {h} | {sep:.2f} | {r:.2f} | {e.sum()*r*r:.3f} | {onset-pred:+d} |"); sim.release()
