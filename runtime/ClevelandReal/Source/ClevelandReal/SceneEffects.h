#pragma once

#include "CoreMinimal.h"

class UWorld;
class FJsonObject;
class UMaterialInstanceDynamic;

/** Bounded, persistent visual options. Collision is independent of visibility. */
class FSceneEffects
{
public:
    void Initialize(UWorld* World);
    bool Update(UWorld* World, const TSharedPtr<FJsonObject>& Input);
    TSharedRef<FJsonObject> Snapshot() const;
    void Apply(UWorld* World);
    TSharedRef<FJsonObject> Verify(UWorld* World);
private:
    bool Grass = true;
    bool Plants = true;
    bool Breeze = true;
    bool RayShadows = true;
    bool Reflections = true;
    bool MaterialsReady = false;
    int32 GrassClusters = 0;
    int32 PlantClusters = 0;
    struct FWindMaterial { TWeakObjectPtr<UMaterialInstanceDynamic> Material; float Strength; };
    TArray<FWindMaterial> WindMaterials;
    bool Read(const TSharedPtr<FJsonObject>& Input);
};
