#include "CeilingFan.h"
#include "Components/SceneComponent.h"

ACeilingFan::ACeilingFan()
{
    PrimaryActorTick.bCanEverTick = true;
    RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Rotor"));
    RootComponent->SetMobility(EComponentMobility::Movable);
}

void ACeilingFan::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (bRunning)
        RootComponent->AddLocalRotation(FRotator(0.f, 6.f * RevolutionsPerMinute * DeltaSeconds, 0.f));
}
