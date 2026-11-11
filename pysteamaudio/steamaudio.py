"""
Minimal ctypes binding for the Steam Audio C API (libphonon 4.8.x) covering scene construction from arbitrary
triangle meshes, instanced (movable) meshes, direct + reflection simulation, impulse-response extraction and
an optional binaural render of Ambisonic IRs.

Coordinates: Steam Audio frame (metres, +x right, +y up, -z ahead, right-handed).
Library selection: SteamAudio(lib_path=...) or environment variable STEAMAUDIO_LIB; default ~/steamaudio/sdk/lib/patched/libphonon.so.
The patched library honours STEAMAUDIO_BIN_DURATION and STEAMAUDIO_RECONSTRUCTION (see ~/steamaudio/README.md).
"""
import ctypes as C
import os
# The core built with GCC 11 needs GLIBCXX_3.4.30; conda's bundled libstdc++ is older and gets loaded by numpy first.
# Load the system libstdc++ globally before numpy (if the user imported numpy earlier, set LD_PRELOAD instead).
for _p in ("/usr/lib/x86_64-linux-gnu/libstdc++.so.6", "/lib/x86_64-linux-gnu/libstdc++.so.6"):
    if os.path.exists(_p):
        try: C.CDLL(_p, mode=C.RTLD_GLOBAL)
        except OSError: pass
        break
import numpy as np

# ----------------------------------------------------------------------------- constants / enums
IPL_NUM_BANDS = 3
STEAMAUDIO_VERSION = (4 << 16) | (8 << 8) | 1

SIMFLAGS_DIRECT, SIMFLAGS_REFLECTIONS, SIMFLAGS_PATHING = 1, 2, 4
DIRECTFLAGS_ALL = 1 | 2 | 4 | 8 | 16
SCENETYPE_DEFAULT = 0
SCENETYPE_EMBREE = 1
REFLECTIONTYPE = {"convolution": 0, "parametric": 1, "hybrid": 2}
DISTANCEATTENUATION_DEFAULT, DISTANCEATTENUATION_INVERSE, DISTANCEATTENUATION_CALLBACK = 0, 1, 2
AIRABSORPTION_DEFAULT, AIRABSORPTION_EXPONENTIAL = 0, 1
OCCLUSION_RAYCAST, OCCLUSION_VOLUMETRIC = 0, 1
CONTEXTFLAGS_VALIDATION = 1
HRTFTYPE_DEFAULT = 0
SPEAKERLAYOUT_STEREO = 1
AMBISONICS_N3D, AMBISONICS_SN3D, AMBISONICS_FUMA = 0, 1, 2

# ----------------------------------------------------------------------------- structs
class Vector3(C.Structure):
    _fields_ = [("x", C.c_float), ("y", C.c_float), ("z", C.c_float)]
    @classmethod
    def of(cls, v): return cls(float(v[0]), float(v[1]), float(v[2]))

class CoordinateSpace3(C.Structure):
    _fields_ = [("right", Vector3), ("up", Vector3), ("ahead", Vector3), ("origin", Vector3)]
    @classmethod
    def of(cls, origin, ahead=(0, 0, -1), up=(0, 1, 0)):
        a = np.asarray(ahead, float); a /= np.linalg.norm(a); u = np.asarray(up, float)
        r = np.cross(a, u); r /= np.linalg.norm(r); u = np.cross(r, a)
        return cls(Vector3.of(r), Vector3.of(u), Vector3.of(a), Vector3.of(origin))

class Sphere(C.Structure):
    _fields_ = [("center", Vector3), ("radius", C.c_float)]

class Matrix4x4(C.Structure):
    _fields_ = [("elements", (C.c_float * 4) * 4)]
    @classmethod
    def of(cls, m):
        m = np.asarray(m, float); out = cls()
        for i in range(4):
            for j in range(4): out.elements[i][j] = m[i, j]
        return out

class EmbreeDeviceSettings(C.Structure):
    _fields_ = [("_unused", C.c_int)]   # the C struct has no fields; a dummy member keeps ctypes happy (sizeof C = 0 or 1)

class ContextSettings(C.Structure):
    _fields_ = [("version", C.c_uint32), ("logCallback", C.c_void_p), ("allocateCallback", C.c_void_p),
                ("freeCallback", C.c_void_p), ("simdLevel", C.c_int), ("flags", C.c_int)]

class SceneSettings(C.Structure):
    _fields_ = [("type", C.c_int), ("closestHitCallback", C.c_void_p), ("anyHitCallback", C.c_void_p),
                ("batchedClosestHitCallback", C.c_void_p), ("batchedAnyHitCallback", C.c_void_p),
                ("userData", C.c_void_p), ("embreeDevice", C.c_void_p), ("radeonRaysDevice", C.c_void_p)]

