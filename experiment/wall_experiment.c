/*
 * wall_experiment.c -- single reflecting wall acoustics experiment using the Steam Audio C API (phonon.h)
 *
 * Scene: one rectangular wall (two triangles) in an otherwise empty world, one point source, one listener.
 * Runs (a) direct-path simulation (distance attenuation, air absorption, occlusion, transmission) and
 * (b) ray-traced reflection simulation. The resulting Ambisonic impulse response (IR) is extracted by
 * pushing a unit impulse through the convolution reflection effect, and written to disk for analysis.
 *
 * Coordinate system (Steam Audio / OpenGL): +x right, +y up, -z ahead. Units: metres.
 */
#include <phonon.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

static void logcb(IPLLogLevel level, const char* msg) { fprintf(stderr, "[phonon %d] %s", (int)level, msg); }

typedef struct {
    char   wallAxis;        /* 'x','y','z' : axis the wall is perpendicular to */
    float  wallPos;         /* coordinate of the wall plane along that axis */
    float  wallSize;        /* edge length of square wall */
    int    flipWinding;     /* reverse triangle winding (normal points away from origin side) */
    int    noWall;          /* empty scene control */
    float  src[3], lis[3];
    float  absorption[3], transmission[3], scattering;
    int    numRays, numBounces, order;
    float  duration;
    int    sr, frameSize;
    int    noAir;           /* disable air absorption (exponential model with zero coefficients) */
    float  irrMin;          /* irradianceMinDistance for reflections (default 1 m) */
    const char* out;
} Config;

static void usage(void) {
    fprintf(stderr,
      "usage: wall_experiment [options]\n"
      "  --wall-axis x|y|z   --wall-pos W  --wall-size S  --flip  --no-wall\n"
      "  --src x y z  --lis x y z\n"
      "  --absorption a b c  --transmission a b c  --scattering s\n"
      "  --rays N  --bounces B  --order O  --duration D  --sr R  --frame F\n"
      "  --out PREFIX   (writes PREFIX.f32 and PREFIX.json)\n");
}

