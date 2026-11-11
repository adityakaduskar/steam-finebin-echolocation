"""Reproduce the single-wall result through the Python binding and compare with the C harness (sparse mode)."""
import sys, os, json
sys.path.insert(0, os.path.expanduser("~/steamaudio"))
from pysteamaudio import steamaudio as sa   # import before numpy so the right libstdc++ is loaded
import numpy as np

ctx = sa.Context(validation=True)
scene = sa.Scene(ctx)
h = 100.0; w = 3.0
V = np.array([[w, -h, -h], [w, -h, h], [w, h, h], [w, h, -h]]); T = np.array([[0, 2, 1], [0, 3, 2]])  # normal -x (toward origin)
scene.add_mesh(V, T, [sa.Material.of(0.0, 0.0)]); scene.commit()
sim = sa.Simulator(ctx, scene, max_rays=262144, max_duration=1.0, max_order=1)
src = sim.add_source(); sim.commit()
sim.set_listener((0, 0, 0), num_rays=262144, bounces=1)
src.set_inputs((0, 0, 0), air_absorption=False)
sim.run_direct(); print("direct:", src.direct())
sim.run_reflections(); ir = sim.extract_ir(src)
W = ir[0]; e = W**2; onset = int(np.flatnonzero(e >= 0.1*e.max())[0])
print(f"binding: W energy {e.sum():.5e}, onset sample {onset}, dir ratios {[round(float((ir[c]*W).sum()/e.sum()),3) for c in (1,2,3)]}")
m = json.load(open("results_sparse/C3_noair_w3.json")); ref = np.fromfile("results_sparse/C3_noair_w3.f32", dtype=np.float32).reshape(m["numChannels"], m["numSamples"])[0]
print(f"C harness: W energy {(ref**2).sum():.5e}, onset sample {int(np.flatnonzero(ref**2 >= 0.1*(ref**2).max())[0])}")
print("max |binding - C| over IR:", float(np.abs(W - ref[:W.size]).max()))
# binaural render smoke test
st = sa.render_binaural(ctx, ir, order=1); print("binaural render shape", st.shape, "L/R energy", float((st[0]**2).sum()), float((st[1]**2).sum()))
sim.release(); scene.release(); ctx.release(); print("ok")