class Material(C.Structure):
    _fields_ = [("absorption", C.c_float * 3), ("scattering", C.c_float), ("transmission", C.c_float * 3)]
    @classmethod
    def of(cls, absorption=(0.1, 0.1, 0.1), scattering=0.0, transmission=(0, 0, 0)):
        if np.isscalar(absorption): absorption = (absorption,) * 3
        if np.isscalar(transmission): transmission = (transmission,) * 3
        m = cls(); m.absorption[:] = [float(a) for a in absorption]; m.scattering = float(scattering); m.transmission[:] = [float(t) for t in transmission]
        return m

class Triangle(C.Structure):
    _fields_ = [("indices", C.c_int32 * 3)]

class StaticMeshSettings(C.Structure):
    _fields_ = [("numVertices", C.c_int32), ("numTriangles", C.c_int32), ("numMaterials", C.c_int32),
                ("vertices", C.POINTER(Vector3)), ("triangles", C.POINTER(Triangle)),
                ("materialIndices", C.POINTER(C.c_int32)), ("materials", C.POINTER(Material))]

class InstancedMeshSettings(C.Structure):
    _fields_ = [("subScene", C.c_void_p), ("transform", Matrix4x4)]

class SimulationSettings(C.Structure):
    _fields_ = [("flags", C.c_int), ("sceneType", C.c_int), ("reflectionType", C.c_int),
                ("maxNumOcclusionSamples", C.c_int32), ("maxNumRays", C.c_int32), ("numDiffuseSamples", C.c_int32),
                ("maxDuration", C.c_float), ("maxOrder", C.c_int32), ("maxNumSources", C.c_int32), ("numThreads", C.c_int32),
                ("rayBatchSize", C.c_int32), ("numVisSamples", C.c_int32), ("samplingRate", C.c_int32), ("frameSize", C.c_int32),
                ("openCLDevice", C.c_void_p), ("radeonRaysDevice", C.c_void_p), ("tanDevice", C.c_void_p)]

class SourceSettings(C.Structure):
    _fields_ = [("flags", C.c_int)]

class DistanceAttenuationModel(C.Structure):
    _fields_ = [("type", C.c_int), ("minDistance", C.c_float), ("callback", C.c_void_p), ("userData", C.c_void_p), ("dirty", C.c_int)]

class AirAbsorptionModel(C.Structure):
    _fields_ = [("type", C.c_int), ("coefficients", C.c_float * 3), ("callback", C.c_void_p), ("userData", C.c_void_p), ("dirty", C.c_int)]

class Directivity(C.Structure):
    _fields_ = [("dipoleWeight", C.c_float), ("dipolePower", C.c_float), ("callback", C.c_void_p), ("userData", C.c_void_p)]

class BakedDataIdentifier(C.Structure):
    _fields_ = [("type", C.c_int), ("variation", C.c_int), ("endpointInfluence", Sphere)]

class SimulationInputs(C.Structure):
    _fields_ = [("flags", C.c_int), ("directFlags", C.c_int), ("source", CoordinateSpace3),
                ("distanceAttenuationModel", DistanceAttenuationModel), ("airAbsorptionModel", AirAbsorptionModel),
                ("directivity", Directivity), ("occlusionType", C.c_int), ("occlusionRadius", C.c_float),
                ("numOcclusionSamples", C.c_int32), ("reverbScale", C.c_float * 3), ("hybridReverbTransitionTime", C.c_float),
                ("hybridReverbOverlapPercent", C.c_float), ("baked", C.c_int), ("bakedDataIdentifier", BakedDataIdentifier),
                ("pathingProbes", C.c_void_p), ("visRadius", C.c_float), ("visThreshold", C.c_float), ("visRange", C.c_float),
                ("pathingOrder", C.c_int32), ("enableValidation", C.c_int), ("findAlternatePaths", C.c_int),
                ("numTransmissionRays", C.c_int32), ("deviationModel", C.c_void_p)]

class SimulationSharedInputs(C.Structure):
    _fields_ = [("listener", CoordinateSpace3), ("numRays", C.c_int32), ("numBounces", C.c_int32), ("duration", C.c_float),
                ("order", C.c_int32), ("irradianceMinDistance", C.c_float), ("pathingVisCallback", C.c_void_p), ("pathingUserData", C.c_void_p)]

class DirectEffectParams(C.Structure):
    _fields_ = [("flags", C.c_int), ("transmissionType", C.c_int), ("distanceAttenuation", C.c_float),
                ("airAbsorption", C.c_float * 3), ("directivity", C.c_float), ("occlusion", C.c_float), ("transmission", C.c_float * 3)]

