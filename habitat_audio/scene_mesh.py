"""Extract a Habitat scene's triangle mesh in Habitat's coordinate frame for Steam Audio.
Habitat (Magnum) and trimesh disagree on glTF node transforms for these assets, so the frame is detected
empirically: the candidate rotation under which the navmesh vertices sit on a mesh floor wins."""
import os, hashlib
import numpy as np
import trimesh

def _rx(deg):
    c, s = np.cos(np.radians(deg)), np.sin(np.radians(deg)); return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])

CANDIDATES = {"identity": np.eye(3), "Rx(-90)": _rx(-90), "Rx(+90)": _rx(90)}

def floor_support(vertices, faces, navmesh_vertices, n=300, seed=0):
    """fraction of sampled navmesh vertices that have mesh surface 0..0.6 m below them (ray cast straight down from +0.3 m)"""
    mesh = trimesh.Trimesh(vertices, faces, process=False)
    rs = np.random.RandomState(seed); sample = navmesh_vertices[rs.choice(len(navmesh_vertices), min(n, len(navmesh_vertices)), replace=False)]
    origins = sample + np.array([0, 0.3, 0]); locs, idx, _ = mesh.ray.intersects_location(origins, np.tile([0, -1.0, 0], (len(origins), 1)), multiple_hits=False)
    d = np.full(len(origins), np.inf)
    if len(idx): d[idx] = origins[idx, 1] - np.asarray(locs).reshape(-1, 3)[:, 1]
    return float(np.mean(d < 0.6))

def load_scene_mesh(glb_path, pathfinder=None, cache_dir=None):
    """Returns (vertices (N,3) float32, triangles (M,3) int32, frame_name). Cached by file path + mtime."""
    cache_dir = cache_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
    key = hashlib.md5(f"{os.path.abspath(glb_path)}:{os.path.getmtime(glb_path)}".encode()).hexdigest()[:12]
    cache = os.path.join(cache_dir, f"{os.path.basename(glb_path)}_{key}.npz")
    if os.path.exists(cache):
        z = np.load(cache); return z["V"], z["T"], str(z["frame"])
    m = trimesh.load(glb_path, force="mesh")
    V0 = np.asarray(m.vertices, np.float64); T = np.asarray(m.faces, np.int32)
    if pathfinder is not None and pathfinder.is_loaded:
        nv = np.array(pathfinder.build_navmesh_vertices())
        scores = {name: floor_support(V0 @ R.T, T, nv) for name, R in CANDIDATES.items()}
        frame = max(scores, key=scores.get)
        if scores[frame] < 0.8:
            raise RuntimeError(f"could not place {glb_path} in Habitat's frame (floor support {scores})")
    else:
        frame = "identity"; scores = {}
    V = (V0 @ CANDIDATES[frame].T).astype(np.float32)
    os.makedirs(cache_dir, exist_ok=True); np.savez(cache, V=V, T=T, frame=frame)
    return V, T, frame
