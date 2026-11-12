"""CPU-only checks for two statements in the paper (no Habitat simulator, no GPU):
 A. grazing-angle deficit for an agent's own click: Steam Audio's specular term makes reflected energy scale with cos(theta) relative to
    a mirror-correct lobe. For source = listener, how large is the resulting loss on real building geometry?  (paper marker J7)
 B. is the acoustic simulation bit-reproducible, and does the thread count matter?  (paper marker J25)
python -m habitat_audio.nogpu_checks"""
import os, sys, json, numpy as np
sys.path.insert(0, os.path.expanduser("~/steamaudio"))
os.environ.setdefault("STEAMAUDIO_LIB", os.path.expanduser("~/steamaudio/sdk/lib/patched_embree/libphonon.so")); os.environ.setdefault("STEAMAUDIO_EMBREE", "1")
from habitat_audio.audio_nav_env import compute_sonar, AUDIO_SR
from habitat_audio.scene_mesh import load_scene_mesh
from habitat_audio.ppo_train import SCENES
from pysteamaudio import steamaudio as sa
import habitat_sim, trimesh
HELD = ["office_2", "frl_apartment_4", "hotel_0", "room_2"]; N_LOBE = 100; C = 340.0; out = {}
rs = np.random.RandomState(0); d = rs.normal(size=(100000, 3)); DIRS = d / np.linalg.norm(d, axis=1, keepdims=True)
print("A. cos(theta) deficit of first-bounce specular returns for a co-located click (geometric model of the engine's lobe, 100k rays per pose)")
print("| building | poses | energy ratio engine / mirror-correct, all first-bounce returns: mean (min) | same, earliest 2 ms: mean (min) | mean incidence angle of the returned energy |"); print("|---|---|---|---|---|")
allr, alle = [], []
for name in HELD:
    path = SCENES["replica/" + name]; pf = habitat_sim.PathFinder(); pf.load_nav_mesh(path.replace("mesh_semantic.ply", "mesh_semantic.navmesh")); pf.seed(1)
    V, T, _ = load_scene_mesh(path, pf); mesh = trimesh.Trimesh(V, T, process=False); r_all, r_early, ang = [], [], []
    for k in range(50):
        p = np.array(pf.get_random_navigable_point(), float) + np.array([0, 1.5, 0])
        loc, ridx, tri = mesh.ray.intersects_location(np.tile(p, (len(DIRS), 1)), DIRS, multiple_hits=False)
        dist = np.linalg.norm(loc - p, axis=1); cos = np.abs(np.einsum("ij,ij->i", mesh.face_normals[tri], DIRS[ridx])); ok = (dist > 0.05) & (cos > 1e-3)
        dist, cos = dist[ok], cos[ok]; w = cos ** N_LOBE / dist ** 2            # engine: lobe (h.N)^n with h = back along the ray, times 1/d^2 irradiance
        if w.sum() <= 0: continue
        r_all.append(w.sum() / (w / cos).sum()); ang.append(np.degrees(np.arccos(np.clip((w * cos).sum() / w.sum(), -1, 1))))
        t = 2 * dist / C; first = t[w > 1e-3 * w.max()].min(); e = t <= first + 0.002; r_early.append(w[e].sum() / (w[e] / cos[e]).sum())
    out[name] = {"all": float(np.mean(r_all)), "all_min": float(np.min(r_all)), "early": float(np.mean(r_early)), "early_min": float(np.min(r_early)), "angle": float(np.mean(ang)), "poses": len(r_all)}
    allr += r_all; alle += r_early
    print(f"| {name} | {len(r_all)} | {np.mean(r_all):.4f} ({np.min(r_all):.4f}) | {np.mean(r_early):.4f} ({np.min(r_early):.4f}) | {np.mean(ang):.1f} deg |")