class ReflectionEffectParams(C.Structure):
    _fields_ = [("type", C.c_int), ("ir", C.c_void_p), ("reverbTimes", C.c_float * 3), ("eq", C.c_float * 3), ("delay", C.c_int32),
                ("numChannels", C.c_int32), ("irSize", C.c_int32), ("tanDevice", C.c_void_p), ("tanSlot", C.c_int32)]

class PathEffectParams(C.Structure):
    _fields_ = [("eqCoeffs", C.c_float * 3), ("shCoeffs", C.POINTER(C.c_float)), ("order", C.c_int32), ("binaural", C.c_int),
                ("hrtf", C.c_void_p), ("listener", CoordinateSpace3), ("normalizeEQ", C.c_int)]

class SimulationOutputs(C.Structure):
    _fields_ = [("direct", DirectEffectParams), ("reflections", ReflectionEffectParams), ("pathing", PathEffectParams)]

class AudioSettings(C.Structure):
    _fields_ = [("samplingRate", C.c_int32), ("frameSize", C.c_int32)]

class AudioBuffer(C.Structure):
    _fields_ = [("numChannels", C.c_int32), ("numSamples", C.c_int32), ("data", C.POINTER(C.POINTER(C.c_float)))]

class ReflectionEffectSettings(C.Structure):
    _fields_ = [("type", C.c_int), ("irSize", C.c_int32), ("numChannels", C.c_int32)]

class HRTFSettings(C.Structure):
    _fields_ = [("type", C.c_int), ("sofaFileName", C.c_char_p), ("sofaData", C.c_void_p), ("sofaDataSize", C.c_int), ("volume", C.c_float), ("normType", C.c_int)]

class SpeakerLayout(C.Structure):
    _fields_ = [("type", C.c_int), ("numSpeakers", C.c_int32), ("speakers", C.POINTER(Vector3))]

class AmbisonicsDecodeEffectSettings(C.Structure):
    _fields_ = [("speakerLayout", SpeakerLayout), ("hrtf", C.c_void_p), ("maxOrder", C.c_int32)]

class AmbisonicsDecodeEffectParams(C.Structure):
    _fields_ = [("order", C.c_int32), ("hrtf", C.c_void_p), ("orientation", CoordinateSpace3), ("binaural", C.c_int)]

STRUCTS = {n: g for n, g in globals().items() if isinstance(g, type) and issubclass(g, C.Structure) and g is not C.Structure}

# ----------------------------------------------------------------------------- library
DEFAULT_LIB = os.environ.get("STEAMAUDIO_LIB", os.path.expanduser("~/steamaudio/sdk/lib/patched/libphonon.so"))

