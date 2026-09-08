#include "LandscapeCluster.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"

ALandscapeCluster::ALandscapeCluster()
{
    PrimaryActorTick.bCanEverTick = false;
    Instances = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("GardenInstances"));
    SetRootComponent(Instances);
    Instances->SetMobility(EComponentMobility::Static);
    Instances->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Instances->SetGenerateOverlapEvents(false);
    Instances->SetCanEverAffectNavigation(false);
    Instances->bAffectDistanceFieldLighting = false;
    Instances->SetCullDistances(1800, 2500);
}
