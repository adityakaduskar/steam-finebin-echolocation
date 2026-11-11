# pysteamaudio — ctypes binding for the Steam Audio C API

Covers what embodied-audio experiments need: scenes from arbitrary triangle meshes, instanced (movable) meshes,
direct + reflection simulation, Ambisonic impulse-response extraction, and a binaural decode. Struct layouts are
verified against the C compiler (`check_layout.c`, 29 structs, 0 mismatches) and the single-wall IR reproduced through the
binding matches the C harness to 1e-8 (`experiment/test_binding.py`).

```python
import sys; sys.path.insert(0, "/home/adityakaduskar/steamaudio")
from pysteamaudio import steamaudio as sa      # import BEFORE numpy (loads the system libstdc++ the patched core needs)
import numpy as np

ctx   = sa.Context()                            # lib_path=... or env STEAMAUDIO_LIB; default sdk/lib/patched/libphonon.so
scene = sa.Scene(ctx)
V, T, faces = sa.box_room((6, 3, 4))            # or V, T = sa.load_mesh("room.obj") / any format via trimesh
scene.add_mesh(V, T, [sa.Material.of(absorption=0.2, scattering=0.3)])
scene.commit()

sim = sa.Simulator(ctx, scene, max_rays=262144, max_duration=1.0, max_order=1)   # reflection_type="parametric" for RT60 only
src = sim.add_source(); sim.commit()
sim.set_listener((4.1, 1.6, 2.6), num_rays=262144, bounces=64)
src.set_inputs((1.7, 1.2, 1.1), air_absorption=False)
sim.run_direct();      print(src.direct())      # distanceAttenuation, airAbsorption, occlusion, transmission, directivity
sim.run_reflections(); ir = sim.extract_ir(src) # (channels, samples) Ambisonic IR, ACN/N3D, t=0 = direct arrival
stereo = sa.render_binaural(ctx, ir, order=1)   # (2, samples) with the default HRTF
```

Dynamic objects: build the moving part as its own `Scene`, then `h = scene.add_instanced(part, transform)` and
`scene.update_transform(h, new_transform); scene.commit(); sim.commit()` each step.

Units and frame: metres, +x right, +y up, −z ahead (Steam Audio). Unreal's cm / X-forward / Z-up frame must be converted first.

Environment: `source ~/steamaudio/experiment/env_patched.sh` (sample-accurate sparse reconstruction) or `env_stock.sh`.
With conda Python, if you import numpy before this module set `LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libstdc++.so.6`.