def _load(lib_path):
    lib = C.CDLL(lib_path)
    P = C.c_void_p; PP = C.POINTER(C.c_void_p)
    proto = {
        "iplContextCreate": ([C.POINTER(ContextSettings), PP], C.c_int),
        "iplContextRelease": ([PP], None),
        "iplEmbreeDeviceCreate": ([P, P, PP], C.c_int),
        "iplEmbreeDeviceRelease": ([PP], None),
        "iplSceneCreate": ([P, C.POINTER(SceneSettings), PP], C.c_int),
        "iplSceneRelease": ([PP], None),
        "iplSceneCommit": ([P], None),
        "iplSceneSaveOBJ": ([P, C.c_char_p], None),
        "iplStaticMeshCreate": ([P, C.POINTER(StaticMeshSettings), PP], C.c_int),
        "iplStaticMeshRelease": ([PP], None),
        "iplStaticMeshAdd": ([P, P], None),
        "iplStaticMeshRemove": ([P, P], None),
        "iplInstancedMeshCreate": ([P, C.POINTER(InstancedMeshSettings), PP], C.c_int),
        "iplInstancedMeshRelease": ([PP], None),
        "iplInstancedMeshAdd": ([P, P], None),
        "iplInstancedMeshRemove": ([P, P], None),
        "iplInstancedMeshUpdateTransform": ([P, P, Matrix4x4], None),
        "iplSimulatorCreate": ([P, C.POINTER(SimulationSettings), PP], C.c_int),
        "iplSimulatorRelease": ([PP], None),
        "iplSimulatorSetScene": ([P, P], None),
        "iplSimulatorSetSharedInputs": ([P, C.c_int, C.POINTER(SimulationSharedInputs)], None),
        "iplSimulatorCommit": ([P], None),
        "iplSimulatorRunDirect": ([P], None),
        "iplSimulatorRunReflections": ([P], None),
        "iplSourceCreate": ([P, C.POINTER(SourceSettings), PP], C.c_int),
        "iplSourceRelease": ([PP], None),
        "iplSourceAdd": ([P, P], None),
        "iplSourceRemove": ([P, P], None),
        "iplSourceSetInputs": ([P, C.c_int, C.POINTER(SimulationInputs)], None),
        "iplSourceGetOutputs": ([P, C.c_int, C.POINTER(SimulationOutputs)], None),
        "iplDistanceAttenuationCalculate": ([P, Vector3, Vector3, C.POINTER(DistanceAttenuationModel)], C.c_float),
        "iplAirAbsorptionCalculate": ([P, Vector3, Vector3, C.POINTER(AirAbsorptionModel), C.POINTER(C.c_float)], None),
        "iplAudioBufferAllocate": ([P, C.c_int32, C.c_int32, C.POINTER(AudioBuffer)], C.c_int),
        "iplAudioBufferFree": ([P, C.POINTER(AudioBuffer)], None),
        "iplReflectionEffectCreate": ([P, C.POINTER(AudioSettings), C.POINTER(ReflectionEffectSettings), PP], C.c_int),
        "iplReflectionEffectRelease": ([PP], None),
        "iplReflectionEffectReset": ([P], None),
        "iplReflectionEffectApply": ([P, C.POINTER(ReflectionEffectParams), C.POINTER(AudioBuffer), C.POINTER(AudioBuffer), P], C.c_int),
        "iplHRTFCreate": ([P, C.POINTER(AudioSettings), C.POINTER(HRTFSettings), PP], C.c_int),
        "iplHRTFRelease": ([PP], None),
        "iplAmbisonicsDecodeEffectCreate": ([P, C.POINTER(AudioSettings), C.POINTER(AmbisonicsDecodeEffectSettings), PP], C.c_int),
        "iplAmbisonicsDecodeEffectRelease": ([PP], None),
        "iplAmbisonicsDecodeEffectReset": ([P], None),
        "iplAmbisonicsDecodeEffectApply": ([P, C.POINTER(AmbisonicsDecodeEffectParams), C.POINTER(AudioBuffer), C.POINTER(AudioBuffer)], C.c_int),
    }
    for name, (argtypes, restype) in proto.items():
        f = getattr(lib, name); f.argtypes = argtypes; f.restype = restype
    return lib

def _check(status, what):
    if status != 0:
        raise RuntimeError(f"{what} failed with IPLerror {status}")

# ----------------------------------------------------------------------------- objects
class Context:
    def __init__(self, lib_path=None, validation=False, embree=None):
        """embree: use Intel Embree for ray tracing (needs a libphonon built with STEAMAUDIO_ENABLE_EMBREE, e.g. sdk/lib/patched_embree).
        None = use Embree iff the library exports it and STEAMAUDIO_EMBREE=1."""
        self.lib_path = lib_path or os.environ.get("STEAMAUDIO_LIB", DEFAULT_LIB)   # read at call time: the package may be imported before the env is set
        self.lib = _load(self.lib_path)
        s = ContextSettings(); s.version = STEAMAUDIO_VERSION; s.flags = CONTEXTFLAGS_VALIDATION if validation else 0
        self.handle = C.c_void_p()
        _check(self.lib.iplContextCreate(C.byref(s), C.byref(self.handle)), "iplContextCreate")
        self.embree_device = C.c_void_p(); self.scene_type = SCENETYPE_DEFAULT
        if embree is None: embree = os.environ.get("STEAMAUDIO_EMBREE", "0") == "1"
        if embree:
            es = EmbreeDeviceSettings(); st = self.lib.iplEmbreeDeviceCreate(self.handle, C.byref(es), C.byref(self.embree_device))
            if st != 0 or not self.embree_device: raise RuntimeError(f"iplEmbreeDeviceCreate failed ({st}); this libphonon was probably built without Embree")
            self.scene_type = SCENETYPE_EMBREE
    def release(self):
        if self.embree_device: self.lib.iplEmbreeDeviceRelease(C.byref(self.embree_device)); self.embree_device = C.c_void_p()
        if self.handle: self.lib.iplContextRelease(C.byref(self.handle)); self.handle = C.c_void_p()
    def distance_attenuation(self, source, listener, model=None):
        model = model or DistanceAttenuationModel(type=DISTANCEATTENUATION_DEFAULT)
        return self.lib.iplDistanceAttenuationCalculate(self.handle, Vector3.of(source), Vector3.of(listener), C.byref(model))
    def air_absorption(self, source, listener, model=None):
        model = model or AirAbsorptionModel(type=AIRABSORPTION_DEFAULT); out = (C.c_float * 3)()
        self.lib.iplAirAbsorptionCalculate(self.handle, Vector3.of(source), Vector3.of(listener), C.byref(model), out)
        return np.array(out[:])