print(f"all buildings: mean ratio {np.mean(allr):.4f}, minimum {np.min(allr):.4f}; earliest 2 ms: mean {np.mean(alle):.4f}, minimum {np.min(alle):.4f}  (1.0 = no deficit)")
out["overall"] = {"all": float(np.mean(allr)), "all_min": float(np.min(allr)), "early": float(np.mean(alle)), "early_min": float(np.min(alle))}

print("\nB. reproducibility of one click (office_2, learning settings: 2048 rays, 4 bounces, 0.3 s, 24 kHz)")
path = SCENES["replica/office_2"]; pf = habitat_sim.PathFinder(); pf.load_nav_mesh(path.replace("mesh_semantic.ply", "mesh_semantic.navmesh")); pf.seed(1)
V, T, _ = load_scene_mesh(path, pf); P = np.array(pf.get_random_navigable_point(), float) + np.array([0, 1.5, 0]); AH = np.array([0, 0, -1.0]); UP = np.array([0, 1.0, 0])
def click(threads, new_context):
    global _state
    if new_context or "_state" not in globals():
        ctx = sa.Context(); sc = sa.Scene(ctx); sc.add_mesh(V, T, [sa.Material.of((0.10, 0.20, 0.30), 0.05, (0.1, 0.05, 0.03))]); sc.commit()
        sim = sa.Simulator(ctx, sc, max_rays=2048, max_duration=0.3, max_order=1, sampling_rate=AUDIO_SR, frame_size=256, threads=threads, max_sources=1); src = sim.add_source(); sim.commit(); _state = (ctx, sc, sim, src)
    ctx, sc, sim, src = _state
    sim.set_listener(P, ahead=AH, up=UP, num_rays=2048, bounces=4, duration=0.3, order=1, irradiance_min=0.1); src.set_inputs(P, air_absorption=True); sim.run_direct(); sim.run_reflections()
    return sim.extract_ir(src, 0.3, 1)
res = {}
for th in (1, 8):
    a = click(th, True); b = click(th, False); c = click(th, True)     # same simulator twice, then a fresh simulator
    sa_, sb, sc_ = (compute_sonar(x, AH, UP) for x in (a, b, c)); e = float((a ** 2).sum())
    res[th] = {"same_sim_max_abs_diff": float(np.abs(a - b).max()), "new_sim_max_abs_diff": float(np.abs(a - c).max()), "ir_peak": float(np.abs(a).max()),
               "same_sim_energy_rel_diff": float(abs((b ** 2).sum() - e) / e), "new_sim_energy_rel_diff": float(abs((c ** 2).sum() - e) / e),
               "sonar_cells_changed_same_sim": int((np.abs(sa_ - sb) > 1e-6).sum()), "sonar_cells_changed_new_sim": int((np.abs(sa_ - sc_) > 1e-6).sum()), "sonar_max_diff_same_sim": float(np.abs(sa_ - sb).max())}
    print(f"threads={th}: repeat on the same simulator: max |IR diff| {res[th]['same_sim_max_abs_diff']:.3e} (IR peak {res[th]['ir_peak']:.3e}), energy differs by {res[th]['same_sim_energy_rel_diff']:.2%}, "
          f"{res[th]['sonar_cells_changed_same_sim']} of 4096 sonar cells change (max change {res[th]['sonar_max_diff_same_sim']:.3f}); fresh simulator: max |IR diff| {res[th]['new_sim_max_abs_diff']:.3e}, {res[th]['sonar_cells_changed_new_sim']} sonar cells change")
ir1 = click(1, True); ir8 = click(8, True); print(f"threads 1 vs 8 (fresh simulators): max |IR diff| {np.abs(ir1 - ir8).max():.3e}")
out["repro"] = {str(k): v for k, v in res.items()}; out["repro"]["threads_1_vs_8_max_abs_diff"] = float(np.abs(ir1 - ir8).max())
json.dump(out, open(os.path.expanduser("~/steamaudio/habitat_audio/results/nogpu_checks.json"), "w"), indent=1)
