#include <phonon.h>
#include <stdio.h>
#define S(n) printf("%s %zu\n", #n, sizeof(n));
int main(void){
S(IPLVector3) S(IPLCoordinateSpace3) S(IPLSphere) S(IPLMatrix4x4) S(IPLContextSettings) S(IPLSceneSettings) S(IPLMaterial) S(IPLTriangle)
S(IPLStaticMeshSettings) S(IPLInstancedMeshSettings) S(IPLSimulationSettings) S(IPLSourceSettings) S(IPLDistanceAttenuationModel)
S(IPLAirAbsorptionModel) S(IPLDirectivity) S(IPLBakedDataIdentifier) S(IPLSimulationInputs) S(IPLSimulationSharedInputs)
S(IPLDirectEffectParams) S(IPLReflectionEffectParams) S(IPLPathEffectParams) S(IPLSimulationOutputs) S(IPLAudioSettings) S(IPLAudioBuffer)
S(IPLReflectionEffectSettings) S(IPLHRTFSettings) S(IPLSpeakerLayout) S(IPLAmbisonicsDecodeEffectSettings) S(IPLAmbisonicsDecodeEffectParams)
return 0;}