class Scene:
    """Container for static meshes (and instanced meshes). Keep vertex/triangle arrays alive for the scene lifetime."""
    def __init__(self, ctx):
        self.ctx = ctx; self.lib = ctx.lib
        s = SceneSettings(); s.type = ctx.scene_type; s.embreeDevice = ctx.embree_device.value if ctx.embree_device else None
        self.handle = C.c_void_p(); _check(self.lib.iplSceneCreate(ctx.handle, C.byref(s), C.byref(self.handle)), "iplSceneCreate")
        self._keep = []; self.meshes = []

    def add_mesh(self, vertices, triangles, materials, material_indices=None):
        """vertices (N,3) float, triangles (M,3) int (counter-clockwise seen from the side the normal faces;
        Steam Audio treats surfaces as two-sided for reflections), materials: list of Material, material_indices (M,) int."""
        V = np.ascontiguousarray(np.asarray(vertices, dtype=np.float32)); T = np.ascontiguousarray(np.asarray(triangles, dtype=np.int32))
        n_v, n_t = len(V), len(T)
        if material_indices is None: material_indices = np.zeros(n_t, dtype=np.int32)
        MI = np.ascontiguousarray(np.asarray(material_indices, dtype=np.int32))
        verts = (Vector3 * n_v)(); tris = (Triangle * n_t)(); mats = (Material * len(materials))(*materials); mi = (C.c_int32 * n_t)(*MI.tolist())
        C.memmove(verts, V.ctypes.data, V.nbytes); C.memmove(tris, T.ctypes.data, T.nbytes)
        s = StaticMeshSettings(n_v, n_t, len(materials), verts, tris, mi, mats)
        h = C.c_void_p(); _check(self.lib.iplStaticMeshCreate(self.handle, C.byref(s), C.byref(h)), "iplStaticMeshCreate")
        self.lib.iplStaticMeshAdd(h, self.handle); self._keep.append((verts, tris, mats, mi)); self.meshes.append(h)
        return h

    def remove_mesh(self, h):
        self.lib.iplStaticMeshRemove(h, self.handle); self.lib.iplStaticMeshRelease(C.byref(h)); self.meshes.remove(h)

    def add_instanced(self, sub_scene, transform=np.eye(4)):
        """Instance another Scene with a 4x4 transform (row-major, column vectors). Returns a handle for update_transform."""
        s = InstancedMeshSettings(sub_scene.handle, Matrix4x4.of(transform)); h = C.c_void_p()
        _check(self.lib.iplInstancedMeshCreate(self.handle, C.byref(s), C.byref(h)), "iplInstancedMeshCreate")
        self.lib.iplInstancedMeshAdd(h, self.handle); self._keep.append(sub_scene); return h

    def update_transform(self, h, transform):
        self.lib.iplInstancedMeshUpdateTransform(h, self.handle, Matrix4x4.of(transform))

    def commit(self): self.lib.iplSceneCommit(self.handle)
    def save_obj(self, base): self.lib.iplSceneSaveOBJ(self.handle, base.encode())
    def release(self):
        if self.handle: self.lib.iplSceneRelease(C.byref(self.handle)); self.handle = C.c_void_p()


