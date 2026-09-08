#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LandscapeCluster.generated.h"

class UHierarchicalInstancedStaticMeshComponent;

/** Shared garden geometry. Individual leaves and blades never obstruct walking. */
UCLASS()
class CLEVELANDREAL_API ALandscapeCluster : public AActor
{
    GENERATED_BODY()
public:
    ALandscapeCluster();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Landscape")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> Instances;
};