int main(int argc, char** argv) {
    Config c = { 'x', 3.0f, 200.0f, 0, 0,
                 {0,0,0}, {0,0,0},
                 {0.1f,0.1f,0.1f}, {0,0,0}, 0.0f,
                 65536, 1, 1, 1.0f, 48000, 512, 0, 1.0f, "results/run" };
    for (int i = 1; i < argc; ++i) {
        #define NEXTF() atof(argv[++i])
        if (!strcmp(argv[i], "--wall-axis")) c.wallAxis = argv[++i][0];
        else if (!strcmp(argv[i], "--wall-pos")) c.wallPos = NEXTF();
        else if (!strcmp(argv[i], "--wall-size")) c.wallSize = NEXTF();
        else if (!strcmp(argv[i], "--flip")) c.flipWinding = 1;
        else if (!strcmp(argv[i], "--no-wall")) c.noWall = 1;
        else if (!strcmp(argv[i], "--no-air")) c.noAir = 1;
        else if (!strcmp(argv[i], "--irr-min")) c.irrMin = NEXTF();
        else if (!strcmp(argv[i], "--src")) { c.src[0]=NEXTF(); c.src[1]=NEXTF(); c.src[2]=NEXTF(); }
        else if (!strcmp(argv[i], "--lis")) { c.lis[0]=NEXTF(); c.lis[1]=NEXTF(); c.lis[2]=NEXTF(); }
        else if (!strcmp(argv[i], "--absorption")) { c.absorption[0]=NEXTF(); c.absorption[1]=NEXTF(); c.absorption[2]=NEXTF(); }
        else if (!strcmp(argv[i], "--transmission")) { c.transmission[0]=NEXTF(); c.transmission[1]=NEXTF(); c.transmission[2]=NEXTF(); }
        else if (!strcmp(argv[i], "--scattering")) c.scattering = NEXTF();
        else if (!strcmp(argv[i], "--rays")) c.numRays = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--bounces")) c.numBounces = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--order")) c.order = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--duration")) c.duration = NEXTF();
        else if (!strcmp(argv[i], "--sr")) c.sr = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--frame")) c.frameSize = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--out")) c.out = argv[++i];
        else { usage(); return 2; }
    }

    /* ---------------- context ---------------- */
    IPLContextSettings cs; memset(&cs, 0, sizeof cs);
    cs.version = STEAMAUDIO_VERSION;
    cs.logCallback = logcb;
    cs.flags = IPL_CONTEXTFLAGS_VALIDATION;
    IPLContext ctx = NULL;
    if (iplContextCreate(&cs, &ctx) != IPL_STATUS_SUCCESS) { fprintf(stderr, "context create failed\n"); return 1; }

    /* ---------------- scene: a single square wall ---------------- */
    IPLSceneSettings ss; memset(&ss, 0, sizeof ss);
    ss.type = IPL_SCENETYPE_DEFAULT;
    IPLScene scene = NULL;
    if (iplSceneCreate(ctx, &ss, &scene) != IPL_STATUS_SUCCESS) { fprintf(stderr, "scene create failed\n"); return 1; }

    IPLStaticMesh mesh = NULL;
    if (!c.noWall) {
        float h = c.wallSize * 0.5f, w = c.wallPos;
        IPLVector3 v[4];
        /* Build the square so that, with CCW winding, the normal points towards the origin side
           (i.e. -axis if wallPos > 0, +axis if wallPos < 0). */
        float sgn = (w >= 0) ? 1.0f : -1.0f;
        switch (c.wallAxis) {
          case 'x': /* plane x = w, spans y,z */
            v[0]=(IPLVector3){w,-h,-h}; v[1]=(IPLVector3){w,-h, h}; v[2]=(IPLVector3){w, h, h}; v[3]=(IPLVector3){w, h,-h};
            /* order above: (y,z): (-,-),(-,+),(+,+),(+,-) -> normal = (v1-v0)x(v2-v0) = (0,0,2h)x(0,2h,2h) = (-4h^2,0,0)?  */
            break;
          case 'y': /* plane y = w, spans x,z */
            v[0]=(IPLVector3){-h,w,-h}; v[1]=(IPLVector3){ h,w,-h}; v[2]=(IPLVector3){ h,w, h}; v[3]=(IPLVector3){-h,w, h};
            break;
          default:  /* plane z = w, spans x,y */
            v[0]=(IPLVector3){-h,-h,w}; v[1]=(IPLVector3){-h, h,w}; v[2]=(IPLVector3){ h, h,w}; v[3]=(IPLVector3){ h,-h,w};
            break;
        }
        /* compute normal of (v0,v1,v2) and flip order if it does not point toward the origin side */
        float ax=v[1].x-v[0].x, ay=v[1].y-v[0].y, az=v[1].z-v[0].z;
        float bx=v[2].x-v[0].x, by=v[2].y-v[0].y, bz=v[2].z-v[0].z;
        float nx=ay*bz-az*by, ny=az*bx-ax*bz, nz=ax*by-ay*bx;
        float ncomp = (c.wallAxis=='x') ? nx : (c.wallAxis=='y') ? ny : nz;
        int wantTowardOrigin = (ncomp * sgn < 0); /* normal should be opposite in sign to w */
        int reverse = !wantTowardOrigin;
        if (c.flipWinding) reverse = !reverse;
        IPLTriangle t[2];
        if (!reverse) { t[0]=(IPLTriangle){{0,1,2}}; t[1]=(IPLTriangle){{0,2,3}}; }
        else          { t[0]=(IPLTriangle){{0,2,1}}; t[1]=(IPLTriangle){{0,3,2}}; }
        /* report final normal */
        {
            IPLVector3 p0=v[t[0].indices[0]], p1=v[t[0].indices[1]], p2=v[t[0].indices[2]];
            float a1=p1.x-p0.x,a2=p1.y-p0.y,a3=p1.z-p0.z,b1=p2.x-p0.x,b2=p2.y-p0.y,b3=p2.z-p0.z;
            float n1=a2*b3-a3*b2,n2=a3*b1-a1*b3,n3=a1*b2-a2*b1,l=sqrtf(n1*n1+n2*n2+n3*n3);
            printf("wall_normal %.3f %.3f %.3f\n", n1/l, n2/l, n3/l);
        }
        IPLMaterial mat;
        memcpy(mat.absorption, c.absorption, sizeof mat.absorption);
        mat.scattering = c.scattering;
        memcpy(mat.transmission, c.transmission, sizeof mat.transmission);
        IPLint32 matIdx[2] = {0,0};
        IPLStaticMeshSettings ms; memset(&ms, 0, sizeof ms);
        ms.numVertices = 4; ms.numTriangles = 2; ms.numMaterials = 1;
        ms.vertices = v; ms.triangles = t; ms.materialIndices = matIdx; ms.materials = &mat;
        if (iplStaticMeshCreate(scene, &ms, &mesh) != IPL_STATUS_SUCCESS) { fprintf(stderr, "mesh create failed\n"); return 1; }
        iplStaticMeshAdd(mesh, scene);
    }
    iplSceneCommit(scene);

    /* ---------------- simulator ---------------- */
    IPLSimulationSettings sim; memset(&sim, 0, sizeof sim);
    sim.flags = IPL_SIMULATIONFLAGS_DIRECT | IPL_SIMULATIONFLAGS_REFLECTIONS;
    sim.sceneType = IPL_SCENETYPE_DEFAULT;
    sim.reflectionType = IPL_REFLECTIONEFFECTTYPE_CONVOLUTION;
    sim.maxNumOcclusionSamples = 64;
    sim.maxNumRays = c.numRays;
    sim.numDiffuseSamples = 1024;
    sim.maxDuration = c.duration;
    sim.maxOrder = c.order;
    sim.maxNumSources = 1;
    sim.numThreads = 8;
    sim.numVisSamples = 1;
    sim.rayBatchSize = 16;
    sim.samplingRate = c.sr;
    sim.frameSize = c.frameSize;
    IPLSimulator simulator = NULL;
    if (iplSimulatorCreate(ctx, &sim, &simulator) != IPL_STATUS_SUCCESS) { fprintf(stderr, "simulator create failed\n"); return 1; }
    iplSimulatorSetScene(simulator, scene);

    IPLSourceSettings srcs; srcs.flags = sim.flags;
    IPLSource source = NULL;
    if (iplSourceCreate(simulator, &srcs, &source) != IPL_STATUS_SUCCESS) { fprintf(stderr, "source create failed\n"); return 1; }
    iplSourceAdd(source, simulator);
    iplSimulatorCommit(simulator);

    IPLCoordinateSpace3 lisCS = { {1,0,0}, {0,1,0}, {0,0,-1}, {c.lis[0],c.lis[1],c.lis[2]} };
    IPLCoordinateSpace3 srcCS = { {1,0,0}, {0,1,0}, {0,0,-1}, {c.src[0],c.src[1],c.src[2]} };

    IPLSimulationSharedInputs shared; memset(&shared, 0, sizeof shared);
    shared.listener = lisCS;
    shared.numRays = c.numRays;
    shared.numBounces = c.numBounces;
    shared.duration = c.duration;
    shared.order = c.order;
    shared.irradianceMinDistance = c.irrMin;
    iplSimulatorSetSharedInputs(simulator, sim.flags, &shared);

    IPLSimulationInputs in; memset(&in, 0, sizeof in);
    in.flags = sim.flags;
    in.directFlags = IPL_DIRECTSIMULATIONFLAGS_DISTANCEATTENUATION | IPL_DIRECTSIMULATIONFLAGS_AIRABSORPTION |
                     IPL_DIRECTSIMULATIONFLAGS_DIRECTIVITY | IPL_DIRECTSIMULATIONFLAGS_OCCLUSION | IPL_DIRECTSIMULATIONFLAGS_TRANSMISSION;
    in.source = srcCS;
    in.distanceAttenuationModel.type = IPL_DISTANCEATTENUATIONTYPE_DEFAULT;
    in.airAbsorptionModel.type = c.noAir ? IPL_AIRABSORPTIONTYPE_EXPONENTIAL : IPL_AIRABSORPTIONTYPE_DEFAULT;
    in.airAbsorptionModel.coefficients[0] = in.airAbsorptionModel.coefficients[1] = in.airAbsorptionModel.coefficients[2] = 0.0f;
    in.directivity.dipoleWeight = 0.0f;  /* omnidirectional */
    in.directivity.dipolePower = 1.0f;
    in.occlusionType = IPL_OCCLUSIONTYPE_RAYCAST;
    in.occlusionRadius = 0.1f;
    in.numOcclusionSamples = 16;
    in.reverbScale[0] = in.reverbScale[1] = in.reverbScale[2] = 1.0f;
    in.hybridReverbTransitionTime = 1.0f;
    in.hybridReverbOverlapPercent = 0.25f;
    in.numTransmissionRays = 1;
    iplSourceSetInputs(source, sim.flags, &in);

    /* ---------------- direct simulation ---------------- */
    iplSimulatorRunDirect(simulator);
    IPLSimulationOutputs out; memset(&out, 0, sizeof out);
    iplSourceGetOutputs(source, IPL_SIMULATIONFLAGS_DIRECT, &out);
    printf("direct distanceAttenuation %.6f\n", out.direct.distanceAttenuation);
    printf("direct airAbsorption %.6f %.6f %.6f\n", out.direct.airAbsorption[0], out.direct.airAbsorption[1], out.direct.airAbsorption[2]);
    printf("direct directivity %.6f\n", out.direct.directivity);
    printf("direct occlusion %.6f\n", out.direct.occlusion);
    printf("direct transmission %.6f %.6f %.6f\n", out.direct.transmission[0], out.direct.transmission[1], out.direct.transmission[2]);
    /* analytic reference from the API's own helper */
    IPLVector3 sv = {c.src[0],c.src[1],c.src[2]}, lv = {c.lis[0],c.lis[1],c.lis[2]};
    printf("api distanceAttenuationCalculate %.6f\n", iplDistanceAttenuationCalculate(ctx, sv, lv, &in.distanceAttenuationModel));
    { float aa[3]; iplAirAbsorptionCalculate(ctx, sv, lv, &in.airAbsorptionModel, aa); printf("api airAbsorptionCalculate %.6f %.6f %.6f\n", aa[0], aa[1], aa[2]); }

    /* ---------------- reflections simulation ---------------- */
    IPLDirectEffectParams directOut = out.direct;
    iplSimulatorRunReflections(simulator);
    memset(&out, 0, sizeof out);
    iplSourceGetOutputs(source, IPL_SIMULATIONFLAGS_REFLECTIONS, &out);
    printf("reflections irHandle %p numChannels %d irSize %d\n", (void*)out.reflections.ir, out.reflections.numChannels, out.reflections.irSize);

    /* ---------------- extract IR via convolution of a unit impulse ---------------- */
    int numChannels = (c.order + 1) * (c.order + 1);
    int irSize = (int)ceilf(c.duration * c.sr);
    IPLAudioSettings as = { c.sr, c.frameSize };
    IPLReflectionEffectSettings res; memset(&res, 0, sizeof res);
    res.type = IPL_REFLECTIONEFFECTTYPE_CONVOLUTION;
    res.irSize = irSize;
    res.numChannels = numChannels;
    IPLReflectionEffect effect = NULL;
    if (iplReflectionEffectCreate(ctx, &as, &res, &effect) != IPL_STATUS_SUCCESS) { fprintf(stderr, "effect create failed\n"); return 1; }

    IPLAudioBuffer inBuf, outBuf;
    iplAudioBufferAllocate(ctx, 1, c.frameSize, &inBuf);
    iplAudioBufferAllocate(ctx, numChannels, c.frameSize, &outBuf);

    int numFrames = irSize / c.frameSize + 2;
    int totalSamples = numFrames * c.frameSize;
    float* ir = (float*)calloc((size_t)numChannels * totalSamples, sizeof(float));

    IPLReflectionEffectParams rp = out.reflections;
    rp.type = IPL_REFLECTIONEFFECTTYPE_CONVOLUTION;
    rp.numChannels = numChannels;
    rp.irSize = irSize;

    /* Warm-up: the convolution effect cross-fades from its previous (empty) IR to the new one over the first frame
       it processes, so anything arriving inside that frame would be ramped. Feed one frame of silence first. */
    memset(inBuf.data[0], 0, sizeof(float) * c.frameSize);
    iplReflectionEffectApply(effect, &rp, &inBuf, &outBuf, NULL);

    for (int f = 0; f < numFrames; ++f) {
        memset(inBuf.data[0], 0, sizeof(float) * c.frameSize);
        if (f == 0) inBuf.data[0][0] = 1.0f;            /* unit impulse at t = 0 */
        iplReflectionEffectApply(effect, &rp, &inBuf, &outBuf, NULL);
        for (int ch = 0; ch < numChannels; ++ch)
            memcpy(ir + (size_t)ch * totalSamples + (size_t)f * c.frameSize, outBuf.data[ch], sizeof(float) * c.frameSize);
    }

    /* write outputs */
    char path[1024];
    snprintf(path, sizeof path, "%s.f32", c.out);
    FILE* fp = fopen(path, "wb");
    if (!fp) { fprintf(stderr, "cannot open %s\n", path); return 1; }
    fwrite(ir, sizeof(float), (size_t)numChannels * totalSamples, fp);
    fclose(fp);
    snprintf(path, sizeof path, "%s.json", c.out);
    fp = fopen(path, "w");
    fprintf(fp, "{\n \"numChannels\": %d, \"numSamples\": %d, \"irSize\": %d, \"sr\": %d, \"frameSize\": %d,\n", numChannels, totalSamples, irSize, c.sr, c.frameSize);
    fprintf(fp, " \"wallAxis\": \"%c\", \"wallPos\": %g, \"wallSize\": %g, \"flip\": %d, \"noWall\": %d,\n", c.wallAxis, c.wallPos, c.wallSize, c.flipWinding, c.noWall);
    fprintf(fp, " \"src\": [%g,%g,%g], \"lis\": [%g,%g,%g],\n", c.src[0],c.src[1],c.src[2], c.lis[0],c.lis[1],c.lis[2]);
    fprintf(fp, " \"absorption\": [%g,%g,%g], \"transmission\": [%g,%g,%g], \"scattering\": %g,\n", c.absorption[0],c.absorption[1],c.absorption[2], c.transmission[0],c.transmission[1],c.transmission[2], c.scattering);
    fprintf(fp, " \"numRays\": %d, \"numBounces\": %d, \"order\": %d, \"duration\": %g, \"noAir\": %d,\n", c.numRays, c.numBounces, c.order, c.duration, c.noAir);
    fprintf(fp, " \"direct\": {\"distanceAttenuation\": %g, \"airAbsorption\": [%g,%g,%g], \"directivity\": %g, \"occlusion\": %g, \"transmission\": [%g,%g,%g]}\n}\n",
            directOut.distanceAttenuation, directOut.airAbsorption[0], directOut.airAbsorption[1], directOut.airAbsorption[2],
            directOut.directivity, directOut.occlusion, directOut.transmission[0], directOut.transmission[1], directOut.transmission[2]);
    fclose(fp);

    double e = 0; for (size_t i = 0; i < (size_t)totalSamples; ++i) e += (double)ir[i]*ir[i];
    printf("ir W-channel energy %.6e\n", e);

    free(ir);
    iplAudioBufferFree(ctx, &inBuf); iplAudioBufferFree(ctx, &outBuf);
    iplReflectionEffectRelease(&effect);
    iplSourceRemove(source, simulator); iplSimulatorCommit(simulator);
    iplSourceRelease(&source);
    iplSimulatorRelease(&simulator);
    if (mesh) { iplStaticMeshRemove(mesh, scene); iplStaticMeshRelease(&mesh); }
    iplSceneRelease(&scene);
    iplContextRelease(&ctx);
    return 0;
}