class Source:
    def __init__(self, sim, flags):
        self.sim = sim; self.lib = sim.lib; self.flags = flags
        s = SourceSettings(flags); self.handle = C.c_void_p()
        _check(self.lib.iplSourceCreate(sim.handle, C.byref(s), C.byref(self.handle)), "iplSourceCreate")
        self.lib.iplSourceAdd(self.handle, sim.handle)
        self.inputs = SimulationInputs()

    def set_inputs(self, position, ahead=(0, 0, -1), up=(0, 1, 0), air_absorption=True, air_coefficients=None,
                   distance_min=1.0, dipole_weight=0.0, dipole_power=1.0, occlusion="raycast", occlusion_radius=0.1,
                   occlusion_samples=16, transmission_rays=1, reverb_scale=(1, 1, 1), hybrid_transition=1.0, hybrid_overlap=0.25):
        i = self.inputs
        i.flags = self.flags; i.directFlags = DIRECTFLAGS_ALL; i.source = CoordinateSpace3.of(position, ahead, up)
        i.distanceAttenuationModel = DistanceAttenuationModel(DISTANCEATTENUATION_DEFAULT if distance_min == 1.0 else DISTANCEATTENUATION_INVERSE, float(distance_min))
        if air_absorption and air_coefficients is None:
            i.airAbsorptionModel = AirAbsorptionModel(type=AIRABSORPTION_DEFAULT)
        else:
            i.airAbsorptionModel = AirAbsorptionModel(type=AIRABSORPTION_EXPONENTIAL)
            coeffs = air_coefficients if air_absorption else (0, 0, 0)
            i.airAbsorptionModel.coefficients[:] = [float(c) for c in coeffs]
        i.directivity = Directivity(float(dipole_weight), float(dipole_power))
        i.occlusionType = OCCLUSION_RAYCAST if occlusion == "raycast" else OCCLUSION_VOLUMETRIC
        i.occlusionRadius = float(occlusion_radius); i.numOcclusionSamples = int(occlusion_samples)
        i.reverbScale[:] = [float(r) for r in reverb_scale]; i.hybridReverbTransitionTime = float(hybrid_transition)
        i.hybridReverbOverlapPercent = float(hybrid_overlap); i.numTransmissionRays = int(transmission_rays)
        self.lib.iplSourceSetInputs(self.handle, self.flags, C.byref(i))

    def outputs(self, flags=None):
        o = SimulationOutputs(); self.lib.iplSourceGetOutputs(self.handle, flags if flags is not None else self.flags, C.byref(o)); return o

    def direct(self):
        d = self.outputs(SIMFLAGS_DIRECT).direct
        return {"distanceAttenuation": d.distanceAttenuation, "airAbsorption": np.array(d.airAbsorption[:]), "directivity": d.directivity,
                "occlusion": d.occlusion, "transmission": np.array(d.transmission[:])}

    def reflections(self):
        return self.outputs(SIMFLAGS_REFLECTIONS).reflections

    def release(self):
        if self.handle:
            self.lib.iplSourceRemove(self.handle, self.sim.handle); self.lib.iplSourceRelease(C.byref(self.handle)); self.handle = C.c_void_p()


class Simulator:
    def __init__(self, ctx, scene, max_rays=65536, max_duration=1.0, max_order=1, reflection_type="convolution",
                 sampling_rate=48000, frame_size=512, threads=8, max_sources=4, flags=SIMFLAGS_DIRECT | SIMFLAGS_REFLECTIONS,
                 diffuse_samples=1024):
        self.ctx = ctx; self.lib = ctx.lib; self.scene = scene; self.sr = sampling_rate; self.frame = frame_size; self.flags = flags
        self.max_duration = max_duration; self.max_order = max_order; self.reflection_type = REFLECTIONTYPE[reflection_type]
        s = SimulationSettings()
        s.flags = flags; s.sceneType = ctx.scene_type; s.reflectionType = self.reflection_type
        s.maxNumOcclusionSamples = 64; s.maxNumRays = max_rays; s.numDiffuseSamples = diffuse_samples; s.maxDuration = max_duration
        s.maxOrder = max_order; s.maxNumSources = max_sources; s.numThreads = threads; s.rayBatchSize = 16; s.numVisSamples = 1
        s.samplingRate = sampling_rate; s.frameSize = frame_size
        self.handle = C.c_void_p(); _check(self.lib.iplSimulatorCreate(ctx.handle, C.byref(s), C.byref(self.handle)), "iplSimulatorCreate")
        self.lib.iplSimulatorSetScene(self.handle, scene.handle); self.sources = []
        self.shared = SimulationSharedInputs()

    def add_source(self):
        src = Source(self, self.flags); self.sources.append(src); return src

    def set_listener(self, position, ahead=(0, 0, -1), up=(0, 1, 0), num_rays=65536, bounces=1, duration=None, order=None, irradiance_min=1.0):
        sh = self.shared
        sh.listener = CoordinateSpace3.of(position, ahead, up); sh.numRays = int(num_rays); sh.numBounces = int(bounces)
        sh.duration = float(duration or self.max_duration); sh.order = int(order if order is not None else self.max_order)
        sh.irradianceMinDistance = float(irradiance_min)
        self.lib.iplSimulatorSetSharedInputs(self.handle, self.flags, C.byref(sh))

    def commit(self): self.lib.iplSimulatorCommit(self.handle)
    def run_direct(self): self.lib.iplSimulatorRunDirect(self.handle)
    def run_reflections(self): self.lib.iplSimulatorRunReflections(self.handle)

    def extract_ir(self, source, duration=None, order=None):
        """Push a unit impulse through the convolution reflection effect; returns (channels, samples) float64 array.
        One silent warm-up frame is processed first so the effect's IR cross-fade does not ramp early arrivals."""
        duration = duration or self.max_duration; order = order if order is not None else self.max_order
        nch = (order + 1) ** 2; ir_size = int(np.ceil(duration * self.sr)); fs = self.frame
        rp = source.reflections(); rp.type = 0; rp.numChannels = nch; rp.irSize = ir_size
        if not rp.ir: raise RuntimeError("no reflection IR available (run_reflections not called or simulator not convolution type)")
        aset = AudioSettings(self.sr, fs); es = ReflectionEffectSettings(0, ir_size, nch); eff = C.c_void_p()
        _check(self.lib.iplReflectionEffectCreate(self.ctx.handle, C.byref(aset), C.byref(es), C.byref(eff)), "iplReflectionEffectCreate")
        inb = AudioBuffer(); outb = AudioBuffer()
        _check(self.lib.iplAudioBufferAllocate(self.ctx.handle, 1, fs, C.byref(inb)), "alloc"); _check(self.lib.iplAudioBufferAllocate(self.ctx.handle, nch, fs, C.byref(outb)), "alloc")
        n_frames = ir_size // fs + 2; out = np.zeros((nch, n_frames * fs))
        zeros = np.zeros(fs, dtype=np.float32)
        C.memmove(inb.data[0], zeros.ctypes.data, zeros.nbytes); self.lib.iplReflectionEffectApply(eff, C.byref(rp), C.byref(inb), C.byref(outb), None)
        for f in range(n_frames):
            frame = zeros.copy()
            if f == 0: frame[0] = 1.0
            C.memmove(inb.data[0], frame.ctypes.data, frame.nbytes)
            self.lib.iplReflectionEffectApply(eff, C.byref(rp), C.byref(inb), C.byref(outb), None)
            for ch in range(nch):
                out[ch, f*fs:(f+1)*fs] = np.ctypeslib.as_array(outb.data[ch], shape=(fs,))
        self.lib.iplAudioBufferFree(self.ctx.handle, C.byref(inb)); self.lib.iplAudioBufferFree(self.ctx.handle, C.byref(outb))
        self.lib.iplReflectionEffectRelease(C.byref(eff))
        return out[:, :ir_size]

    def release(self):
        for s in self.sources: s.release()
        if self.handle: self.lib.iplSimulatorRelease(C.byref(self.handle)); self.handle = C.c_void_p()


class BinauralRenderer:
    """Decodes Ambisonic (ACN/N3D, world-frame) IRs or signals to binaural stereo with Steam Audio's default HRTF.
    Holds the HRTF, decode effect and buffers, so repeated renders cost ~1 ms instead of re-loading the HRTF."""
    def __init__(self, ctx, order=1, sampling_rate=48000, frame_size=512):
        self.ctx, self.lib, self.order, self.sr, self.fs = ctx, ctx.lib, order, sampling_rate, frame_size
        aset = AudioSettings(sampling_rate, frame_size); hs = HRTFSettings(); hs.type = HRTFTYPE_DEFAULT; hs.volume = 1.0; self.hrtf = C.c_void_p()
        _check(self.lib.iplHRTFCreate(ctx.handle, C.byref(aset), C.byref(hs), C.byref(self.hrtf)), "iplHRTFCreate (default HRTF needs 24/44.1/48 kHz)")
        ds = AmbisonicsDecodeEffectSettings(); ds.speakerLayout = SpeakerLayout(SPEAKERLAYOUT_STEREO, 0, None); ds.hrtf = self.hrtf; ds.maxOrder = order
        self.effect = C.c_void_p(); _check(self.lib.iplAmbisonicsDecodeEffectCreate(ctx.handle, C.byref(aset), C.byref(ds), C.byref(self.effect)), "iplAmbisonicsDecodeEffectCreate")
        self.nch = (order + 1) ** 2; self.inb = AudioBuffer(); self.outb = AudioBuffer()
        _check(self.lib.iplAudioBufferAllocate(ctx.handle, self.nch, frame_size, C.byref(self.inb)), "alloc"); _check(self.lib.iplAudioBufferAllocate(ctx.handle, 2, frame_size, C.byref(self.outb)), "alloc")
        self.zero = np.zeros(frame_size, dtype=np.float32)

    def render(self, ambisonic_ir, listener_ahead=(0, 0, -1), listener_up=(0, 1, 0)):
        n = ambisonic_ir.shape[1]; fs = self.fs; n_frames = int(np.ceil(n / fs)) + 1
        x = np.zeros((self.nch, n_frames * fs), dtype=np.float32); x[:, :n] = ambisonic_ir
        p = AmbisonicsDecodeEffectParams(self.order, self.hrtf, CoordinateSpace3.of((0, 0, 0), listener_ahead, listener_up), 1)
        self.lib.iplAmbisonicsDecodeEffectReset(self.effect)
        # warm-up: the decoder interpolates its orientation from the default over the first frame it processes
        for ch in range(self.nch): C.memmove(self.inb.data[ch], self.zero.ctypes.data, self.zero.nbytes)
        self.lib.iplAmbisonicsDecodeEffectApply(self.effect, C.byref(p), C.byref(self.inb), C.byref(self.outb))
        out = np.zeros((2, n_frames * fs), dtype=np.float32)
        for f in range(n_frames):
            for ch in range(self.nch):
                seg = np.ascontiguousarray(x[ch, f*fs:(f+1)*fs]); C.memmove(self.inb.data[ch], seg.ctypes.data, seg.nbytes)
            self.lib.iplAmbisonicsDecodeEffectApply(self.effect, C.byref(p), C.byref(self.inb), C.byref(self.outb))
            for ch in range(2): out[ch, f*fs:(f+1)*fs] = np.ctypeslib.as_array(self.outb.data[ch], shape=(fs,))
        return out[:, :n]

    def release(self):
        self.lib.iplAudioBufferFree(self.ctx.handle, C.byref(self.inb)); self.lib.iplAudioBufferFree(self.ctx.handle, C.byref(self.outb))
        self.lib.iplAmbisonicsDecodeEffectRelease(C.byref(self.effect)); self.lib.iplHRTFRelease(C.byref(self.hrtf))


def render_binaural(ctx, ambisonic_ir, order, sampling_rate=48000, frame_size=512, listener_ahead=(0, 0, -1), listener_up=(0, 1, 0)):
    """One-off binaural decode (creates and releases a BinauralRenderer). Returns (2, samples)."""
    r = BinauralRenderer(ctx, order, sampling_rate, frame_size)
    try: return r.render(ambisonic_ir, listener_ahead, listener_up)
    finally: r.release()

# ----------------------------------------------------------------------------- geometry helpers
def box_room(size, origin=(0, 0, 0)):
    """Closed shoebox [origin, origin+size] with inward-facing triangles. Returns (vertices (8,3), triangles (12,3), face_ids (12,))
    face ids: 0:x=min 1:x=max 2:y=min 3:y=max 4:z=min 5:z=max (one material index per face pair if you like)."""
    o = np.asarray(origin, float); s = np.asarray(size, float)
    corners = np.array([[i, j, k] for i in (0, 1) for j in (0, 1) for k in (0, 1)], float)  # index = 4i+2j+k
    V = o + corners * s
    def idx(i, j, k): return 4*i + 2*j + k
    faces = {  # quads ordered counter-clockwise when viewed from inside the box
        0: [idx(0,0,0), idx(0,0,1), idx(0,1,1), idx(0,1,0)],   # x = min, normal +x
        1: [idx(1,0,0), idx(1,1,0), idx(1,1,1), idx(1,0,1)],   # x = max, normal -x
        2: [idx(0,0,0), idx(1,0,0), idx(1,0,1), idx(0,0,1)],   # y = min, normal +y
        3: [idx(0,1,0), idx(0,1,1), idx(1,1,1), idx(1,1,0)],   # y = max, normal -y
        4: [idx(0,0,0), idx(0,1,0), idx(1,1,0), idx(1,0,0)],   # z = min, normal +z
        5: [idx(0,0,1), idx(1,0,1), idx(1,1,1), idx(0,1,1)],   # z = max, normal -z
    }
    T, F = [], []
    centre = o + s/2
    for f, q in faces.items():
        tri = [[q[0], q[1], q[2]], [q[0], q[2], q[3]]]
        for t in tri:
            n = np.cross(V[t[1]] - V[t[0]], V[t[2]] - V[t[0]])
            if np.dot(n, centre - V[t[0]]) < 0: t = [t[0], t[2], t[1]]   # make the winding counter-clockwise from inside
            T.append(t); F.append(f)
    T = np.array(T, int)
    return V, T, np.array(F)

def load_obj(path):
    """Minimal Wavefront OBJ loader (triangulates polygons). Returns (vertices, triangles)."""
    V, T = [], []
    for line in open(path):
        if line.startswith("v "):
            V.append([float(x) for x in line.split()[1:4]])
        elif line.startswith("f "):
            ids = [int(tok.split("/")[0]) - 1 for tok in line.split()[1:]]
            for k in range(1, len(ids) - 1): T.append([ids[0], ids[k], ids[k+1]])
    return np.array(V, float), np.array(T, int)

def load_mesh(path):
    """Load OBJ natively, anything else through trimesh if installed (pip install trimesh)."""
    if path.lower().endswith(".obj"): return load_obj(path)
    import trimesh
    m = trimesh.load(path, force="mesh"); return np.asarray(m.vertices, float), np.asarray(m.faces, int)
